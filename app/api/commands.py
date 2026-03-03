from fastapi import APIRouter
from app.api.models import CommandRequest, CommandResponse, TerminalLine, INFO, ERR
from app.api.handlers.filesystem import handle_pwd, handle_ls, handle_cd, handle_view
from app.api.handlers.portfolio import handle_help, handle_projects, handle_about, handle_resume, handle_contact, fetch_readme
from app.logging.logger import setup_logger
from app.data.filesystem import FILESYSTEM

log = setup_logger(__name__)
router = APIRouter()

COMMANDS = {
    "help":     "Show this message",
    "ls":       "List directory contents",
    "cd":       "Change directory",
    "pwd":      "Print working directory",
    "view":     "Open a file or project",
    "projects": "List all projects",
    "about":    "About this portfolio",
    "resume":   "View resume",
    "contact":  "Contact info",
    "clear":    "Clear the terminal",
}

@router.get("/projects/{name}/readme")
async def get_readme(name: str):
    return await fetch_readme(name)

@router.get("/commands")
async def get_commands():
    return COMMANDS

@router.get("/filesystem")
async def get_filesystem():
    return FILESYSTEM

@router.post("/command", response_model=CommandResponse)
async def run_command(payload: CommandRequest) -> CommandResponse:
    log.debug(f"Command: {payload.command}")

    raw   = payload.command.strip()
    parts = raw.split()
    cmd   = parts[0].lower() if parts else ""
    args  = parts[1:]
    cwd   = payload.cwd or "~"
    mode  = payload.mode
    open_url: str | None = None
    lines: list[TerminalLine] = []

    if not cmd:
        return CommandResponse(session_id=payload.session_id, mode=mode, cwd=cwd, lines=[])

    if cmd in {"help", "?"}:
        lines = handle_help(COMMANDS)
    elif cmd == "pwd":
        lines = handle_pwd(cwd)
    elif cmd == "ls":
        lines = handle_ls(cwd)
    elif cmd == "cd":
        cwd, lines = handle_cd(cwd, args)
    elif cmd == "view":
        lines, open_url, open_readme = handle_view(cwd, args)
        
        return CommandResponse(
            session_id=payload.session_id,
            mode=mode,
            cwd=cwd,
            lines=lines,
            open_url=open_url,
            open_readme=open_readme,
        )
    elif cmd == "projects":
        lines = handle_projects()
    elif cmd == "about":
        lines = handle_about()
    elif cmd == "resume":
        lines, open_url = handle_resume()
    elif cmd == "contact":
        lines = handle_contact()
    elif cmd == "clear":
        pass
    else:
        lines = [ERR(f"command not found: {cmd} — type 'help' for options")]

    return CommandResponse(
        session_id=payload.session_id,
        mode=mode,
        cwd=cwd,
        lines=lines,
        open_url=open_url,
    )