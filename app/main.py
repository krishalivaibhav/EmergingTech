from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import api, web


load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Resume & Job Match Analyzer",
        description="Analyze resume fit against a job description using LLM-powered ATS-style insights.",
        version="1.0.0",
    )

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.state.templates = Jinja2Templates(directory="app/templates")

    app.include_router(web.router)
    app.include_router(api.router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

