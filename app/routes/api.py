from functools import lru_cache

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.models.schemas import (
    AnalysisResponse,
    CVScanResponse,
    LatexCompileRequest,
    LiveMarketJobsResponse,
    ResumeUpgradeResponse,
    RoleSuggestionResponse,
)
from app.services.analyzer import ResumeJobAnalyzer
from app.services.groq_service import GroqConfigurationError, GroqServiceError
from app.services.job_market_service import JobMarketService, JobMarketServiceError
from app.services.latex_compiler import (
    LaTeXCompilationError,
    LaTeXCompilerService,
    LaTeXCompilerUnavailableError,
)
from app.services.llm_service import LLMConfigurationError, LLMServiceError
from app.services.local_llm_service import LocalLLMConfigurationError, LocalLLMServiceError
from app.services.pdf_parser import PDFParsingError, extract_text_from_pdf_bytes
from app.services.pdf_preview_service import (
    PDFPreviewRenderError,
    PDFPreviewService,
    PDFPreviewUnavailableError,
)


router = APIRouter(prefix="/api", tags=["analysis"])


@lru_cache(maxsize=1)
def get_analyzer() -> ResumeJobAnalyzer:
    return ResumeJobAnalyzer()


@lru_cache(maxsize=1)
def get_latex_compiler() -> LaTeXCompilerService:
    return LaTeXCompilerService()


@lru_cache(maxsize=1)
def get_job_market_service() -> JobMarketService:
    return JobMarketService()


@lru_cache(maxsize=1)
def get_pdf_preview_service() -> PDFPreviewService:
    return PDFPreviewService()


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


