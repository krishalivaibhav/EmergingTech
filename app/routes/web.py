from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "asset_version": int(datetime.now().timestamp()),
            "year": datetime.now().year,
        },
    )
