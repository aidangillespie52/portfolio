from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="portfolio.exe",
        description="SSH-style interactive portfolio",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )

    # Static assets (CSS / JS / fonts)
    app.mount(
        "/static",
        StaticFiles(directory="app/static"),
        name="static",
    )

    # Templates
    templates = Jinja2Templates(directory="app/templates")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "app_name": "portfolio.exe",
                "version": "1.0.0",
            },
        )

    # API routes
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()