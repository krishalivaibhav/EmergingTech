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
