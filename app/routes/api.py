from functools import lru_cache

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import AnalysisResponse, CVScanResponse, RoleSuggestionResponse
from app.services.analyzer import ResumeJobAnalyzer
from app.services.groq_service import GroqConfigurationError, GroqServiceError
from app.services.llm_service import LLMConfigurationError, LLMServiceError
from app.services.local_llm_service import LocalLLMConfigurationError, LocalLLMServiceError
from app.services.pdf_parser import PDFParsingError, extract_text_from_pdf_bytes


router = APIRouter(prefix="/api", tags=["analysis"])


@lru_cache(maxsize=1)
def get_analyzer() -> ResumeJobAnalyzer:
    return ResumeJobAnalyzer()


def _is_pdf_upload(upload: UploadFile) -> bool:
    if upload.content_type and upload.content_type.lower() == "application/pdf":
        return True
    return upload.filename.lower().endswith(".pdf")


def _build_role_based_job_description(target_role: str) -> str:
    return (
        f"Target Role: {target_role}\n"
        "Generate fit analysis using a standard hiring bar for this role.\n"
        "Evaluate responsibilities, required technical skills, collaboration ability, "
        "problem-solving approach, and communication expectations."
    )


async def _collect_resume_text(resume_file: UploadFile | None, resume_text: str) -> str:
    cleaned_resume_text = resume_text.strip()
    parsed_pdf_text = ""

    if resume_file and resume_file.filename:
        if not _is_pdf_upload(resume_file):
            raise HTTPException(status_code=400, detail="Resume file must be a PDF.")

        file_bytes = await resume_file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

        try:
            parsed_pdf_text = extract_text_from_pdf_bytes(file_bytes)
        except PDFParsingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    combined_resume = "\n\n".join(
        chunk for chunk in [cleaned_resume_text, parsed_pdf_text] if chunk.strip()
    ).strip()
    if not combined_resume:
        raise HTTPException(
            status_code=400,
            detail="Provide either a PDF resume upload, pasted resume text, or both.",
        )

    return combined_resume


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    resume_file: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
    job_description: str = Form(default=""),
    target_role: str = Form(default=""),
) -> AnalysisResponse:
    cleaned_job_description = job_description.strip()
    cleaned_target_role = target_role.strip()

    if not cleaned_job_description and not cleaned_target_role:
        raise HTTPException(
            status_code=400,
            detail="Provide a job description or select a target role.",
        )

    combined_resume = await _collect_resume_text(resume_file=resume_file, resume_text=resume_text)

    if cleaned_job_description:
        effective_job_description = cleaned_job_description
        if cleaned_target_role:
            effective_job_description = (
                f"Selected Role Focus: {cleaned_target_role}\n\n{cleaned_job_description}"
            )
    else:
        effective_job_description = _build_role_based_job_description(cleaned_target_role)

    try:
        analyzer = get_analyzer()
        return analyzer.analyze(
            resume_text=combined_resume,
            job_description=effective_job_description,
        )
    except (LLMConfigurationError, GroqConfigurationError, LocalLLMConfigurationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (LLMServiceError, GroqServiceError, LocalLLMServiceError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI analysis failed. Please retry. ({exc})",
        ) from exc


@router.post("/suggest-roles", response_model=RoleSuggestionResponse)
async def suggest_roles(
    resume_file: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
) -> RoleSuggestionResponse:
    combined_resume = await _collect_resume_text(resume_file=resume_file, resume_text=resume_text)

    try:
        analyzer = get_analyzer()
        return analyzer.suggest_roles(resume_text=combined_resume)
    except (LLMConfigurationError, GroqConfigurationError, LocalLLMConfigurationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (LLMServiceError, GroqServiceError, LocalLLMServiceError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Role suggestion failed. Please retry. ({exc})",
        ) from exc


@router.post("/scan-cv", response_model=CVScanResponse)
async def scan_cv(
    resume_file: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
) -> CVScanResponse:
    combined_resume = await _collect_resume_text(resume_file=resume_file, resume_text=resume_text)

    try:
        analyzer = get_analyzer()
        return analyzer.scan_cv(resume_text=combined_resume)
    except (LLMConfigurationError, GroqConfigurationError, LocalLLMConfigurationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (LLMServiceError, GroqServiceError, LocalLLMServiceError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"CV scan failed. Please retry. ({exc})",
        ) from exc
