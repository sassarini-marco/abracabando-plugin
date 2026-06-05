import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from mcp_replay import (  # noqa: E402
    FixtureMissingError,
    Recorder,
    Replayer,
    fixture_key,
    load_fixture,
    save_fixture,
)


def test_fixture_key_strips_pagination_and_sorts():
    a = fixture_key("ted_search", {"q": "cloud", "limit": 10, "page": 1})
    b = fixture_key("ted_search", {"page": 9, "q": "cloud", "limit": 25, "offset": 100})
    assert a == b  # pagination keys ignored, key order irrelevant
    assert fixture_key("ted_search", {"q": "x"}) != fixture_key("ted_search", {"q": "y"})


def test_replay_keyed_then_sequential_then_errors():
    calls = [
        {"tool": "ted_search", "params": {"q": "cloud", "limit": 10},
         "response": {"items": [{"record_id": "1-2026"}]}},
        {"tool": "ted_search", "params": {"q": "cloud", "limit": 25},
         "response": {"items": [{"record_id": "2-2026"}]}},
        {"tool": "ted_pin_italy", "params": {"cpv": "72"},
         "response": {"content": [{"type": "text", "text": "__FIXTURE_FILE_PATH__"}]},
         "file_content": '{"items":[{"record_id":"3-2026"}]}'},
    ]
    r = Replayer(calls)

    # 1. exact normalized-key match (limit stripped)
    assert r.tools_call("ted_search", {"q": "cloud", "limit": 10}) == {"items": [{"record_id": "1-2026"}]}

    # 2. drifted args -> sequential fallback to the next recorded ted_search
    assert r.tools_call("ted_search", {"q": "DRIFTED"}) == {"items": [{"record_id": "2-2026"}]}

    # 3. file-path response reconstitutes a readable temp file
    resp = r.tools_call("ted_pin_italy", {"cpv": "72"})
    path = resp["content"][0]["text"]
    assert path != "__FIXTURE_FILE_PATH__"
    assert os.path.exists(path)
    with open(path) as fh:
        assert json.load(fh)["items"][0]["record_id"] == "3-2026"

    # 4. no remaining recordings for this tool -> FixtureMissingError
    with pytest.raises(FixtureMissingError):
        r.tools_call("ted_search", {"q": "anything"})


def test_recorded_fixture_roundtrips_through_replay(tmp_path):
    """Recording a synthetic proxied session writes a fixture whose every
    recorded tools/call is served back byte-identical in replay mode."""
    upstream = {
        ("anac_search_awards", '{"cpv": "72"}'): {"items": [{"record_id": "CIGABCDE123"}]},
        ("ted_search", '{"q": "cloud"}'): {"items": [{"record_id": "9-2026"}]},
    }

    def fake_upstream(tool, params):
        return upstream[(tool, json.dumps(params, sort_keys=True))]

    rec = Recorder(fake_upstream)
    r1 = rec.tools_call("anac_search_awards", {"cpv": "72"})
    r2 = rec.tools_call("ted_search", {"q": "cloud"})

    case_dir = tmp_path / "3.1-001"
    save_fixture(case_dir, rec.dump(), tools_list={"tools": [{"name": "ted_search"}]})

    calls, tools_list = load_fixture(case_dir)
    replay = Replayer(calls)
    assert replay.tools_call("anac_search_awards", {"cpv": "72"}) == r1
    assert replay.tools_call("ted_search", {"q": "cloud"}) == r2
    assert tools_list == {"tools": [{"name": "ted_search"}]}


def test_recorder_captures_file_path_response(tmp_path):
    big = tmp_path / "ted_big.json"
    big.write_text('{"items":[{"record_id":"7-2026"}]}')

    def fake_upstream(tool, params):
        return {"content": [{"type": "text", "text": str(big)}]}

    rec = Recorder(fake_upstream)
    rec.tools_call("ted_pin_italy", {"cpv": "72"})
    entry = rec.dump()[0]
    assert entry.get("file_content") == '{"items":[{"record_id":"7-2026"}]}'
    assert "__FIXTURE_FILE_PATH__" in json.dumps(entry["response"])

    # and it replays back into a real temp file
    resp = Replayer(rec.dump()).tools_call("ted_pin_italy", {"cpv": "72"})
    path = resp["content"][0]["text"]
    with open(path) as fh:
        assert json.load(fh)["items"][0]["record_id"] == "7-2026"
