"""OS-native terminal + Claude Code session launcher (Windows / macOS / Linux)"""
import asyncio
import functools
import logging
import platform
import shutil
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def launch_session(project_path: str, handoff_path: str, project_name: str = ""):
    """Open an OS-native terminal and start a Claude Code session in project_path."""

    display_name = project_name or Path(project_path).name
    # Strip characters that are problematic in shell / terminal title args
    display_name = "".join(c for c in display_name if c.isalnum() or c in " _-.")

    initial_prompt = (
        f"まず '{handoff_path}' を読み込んでください。\n"
        "読み込み後、以下の手順で進めてください:\n"
        "1. Phase 0（系譜分析）を系譜研究員（genealogist）サブエージェントに委譲する\n"
        "   - handoff.md のチームロスターに記載の prompt_directive を参照\n"
        "   - 深度設定は Phase 0 タスク記述の「深度設定」欄に従う\n"
        "   - 完了したら memory/genealogy.md に保存する\n"
        "   - 続けてポジショニング表を作成し memory/positioning.md に保存する\n"
        "2. genealogy.md + positioning.md 完成後、Phase 1 以降に進む\n"
        "   - 各フェーズは positioning.md の判断（採用/超越/狙う/対象外）を踏まえて作業する\n"
        "   - SOTA に対して劣後する設計判断をしてはならない\n"
        "3. Phase 2 完了後は Innovation Gate を必ず実施する\n"
        "   - 系譜的位置づけ基準をクリアするまで Phase 3 に進まない\n"
    )

    logger.info("Launching session for %s (OS=%s)", project_path, _OS)

    loop = asyncio.get_event_loop()

    try:
        if _OS == "Darwin":
            await loop.run_in_executor(
                None,
                functools.partial(_launch_macos, project_path, initial_prompt, display_name),
            )
        elif _OS == "Linux":
            await loop.run_in_executor(
                None,
                functools.partial(_launch_linux, project_path, initial_prompt, display_name),
            )
        else:
            # Windows (default)
            await _launch_windows(project_path, initial_prompt, display_name)
    except Exception as e:
        # Session launch failure is non-fatal — project and handoff.md are already created.
        logger.warning(
            "Session launch failed (%s). Open the project manually: cd %s && claude. Error: %s",
            _OS, project_path, e,
        )
        return

    logger.info("Session launched for %s", project_path)


# ---------------------------------------------------------------------------
# Unix helpers
# ---------------------------------------------------------------------------

