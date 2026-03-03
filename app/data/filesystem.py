import json
from pathlib import Path
from app.logging.logger import setup_logger

STATIC_DIR    = Path("app/static")
PROJECTS_DIR  = STATIC_DIR / "projects"

log = setup_logger(__name__)

def build_filesystem() -> dict:
    log.debug("Building in-memory filesystem from static/projects...")

    fs = {
        "~": ["projects"],
        "~/projects": [],
    }

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        name = project_dir.name
        fs["~/projects"].append(name)
        fs[f"~/projects/{name}"] = []

        for file in sorted(project_dir.iterdir()):
            if file.is_file() and file.name != "content.json":
                fs[f"~/projects/{name}"].append({
                    "name": file.name,
                    "type": "file",
                    "url": f"/static/projects/{name}/{file.name}",
                })

    return fs


def build_project_info() -> dict:
    info = {}

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        log.debug(f"Processing project directory: {project_dir}")
        if not project_dir.is_dir():
            continue

        name         = project_dir.name
        content_file = project_dir / "content.json"

        if content_file.exists():
            log.debug(f"Found content.json for project '{name}', loading metadata...")
            data = json.loads(content_file.read_text())
            info[name] = {
                "name":        data.get("title", name),
                "status":      data.get("status", "Active"),
                "description": data.get("description", ""),
                "github_url":  data.get("github_url", None),
            }
        else:
            log.debug(f"No content.json found for project '{name}', using defaults.")
            info[name] = {
                "name":        name,
                "status":      "Active",
                "description": "",
                "github_url":  None,
            }

    return info


FILESYSTEM   = build_filesystem()
PROJECT_INFO = build_project_info()