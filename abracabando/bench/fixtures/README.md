# bench/fixtures/ — frozen replay fixtures

Each `<case_id>/` holds a recorded MCP call/response sequence (`calls.json`) and
the server's `tools/list` (`tools_list.json`), replayed by `bench/mcp_replay.py`
for the deterministic frozen tier.

> **Status: SYNTHETIC PLACEHOLDERS.** These were seeded from the committed golden
> (`bench/ground-truth/golden/`) so the directory is structurally valid and
> committed. They are NOT real recordings of a live `industrial-mcp` session.
> Before trusting the frozen tier, re-record against the live MCP:
>
> ```bash
> MCP_REPLAY_CASE=<case_id> python3 bench/mcp_replay.py --record --case <case_id>
> ```
>
> See bench/REFRESH_PROCEDURE.md §4. MCP-layer data defects are fixed in
> `../industrial-data-mcp`, never by hand-editing these fixtures.