def _write_startup_sh(project_path: str, initial_prompt: str) -> str:
    """Write a bash startup script and return its path (Unix)."""
    # Escape single quotes in the prompt for bash single-quoted string
    escaped_prompt = initial_prompt.replace("'", "'\\''")
    path = Path(project_path) / ".claude_start.sh"
    path.write_text(
        "#!/usr/bin/env bash\n"
        f"cd '{project_path}'\n"
        f"claude --dangerously-skip-permissions '{escaped_prompt}'\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return str(path)


# ---------------------------------------------------------------------------
# macOS launcher
# ---------------------------------------------------------------------------

def _launch_macos(project_path: str, initial_prompt: str, display_name: str):
    """Launch Claude Code in a new macOS terminal window."""
    startup_script = _write_startup_sh(project_path, initial_prompt)

    # Escape single quotes for AppleScript string context
    def as_escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    escaped_script = as_escape(startup_script)
    escaped_path = as_escape(project_path)

    has_iterm = Path("/Applications/iTerm.app").exists()

    if has_iterm:
        applescript = f'''
tell application "iTerm"
    create window with default profile
    tell current session of current window
        write text "bash \\"{escaped_script}\\""
    end tell
    activate
end tell'''
    else:
        applescript = f'''
tell application "Terminal"
    do script "bash \\"{escaped_script}\\""
    activate
end tell'''

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        # Fallback: open project folder in Finder and log instructions
        subprocess.run(["open", escaped_path], check=False)
        raise RuntimeError(f"osascript failed: {stderr}")


# ---------------------------------------------------------------------------
# Linux launcher
# ---------------------------------------------------------------------------

def _launch_linux(project_path: str, initial_prompt: str, display_name: str):
    """Launch Claude Code in an available Linux terminal emulator."""
    startup_script = _write_startup_sh(project_path, initial_prompt)

    # Ordered preference list: (binary, args_builder)
    def _gnome(script):
        return ["gnome-terminal", f"--title={display_name}",
                f"--working-directory={project_path}", "--", "bash", script]

    def _konsole(script):
        return ["konsole", "--workdir", project_path,
                "-p", f"tabtitle={display_name}", "-e", "bash", script]

    def _xfce(script):
        return ["xfce4-terminal", f"--title={display_name}",
                f"--working-directory={project_path}", "-e", f"bash {script}"]

    def _xterm(script):
        return ["xterm", "-title", display_name, "-e",
                f"bash -c 'cd \"{project_path}\" && bash \"{script}\"'"]

    candidates = [("gnome-terminal", _gnome), ("konsole", _konsole),
                  ("xfce4-terminal", _xfce), ("xterm", _xterm)]

    for binary, build_args in candidates:
        if shutil.which(binary):
            cmd = build_args(startup_script)
            logger.info("Using terminal: %s", binary)
            subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

    raise RuntimeError(
        f"No supported terminal emulator found. "
        f"Install one of: gnome-terminal, konsole, xfce4-terminal, xterm. "
        f"Then run manually: cd '{project_path}' && claude"
    )


# ---------------------------------------------------------------------------
# Windows launcher (original logic, extracted into a function)
# ---------------------------------------------------------------------------

async def _launch_windows(project_path: str, initial_prompt: str, display_name: str):
    """Launch Claude Code via Windows Terminal on a new Virtual Desktop."""

    git_bash = config.GIT_BASH

    def ps_escape(s: str) -> str:
        """Escape for PowerShell single-quoted strings."""
        return s.replace("'", "''")

    escaped_path = project_path.replace("/", "\\")

    # Write a PowerShell startup script into the project dir to avoid
    # quoting/semicolon/CWD issues when launching via wt.exe.
    startup_script = Path(project_path) / ".claude_start.ps1"
    startup_script.write_text(
        f"[Environment]::SetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', '{ps_escape(git_bash)}', 'Process')\n"
        f"claude --dangerously-skip-permissions '{ps_escape(initial_prompt)}'\n",
        encoding="utf-8",
    )
    startup_script_path = str(startup_script).replace("/", "\\")

    ps_script = f'''
$ErrorActionPreference = "Continue"

# VirtualDesktop module check
$hasVD = $false
try {{
    Import-Module VirtualDesktop -ErrorAction Stop
    $hasVD = $true
}} catch {{
    Write-Host "VirtualDesktop module not found, opening in current desktop"
}}

if ($hasVD) {{
    try {{
        $desktop = New-Desktop
        Switch-Desktop -Desktop $desktop
        Start-Sleep -Seconds 1
    }} catch {{
        Write-Host "Failed to create virtual desktop: $_"
    }}
}}

# Open project folder in Explorer
Start-Process explorer.exe "{escaped_path}"
Start-Sleep -Seconds 1

# Open a new Windows Terminal tab running the startup script
try {{
    Start-Process wt.exe -ArgumentList @(
        "new-tab",
        "--startingDirectory", """{escaped_path}""",
        "--title", """{display_name}""",
        "pwsh", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", """{startup_script_path}"""
    )
}} catch {{
    # Fallback: plain PowerShell if wt.exe is unavailable
    Start-Process pwsh.exe -WorkingDirectory "{escaped_path}" -ArgumentList @(
        "-NoExit", "-ExecutionPolicy", "Bypass", "-File", """{startup_script_path}"""
    )
}}
'''

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        functools.partial(
            subprocess.run,
            ["pwsh", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ),
    )

    if result.stdout:
        logger.info("Launcher stdout: %s", result.stdout.decode(errors="replace").strip())
    if result.stderr:
        logger.warning("Launcher stderr: %s", result.stderr.decode(errors="replace").strip())

    if result.returncode != 0:
        raise RuntimeError(f"Windows session launch failed (rc={result.returncode})")
