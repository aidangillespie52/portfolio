# terminal-portfolio

A browser-based developer portfolio built as a fully functional terminal emulator. Navigate with real shell commands to explore projects, view a resume, and browse contact info — all rendered in a split-pane SSH-style interface.

## Demo

```
$ ssh aidan@portfolio.dev
```

## Features

- **Terminal emulator** — `ls`, `cd`, `pwd`, `view`, `clear` and more
- **Tab completion** — commands and filenames, loaded dynamically from the backend
- **Project registry** — file-based, each project is a `content.json` with metadata and a GitHub URL
- **Split-pane README viewer** — `view <project>` fetches and renders the project's GitHub README live
- **Dynamic boot sequence** — project count and last push timestamp fetched on load
- **Resume viewer** — PDF rendered inline in the right pane
- **Modular FastAPI backend** — clean separation of routing, handlers, filesystem, and config

## Stack

- **Backend** — Python, FastAPI, aiohttp, Uvicorn
- **Frontend** — Vanilla JS, CSS (no frameworks)
- **Infra** — Ubuntu, nginx (reverse proxy), Certbot (SSL)
- **Fonts** — JetBrains Mono

## Project Structure

```
portfolio/
├── app/
│   ├── api/
│   │   ├── router.py          # registers routes
│   │   ├── commands.py        # endpoint + command dispatch
│   │   ├── models.py          # Pydantic models + line helpers
│   │   └── handlers/
│   │       ├── filesystem.py  # ls, cd, pwd, view, fetch_readme
│   │       └── portfolio.py   # projects, about, resume, contact, help
│   ├── data/
│   │   └── filesystem.py      # builds FILESYSTEM + PROJECT_INFO at startup
│   ├── logging/
│   │   └── logger.py          # structured logging, uvicorn-aligned format
│   └── static/
│       ├── css/styles.css
│       ├── js/terminal.js
│       └── projects/
│           └── <name>/
│               └── content.json
├── templates/
│   └── index.html
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Adding a Project

Create a folder under `app/static/projects/` with a `content.json`:

```json
{
  "title": "My Project",
  "status": "Active",
  "description": "A short description shown in the projects table",
  "github_url": "https://github.com/you/my-project"
}
```

The project will automatically appear in `ls`, `projects`, and `view` — no code changes needed.

## Running Locally

```bash
git clone git@github.com:aidangillespie52/portfolio.git
cd portfolio
uv run uvicorn app.main:app --reload
```

## Deployment

```bash
# install nginx + certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# reverse proxy to port 8000
sudo nano /etc/nginx/sites-available/portfolio

# get SSL cert
sudo certbot --nginx -d yourdomain.com

# run as a service
sudo systemctl enable portfolio
sudo systemctl start portfolio
```