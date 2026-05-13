"""
scratch/inject_emit_hooks.py
Step 14 — Inject SSE emit hooks into all tool execute() functions

Adds the sse_emitter import and an await emit_activity_log call
at the start of each tool's async execute() body.

Safe to re-run — skips files already injected.
"""

import os
import re

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "tools")
EMIT_IMPORT_LINE = "from src.api.streaming.sse_emitter import sse_emitter\n"


def inject(filepath: str, tool_name: str) -> bool:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Already done?
    if "sse_emitter" in content:
        print(f"  SKIP  {tool_name}")
        return False

    # 1. Add import after existing imports block
    lines = content.split("\n")
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    lines.insert(last_import_idx + 1, EMIT_IMPORT_LINE.rstrip())
    content = "\n".join(lines)

    # 2. Find `async def execute(params: dict) -> dict:` and insert emit after it
    #    We look for the line immediately after the def line (which is either a
    #    comment `# 1. Pydantic` or blank) and insert before it.
    pattern = re.compile(
        r"(async def execute\(params: dict\) -> dict:\n)(    )",
        re.MULTILINE
    )
    emit_block = (
        "async def execute(params: dict) -> dict:\n"
        f"    _case_id: str = params.get(\"case_id\", \"\")\n"
        f"    await sse_emitter.emit_activity_log(_case_id, \"tool\", \"{tool_name} invoked\", \"{tool_name}\")\n"
        "    "
    )
    new_content, count = pattern.subn(emit_block, content, count=1)

    if count == 0:
        print(f"  WARN  {tool_name} — pattern not matched, skipping")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  OK    {tool_name}")
    return True


if __name__ == "__main__":
    ok = skip = warn = 0
    for fname in sorted(os.listdir(TOOLS_DIR)):
        if fname.startswith("_") or not fname.endswith(".py"):
            continue
        tool = fname[:-3]
        result = inject(os.path.join(TOOLS_DIR, fname), tool)
        if result is True:
            ok += 1
        elif result is False:
            skip += 1
        else:
            warn += 1

    print(f"\nResult: {ok} injected | {skip} skipped | {warn} warnings")
