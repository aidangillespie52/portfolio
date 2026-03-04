from app.api.models import TerminalLine, T, OK, INFO, ERR, TerminalLine
from app.data.filesystem import FILESYSTEM, PROJECT_INFO, PROJECTS_DIR
import re
import aiohttp
import markdown as md

def get_children(cwd: str) -> list | None:
    return FILESYSTEM.get(cwd)


def find_file(cwd: str, filename: str) -> dict | None:
    for child in FILESYSTEM.get(cwd, []):
        if isinstance(child, dict) and child["name"] == filename:
            return child
    return None


def handle_pwd(cwd: str) -> list[TerminalLine]:
    return [T(cwd.replace("~", "/home/aidan"))]


def handle_ls(cwd: str) -> list[TerminalLine]:
    children = get_children(cwd)
    if children is None:
        return [ERR(f"ls: cannot access '{cwd}': No such directory")]
    if not children:
        return [INFO("(empty)")]

    lines = []
    for child in children:
        if isinstance(child, dict):
            lines.append(T(f"  {child['name']}"))
        else:
            info = PROJECT_INFO.get(child)
            desc = f"  — {info['description']}" if info and info.get("description") else ""
            lines.append(T(f"  {child}/{desc}"))
    return lines


def handle_cd(cwd: str, args: list[str]) -> tuple[str, list[TerminalLine]]:
    target = args[0].rstrip("/") if args else "~"

    if target == "~":
        return "~", []
    if target == "..":
        new_cwd = cwd.rsplit("/", 1)[0] or "~" if cwd != "~" else "~"
        return new_cwd, []

    new_path = f"~/{target}" if cwd == "~" else f"{cwd}/{target}"
    if new_path in FILESYSTEM:
        return new_path, []
    return cwd, [ERR(f"cd: {target}: No such file or directory")]


def handle_view(cwd: str, args: list[str]) -> tuple[list[TerminalLine], str | None, str | None]:
    if not args:
        return [ERR("view: missing filename — usage: view <file>")], None, None

    filename     = args[0]
    project_name = None

    if cwd == "~/projects":
        project_name = filename.removesuffix(".proj")
    elif cwd.startswith("~/projects/"):
        project_name = cwd.split("/")[2].removesuffix(".proj")

    if project_name and project_name in PROJECT_INFO:
        return [OK(f"Opening {project_name}…")], None, project_name

    file = find_file(cwd, filename)
    if file is None:
        return [ERR(f"view: {filename}: No such file")], None, None
    return [OK(f"Opening {filename}…")], file["url"], None

async def fetch_readme(name: str) -> dict:
    project    = PROJECT_INFO.get(name)
    github_url = project.get("github_url") if project else None

    if github_url:
        raw_url = github_url.rstrip("/").replace(
            "https://github.com", "https://raw.githubusercontent.com"
        ) + "/refs/heads/main/README.md"

        async with aiohttp.ClientSession() as session:
            async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=8)) as res:
                if res.status == 200:
                    text = await res.text()
                    html = md.markdown(text, extensions=["fenced_code", "tables"])
                    return {"html": html}

    path = PROJECTS_DIR / name / "README.md"
    if path.exists():
        html = md.markdown(path.read_text(), extensions=["fenced_code", "tables"])
        return {"html": html}

    return {"html": "<p class='muted'>No README found.</p>"}