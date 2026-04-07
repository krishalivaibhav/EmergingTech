from pydantic import BaseModel, Field


class TailorMyResume(BaseModel):
    improved_professional_summary: str = Field(
        default="", description="Improved role-targeted professional summary."
    )
    stronger_project_bullets: list[str] = Field(
        default_factory=list,
        description="Stronger bullet points aligned with job requirements.",
    )
    suggested_skills_keywords: list[str] = Field(
        default_factory=list,
        description="Suggested keyword skills to include for ATS optimization.",
    )


class AnalysisResponse(BaseModel):
    match_score: int = Field(
        ge=0,
        le=100,
        description="Estimated resume-to-job fit score between 0 and 100.",
    )
    matching_skills: list[str] = Field(
        default_factory=list, description="Skills found in both resume and job description."
    )
    missing_skills: list[str] = Field(
        default_factory=list, description="Important job skills absent from the resume."
    )
    resume_summary: str = Field(
        default="", description="Concise recruiter-style summary of the candidate profile."
    )
    ats_suggestions: list[str] = Field(
        default_factory=list, description="Actionable ATS-focused resume improvements."
    )
    improved_bullets: list[str] = Field(
        default_factory=list, description="Rewritten bullet points tailored to the role."
    )
    interview_questions: list[str] = Field(
        default_factory=list, description="Likely interview questions based on role fit."
    )
    tailor_my_resume: TailorMyResume = Field(
        default_factory=TailorMyResume,
        description="Extra resume tailoring suggestions for profile optimization.",
    )
    live_market_jobs: list["LiveMarketJob"] = Field(
        default_factory=list,
        description="Live role-matched market jobs fetched from a public jobs source.",
    )
    live_market_jobs_query: str = Field(
        default="",
        description="Role query used to fetch live market jobs.",
    )
    live_market_jobs_source_name: str = Field(
        default="",
        description="Source name for the live jobs feed.",
    )
    live_market_jobs_source_url: str = Field(
        default="",
        description="Source URL for the live jobs feed.",
    )
    live_market_jobs_note: str = Field(
        default="",
        description="Attribution or caveat for the live jobs feed.",
    )
    live_market_jobs_error: str = Field(
        default="",
        description="Non-fatal live jobs lookup error, if any.",
    )
    live_market_jobs_page: int = Field(
        default=1,
        ge=1,
        description="Current page index for the live jobs result set.",
    )
    live_market_jobs_has_more: bool = Field(
        default=False,
        description="Whether more live jobs are available for the current search.",
    )


class LiveMarketJob(BaseModel):
    title: str = Field(default="", description="Live market job title.")
    company_name: str = Field(default="", description="Hiring company name.")
    location_summary: str = Field(default="", description="Remote/location summary.")
    seniority: str = Field(default="", description="Seniority label from the source.")
    employment_type: str = Field(default="", description="Employment type from the source.")
    salary_summary: str = Field(default="", description="Human-readable salary summary if available.")
    excerpt: str = Field(default="", description="Short job excerpt.")
    application_link: str = Field(default="", description="Direct application or listing URL.")
    source_name: str = Field(default="", description="Source label for this job listing.")
    source_url: str = Field(default="", description="Source URL for this job listing.")
    published_at: str = Field(default="", description="Publication timestamp from the source.")


class LiveMarketJobsResponse(BaseModel):
    live_market_jobs: list[LiveMarketJob] = Field(
        default_factory=list,
        description="Live role-matched market jobs fetched from a public jobs source.",
    )
    live_market_jobs_query: str = Field(
        default="",
        description="Role query used to fetch live market jobs.",
    )
    live_market_jobs_source_name: str = Field(
        default="",
        description="Source name for the live jobs feed.",
    )
    live_market_jobs_source_url: str = Field(
        default="",
        description="Source URL for the live jobs feed.",
    )
    live_market_jobs_note: str = Field(
        default="",
        description="Attribution or caveat for the live jobs feed.",
    )
    live_market_jobs_error: str = Field(
        default="",
        description="Non-fatal live jobs lookup error, if any.",
    )
    live_market_jobs_page: int = Field(
        default=1,
        ge=1,
        description="Current page index for the live jobs result set.",
    )
    live_market_jobs_has_more: bool = Field(
        default=False,
        description="Whether more live jobs are available for the current search.",
    )
    resolved_location_label: str = Field(
        default="",
        description="Resolved user location label used for the job search.",
    )


class RoleSuggestionResponse(BaseModel):
    current_status: str = Field(
        default="",
        description="Inferred candidate seniority/status based on resume evidence.",
    )
    profile_summary: str = Field(
        default="",
        description="Brief summary of candidate profile and strengths.",
    )
    recommended_roles: list[str] = Field(
        default_factory=list,
        description="Recommended target roles relevant to current resume profile.",
    )


class CVScanResponse(BaseModel):
    cv_score: int = Field(ge=0, le=100, description="Overall standalone CV quality score.")
    current_status: str = Field(
        default="", description="Inferred candidate seniority/status from resume."
    )
    profile_summary: str = Field(
        default="", description="High-level profile summary and readiness signal."
    )
    recommended_roles: list[str] = Field(
        default_factory=list, description="Suggested roles based on current CV."
    )
    resume_summary: str = Field(
        default="", description="Recruiter-style CV summary."
    )
    top_strengths: list[str] = Field(
        default_factory=list, description="Top strengths detected in CV content."
    )
    improvement_areas: list[str] = Field(
        default_factory=list, description="Key gaps to improve CV quality."
    )
    ats_suggestions: list[str] = Field(
        default_factory=list, description="Actionable ATS optimization suggestions."
    )
    improved_bullets: list[str] = Field(
        default_factory=list, description="Stronger bullet rewrites for the CV."
    )


class ResumeUpgradeResponse(BaseModel):
    ats_score_before: int = Field(
        ge=0,
        le=100,
        description="Estimated ATS score before applying the upgraded resume rewrite.",
    )
    ats_score_after: int = Field(
        ge=0,
        le=100,
        description="Estimated ATS score after applying the upgraded resume rewrite.",
    )
    improvement_summary: str = Field(
        default="",
        description="High-level explanation of how the upgraded resume improves ATS alignment.",
    )
    key_improvements: list[str] = Field(
        default_factory=list,
        description="Specific before-vs-after improvements reflected in the upgraded resume.",
    )
    original_resume_snapshot: str = Field(
        default="",
        description="Condensed plain-text snapshot of the original resume structure/content.",
    )
    updated_resume_snapshot: str = Field(
        default="",
        description="Condensed plain-text snapshot of the upgraded resume content.",
    )
    latex_resume: str = Field(
        default="",
        description="Overleaf-ready LaTeX source for the upgraded resume.",
    )
    latex_notes: list[str] = Field(
        default_factory=list,
        description="Notes about assumptions or recommended edits before using the generated LaTeX resume.",
    )


class LatexCompileRequest(BaseModel):
    latex_resume: str = Field(
        min_length=1,
        description="Full LaTeX resume source to compile into a PDF preview.",
    )