def _build_live_jobs_payload(
    *,
    jobs: list[dict],
    query: str,
    source_name: str,
    source_url: str,
    note: str,
    error: str = "",
    resolved_location_label: str = "",
    page: int = 1,
    has_more: bool = False,
) -> dict:
    return {
        "live_market_jobs": jobs,
        "live_market_jobs_query": query,
        "live_market_jobs_source_name": source_name,
        "live_market_jobs_source_url": source_url,
        "live_market_jobs_note": note,
        "live_market_jobs_error": error,
        "resolved_location_label": resolved_location_label,
        "live_market_jobs_page": page,
        "live_market_jobs_has_more": has_more,
    }


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
        analysis = analyzer.analyze(
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

    live_jobs_payload = _build_live_jobs_payload(
        jobs=[],
        query="",
        source_name="",
        source_url="",
        note="",
    )

    if cleaned_target_role:
        try:
            market_service = get_job_market_service()
            live_jobs = await market_service.fetch_live_jobs(cleaned_target_role)
            live_jobs_payload = _build_live_jobs_payload(
                jobs=live_jobs.jobs,
                query=cleaned_target_role,
                source_name=live_jobs.source_name,
                source_url=live_jobs.source_url,
                note=live_jobs.note,
                page=live_jobs.page,
                has_more=live_jobs.has_more,
            )
        except JobMarketServiceError as exc:
            live_jobs_payload = _build_live_jobs_payload(
                jobs=[],
                query=cleaned_target_role,
                source_name="Adzuna + Himalayas",
                source_url="https://www.adzuna.in/",
                note="India-focused jobs come from Adzuna and remote jobs come from Himalayas.",
                error=str(exc),
            )

    return AnalysisResponse(**(analysis.model_dump() | live_jobs_payload))


@router.post("/location-jobs", response_model=LiveMarketJobsResponse)
async def fetch_location_jobs(
    target_role: str = Form(default=""),
    location_query: str = Form(default=""),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    page: int = Form(default=1),
) -> LiveMarketJobsResponse:
    cleaned_target_role = target_role.strip()
    cleaned_location_query = location_query.strip()
    current_page = max(int(page or 1), 1)
    if not cleaned_target_role:
        raise HTTPException(status_code=400, detail="Select a target role before using location-based job search.")

    try:
        market_service = get_job_market_service()
        if latitude is not None and longitude is not None:
            live_jobs = await market_service.fetch_live_jobs_by_coordinates(
                role_query=cleaned_target_role,
                latitude=latitude,
                longitude=longitude,
                page=current_page,
            )
        elif cleaned_location_query:
            live_jobs = await market_service.fetch_live_jobs_by_location_query(
                role_query=cleaned_target_role,
                location_query=cleaned_location_query,
                page=current_page,
            )
        else:
            live_jobs = await market_service.fetch_live_jobs(
                role_query=cleaned_target_role,
                page=current_page,
            )
    except JobMarketServiceError as exc:
        return LiveMarketJobsResponse(
            **_build_live_jobs_payload(
                jobs=[],
                query=cleaned_target_role,
                source_name="Adzuna + Himalayas",
                source_url="https://www.adzuna.in/",
                note="India-focused jobs come from Adzuna and remote jobs come from Himalayas.",
                error=str(exc),
                resolved_location_label=cleaned_location_query,
                page=current_page,
            )
        )

    return LiveMarketJobsResponse(
        **_build_live_jobs_payload(
            jobs=live_jobs.jobs,
            query=cleaned_target_role,
            source_name=live_jobs.source_name,
            source_url=live_jobs.source_url,
            note=live_jobs.note,
            resolved_location_label=live_jobs.resolved_location_label,
            page=live_jobs.page,
            has_more=live_jobs.has_more,
        )
    )


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


@router.post("/resume-upgrade", response_model=ResumeUpgradeResponse)
async def resume_upgrade(
    resume_file: UploadFile | None = File(default=None),
    resume_text: str = Form(default=""),
    job_description: str = Form(default=""),
    target_role: str = Form(default=""),
    baseline_score: int | None = Form(default=None),
) -> ResumeUpgradeResponse:
    combined_resume = await _collect_resume_text(resume_file=resume_file, resume_text=resume_text)
    cleaned_job_description = job_description.strip()
    cleaned_target_role = target_role.strip()

    if not cleaned_target_role:
        raise HTTPException(
            status_code=400,
            detail="Select a target role before generating the upgraded resume.",
        )

    if cleaned_job_description:
        effective_job_description = cleaned_job_description
        effective_job_description = (
            f"Selected Role Focus: {cleaned_target_role}\n\n{cleaned_job_description}"
        )
    else:
        effective_job_description = _build_role_based_job_description(cleaned_target_role)

    try:
        analyzer = get_analyzer()
        return analyzer.generate_resume_upgrade(
            resume_text=combined_resume,
            job_description=effective_job_description,
            baseline_score=baseline_score,
        )
    except (LLMConfigurationError, GroqConfigurationError, LocalLLMConfigurationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (LLMServiceError, GroqServiceError, LocalLLMServiceError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Resume upgrade failed. Please retry. ({exc})",
        ) from exc


@router.post("/compile-latex")
async def compile_latex_preview(payload: LatexCompileRequest) -> Response:
    try:
        compiler = get_latex_compiler()
        pdf_bytes = compiler.compile_pdf(payload.latex_resume)
    except LaTeXCompilerUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LaTeXCompilationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    headers = {"Content-Disposition": 'inline; filename="updated-resume-preview.pdf"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/compile-latex-preview-image")
async def compile_latex_preview_image(payload: LatexCompileRequest) -> Response:
    try:
        compiler = get_latex_compiler()
        pdf_bytes = compiler.compile_pdf(payload.latex_resume)
        preview_service = get_pdf_preview_service()
        png_bytes = preview_service.render_first_page_png(pdf_bytes)
    except LaTeXCompilerUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LaTeXCompilationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFPreviewUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PDFPreviewRenderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    headers = {"Content-Disposition": 'inline; filename="updated-resume-preview.png"'}
    return Response(content=png_bytes, media_type="image/png", headers=headers)


@router.post("/render-pdf-preview")
async def render_pdf_preview(resume_file: UploadFile = File(...)) -> Response:
    if not resume_file.filename or not _is_pdf_upload(resume_file):
        raise HTTPException(status_code=400, detail="Resume file must be a PDF.")

    file_bytes = await resume_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    try:
        preview_service = get_pdf_preview_service()
        png_bytes = preview_service.render_first_page_png(file_bytes)
    except PDFPreviewUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PDFPreviewRenderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    headers = {"Content-Disposition": 'inline; filename="resume-preview.png"'}
    return Response(content=png_bytes, media_type="image/png", headers=headers)


# ============================================================================
# ML-POWERED ANALYSIS ENDPOINTS (scikit-learn TF-IDF + Cosine Similarity)
# ============================================================================

@router.post("/ml-insights")
async def get_ml_insights(
    resume: str = Form(...),
    job_description: str = Form(default=""),
    role: str = Form(default="ml_engineer"),
) -> dict:
    """
    Get ML-based resume analysis using scikit-learn models.
    
    ML Pipeline:
    - TF-IDF Vectorization + Logistic Regression for quality scoring
    - Cosine Similarity for resume-job matching
    - Feature extraction for NLP analysis
    
    Returns: ML predictions, confidence scores, and feature importance
    """
    analyzer = get_analyzer()
    insights = analyzer.get_ml_insights(
        resume_text=resume,
        job_description=job_description,
        role=role
    )
    return insights


@router.post("/ml-quality-score")
async def get_ml_quality_score(resume: str = Form(...)) -> dict:
    """
    Get ML-predicted resume quality score using trained Logistic Regression classifier.
    
    ML Model: TF-IDF Vectorizer + Logistic Regression
    Returns: Quality score (0-100), confidence, quality level, top keywords
    """
    analyzer = get_analyzer()
    result = analyzer.get_ml_quality_score(resume)
    return result


@router.post("/ml-skill-similarity")
async def get_ml_skill_similarity(
    resume: str = Form(...),
    job_description: str = Form(...),
    role: str = Form(default="ml_engineer"),
) -> dict:
    """
    Get semantic similarity score and skill matching using TF-IDF + Cosine Similarity.
    
    ML Model: TF-IDF Vectorizer + Cosine Similarity Matrix
    Returns: Semantic similarity score, skill match percentage, matched/missing skills
    """
    analyzer = get_analyzer()
    result = analyzer.get_ml_skill_similarity(resume, job_description, role)
    return result
