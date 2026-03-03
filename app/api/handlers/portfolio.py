from app.api.models import TerminalLine, T, OK, INFO, ERR, HTML
from app.data.filesystem import PROJECT_INFO, PROJECTS_DIR
import aiohttp
import markdown as md
import re

def _process_markdown(text: str) -> str:
    # Strip info strings from fenced code blocks (```text, ```python, etc.)
    text = re.sub(r'```\w+', '```', text)
    return md.markdown(text, extensions=["fenced_code", "tables"])

def handle_help(commands: dict) -> list[TerminalLine]:
    lines = [OK("Available commands:")]
    for cmd, desc in commands.items():
        lines.append(T(f"  {cmd:<12}{desc}"))
    return lines


def handle_projects() -> list[TerminalLine]:
    headers = ("ID", "NAME", "STATUS")
    name_trunc = 40

    def truncate(s: str, n: int) -> str:
        return s if len(s) <= n else s[:n - 3] + "..."

    rows = [
        (f"{i:02}", truncate(info["name"], name_trunc), info["status"])
        for i, (_, info) in enumerate(PROJECT_INFO.items(), 1)
    ]

    col_id   = max(len(headers[0]), max(len(r[0]) for r in rows))
    col_name = max(len(headers[1]), max(len(r[1]) for r in rows))
    col_stat = max(len(headers[2]), max(len(r[2]) for r in rows))

    def divider():
        return T("  +" + "-" * (col_id   + 2) +
                     "+" + "-" * (col_name + 2) +
                     "+" + "-" * (col_stat + 2) + "+")

    def row(a, b, c, line_type=T):
        return line_type(
            f"  | {a:<{col_id}} | {b:<{col_name}} | {c:<{col_stat}} |"
        )

    lines = [OK("Projects:"), divider()]
    lines.append(row(*headers, line_type=OK))
    lines.append(divider())
    for r in rows:
        lines.append(row(*r))
    lines.append(divider())
    lines.append(INFO("Tip: cd projects/ to browse them"))
    return lines


def handle_about() -> list[TerminalLine]:
    return [
        OK("About:"),
        T("  Name     Aidan Gillespie"),
        T("  Role     Applied Analytics Engineer"),
        T("  Stack    Python · SQL · FastAPI · vanilla JS"),
        T("  Focus    Turning messy data into systems people trust"),
    ]


def handle_resume() -> tuple[list[TerminalLine], str]:
    return [OK("Resume:"), INFO("  Opening resume…")], "/static/pdfs/resume.pdf"


def handle_contact() -> list[TerminalLine]:
    return [
        OK("Contact:"),
        HTML("  Email    <a href='mailto:aidangillespie52@gmail.com'>aidangillespie52@gmail.com</a>"),
        HTML("  GitHub   <a href='https://github.com/aidangillespie52' target='_blank'>github.com/aidangillespie52</a>"),
        HTML("  LinkedIn <a href='https://linkedin.com/in/aidan-gillespie52' target='_blank'>linkedin.com/in/aidan-gillespie52</a>"),
    ]

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
                    return {
                        "html":       _process_markdown(text),
                        "github_url": github_url,
                    }

    path = PROJECTS_DIR / name / "README.md"
    if path.exists():
        return {"html": _process_markdown(path.read_text()), "github_url": None}

    return {"html": "<p class='muted'>No README found.</p>", "github_url": None}