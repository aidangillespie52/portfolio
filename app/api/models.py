from pydantic import BaseModel
from typing import List, Literal


class CommandRequest(BaseModel):
    session_id: str
    mode: Literal["portfolio", "project"] = "portfolio"
    cwd: str | None = "~"
    command: str


class TerminalLine(BaseModel):
    type: Literal["text", "info", "ok", "error"]
    content: str
    html: bool = False


class CommandResponse(BaseModel):
    session_id: str
    mode: str
    cwd: str | None
    lines: List[TerminalLine]
    open_url: str | None = None
    open_readme: str | None = None


def T(content: str)    -> TerminalLine: return TerminalLine(type="text",  content=content)
def OK(content: str)   -> TerminalLine: return TerminalLine(type="ok",    content=content)
def INFO(content: str) -> TerminalLine: return TerminalLine(type="info",  content=content)
def ERR(content: str)  -> TerminalLine: return TerminalLine(type="error", content=content)
def HTML(content: str) -> TerminalLine: return TerminalLine(type="text",  content=content, html=True)