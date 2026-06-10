"""Brain CLI plugin — think + plan + gate for Hermes Agent."""

import json
import logging
import subprocess
import time
from pathlib import Path

from . import schemas

logger = logging.getLogger(__name__)

STATE_FILE = Path.home() / ".brain" / "state" / "plan.json"
ACTION_TOOLS = {"terminal", "write_file", "patch", "file_edit", "edit", "bash", "task"}


def _run_brain(*args: str) -> str:
    try:
        result = subprocess.run(
            ["brain", *args],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip() or "unknown error"
            return json.dumps(
                {"error": f"brain failed (exit {result.returncode}): {err}"}
            )
        return json.dumps({"result": output})
    except FileNotFoundError:
        return json.dumps(
            {"error": "brain CLI not installed. Run: uv tool install brain-cli"}
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "brain CLI timed out"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def brain_think(args: dict, **kwargs) -> str:
    prompt = args.get("prompt", "").strip()
    if not prompt:
        return json.dumps({"error": "No prompt provided"})
    return _run_brain("think", "--plan", prompt)


def brain_plan_done(args: dict, **kwargs) -> str:
    return _run_brain("plan", "done")


def brain_plan_block(args: dict, **kwargs) -> str:
    reason = args.get("reason", "").strip()
    if reason:
        return _run_brain("plan", "block", reason)
    return _run_brain("plan", "block")


def _load_gate_state() -> tuple[bool, str]:
    if not STATE_FILE.exists():
        return False, "No active plan. Call brain_think to create one."
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False, "Plan file is corrupt. Call brain_think to recreate."

    expires_at = data.get("expires_at", 0)
    if time.time() >= expires_at:
        return False, "Plan has expired. Call brain_think to create a new one."

    steps = data.get("steps", [])
    has_active = any(s.get("status") == "in_progress" for s in steps)
    if not has_active:
        current = data.get("current_step", 0)
        if current >= len(steps):
            return (
                False,
                "All plan steps are complete. Call brain_think for the next phase.",
            )
        return False, "No in-progress step found. Your plan may need attention."

    return True, ""


def gate_pre_tool_call(tool_name: str, args: dict, task_id: str, **kwargs):
    if tool_name not in ACTION_TOOLS:
        return

    allowed, message = _load_gate_state()
    if not allowed:
        logger.info("GATE blocked %s: %s", tool_name, message)
        return {"action": "block", "message": f"⛔ {message}"}


def register(ctx):
    ctx.register_tool(
        name="brain_think",
        toolset="brain",
        schema=schemas.BRAIN_THINK,
        handler=brain_think,
    )
    ctx.register_tool(
        name="brain_plan_done",
        toolset="brain",
        schema=schemas.BRAIN_PLAN_DONE,
        handler=brain_plan_done,
    )
    ctx.register_tool(
        name="brain_plan_block",
        toolset="brain",
        schema=schemas.BRAIN_PLAN_BLOCK,
        handler=brain_plan_block,
    )
    ctx.register_hook("pre_tool_call", gate_pre_tool_call)
