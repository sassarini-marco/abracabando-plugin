import json
import pathlib

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "bench" / "dataset" / "eval_dataset.json"
SCHEMA_PATH = ROOT / "bench" / "dataset" / "eval_dataset_schema.json"
REFRESH_PATH = ROOT / "bench" / "REFRESH_PROCEDURE.md"

def test_schema_is_valid_json_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)

def test_rubrics_require_deterministic_d2_d4():
    schema = json.loads(SCHEMA_PATH.read_text())
    # Build a case with D2 = "judge" (should fail validation)
    bad_case = {
        "id": "3.1-001",
        "template": "3.1",
        "prompt": "test",
        "parameters": {},
        "snapshot_date": "2025-11-01",
        "frozen_date": "2026-05-29",
        "ttl_days": 120,
        "ground_truth_records": [{"source": "ted", "record_id": "123456-2025"}],
        "rubrics": {"D2": "judge", "D4": "deterministic"},
        "refresh_instructions": "Re-run script."
    }
    bad_dataset = {
        "schema_version": "1.0.0",
        "judge_prompt_version": "haiku-2025-10-v1",
        "cases": [bad_case]
    }
    import pytest
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_dataset, schema)

def test_eval_dataset_validates_against_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(DATASET_PATH.read_text())
    jsonschema.validate(data, schema)
    assert len(data["cases"]) >= 6

def test_no_numeric_transformation_scores():
    data = json.loads(DATASET_PATH.read_text())
    valid_labels = {"basso", "medio", "alto"}
    for case in data["cases"]:
        if case["template"] == "3.3":
            label = case.get("transformation_score_label")
            assert label in valid_labels, f"Case {case['id']} has invalid label: {label!r}"

def test_judge_prompt_contains_required_sections():
    text = (ROOT / "bench" / "judge_prompt_v1.md").read_text()
    for substr in ["## Version", "## Terminology glossary", "## Scoring rubrics",
                   "## Mandatory refusals", "trasformazione in gara"]:
        assert substr in text, f"Missing: {substr!r}"

def test_judge_prompt_version_matches_dataset():
    import re
    prompt_text = (ROOT / "bench" / "judge_prompt_v1.md").read_text()
    data = json.loads(DATASET_PATH.read_text())
    # Extract version from "## Version" section
    m = re.search(r'##\s+Version\s*\n+[*-]?\s*Version[^:]*:\s*([^\n]+)', prompt_text, re.I)
    if not m:
        m = re.search(r'`([^`]+)`', prompt_text.split("## Version")[1].split("##")[0])
    version_in_prompt = m.group(1).strip() if m else None
    assert version_in_prompt == data["judge_prompt_version"], \
        f"Version mismatch: prompt={version_in_prompt!r} dataset={data['judge_prompt_version']!r}"

def test_eval_dataset_not_gitignored():
    import subprocess
    result = subprocess.run(
        ["git", "check-ignore", "-q", "bench/dataset/eval_dataset.json"],
        cwd=ROOT, capture_output=True
    )
    assert result.returncode == 1, "bench/dataset/eval_dataset.json should NOT be gitignored"

def test_eval_results_dir_is_gitignored():
    import subprocess
    result = subprocess.run(
        ["git", "check-ignore", "-q", "bench/eval_results/dummy.json"],
        cwd=ROOT, capture_output=True
    )
    assert result.returncode == 0, "bench/eval_results/ should be gitignored"

def test_judge_prompt_d7_references_sintesi_incrociata_fields():
    text = (ROOT / "bench" / "judge_prompt_v1.md").read_text()
    assert "Sintesi incrociata TED-ANAC" in text
    assert "PIN TED" in text
    assert "Valutazione trasformazione" in text


def test_refresh_procedure_covers_iteration_loop():
    text = REFRESH_PATH.read_text()
    assert "eval_report.py" in text
    assert "iteration" in text.lower()
    assert "D7" in text


def test_refresh_procedure_covers_schema_evolution():
    text = REFRESH_PATH.read_text()
    assert "## 7. Evolving a skill schema" in text
    assert "schema_version" in text


SKILL_TO_PREFIX = {
    "pin-radar": "/pin-radar ",
    "consultazioni-radar": "/consultazioni-radar ",
    "scheda-opportunita": "/scheda-opportunita ",
    "digest-pregara": "/digest-pregara ",
    "profilo-sa": "/profilo-sa ",
    "reconciliation-pnrr": "/reconciliation-pnrr ",
    "analisi-disciplinare": "/analisi-disciplinare ",
}
SCENARIOS = {"happy-path", "missing-data", "edge"}


def test_eval_prompts_have_skill_prefix():
    data = json.loads(DATASET_PATH.read_text())
    for case in data["cases"]:
        expected_prefix = SKILL_TO_PREFIX.get(case["skill"])
        assert expected_prefix is not None, f"Unknown skill {case.get('skill')!r}"
        assert case["prompt"].startswith(expected_prefix), (
            f"Case {case['id']}: prompt must start with {expected_prefix!r}, got {case['prompt'][:50]!r}"
        )


def test_dataset_covers_all_skills_three_scenarios():
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(DATASET_PATH.read_text())
    jsonschema.validate(data, schema)

    by_skill: dict[str, set] = {s: set() for s in SKILL_TO_PREFIX}
    for case in data["cases"]:
        assert case["skill"] in SKILL_TO_PREFIX, f"Unknown skill {case['skill']!r}"
        assert case["scenario"] in SCENARIOS, f"Bad scenario {case['scenario']!r}"
        assert case["tier"] in {"frozen", "live"}, f"Bad tier {case['tier']!r}"
        assert case["prompt"].startswith(SKILL_TO_PREFIX[case["skill"]])
        by_skill[case["skill"]].add(case["scenario"])

    for skill, scenarios in by_skill.items():
        assert scenarios == SCENARIOS, f"{skill} missing scenarios: {SCENARIOS - scenarios}"


def test_refresh_procedure_covers_all_templates():
    text = REFRESH_PATH.read_text()
    for token in ["3.1", "3.2", "3.3", "ttl_days", "judge_prompt_version"]:
        assert token in text, f"Missing token in REFRESH_PROCEDURE.md: {token!r}"
