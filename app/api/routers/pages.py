from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import BASE_DIR
from app.models import IsolationLevel

pages_router = APIRouter(tags=["pages"])


@pages_router.get("/", response_class=HTMLResponse)
async def get_demo_page(request: Request) -> HTMLResponse:

    html_path = Path(BASE_DIR / "templates/index.html")
    html_content = html_path.read_text(encoding="utf-8")

    options_html = "\n".join(
        [f'<option value="{level}">{level}</option>' for level in IsolationLevel]
    )

    html_content = html_content.replace("{options_html}", options_html)
    return HTMLResponse(content=html_content)
