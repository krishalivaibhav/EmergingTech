import os
from typing import Any

from app.models.schemas import (
    CVScanResponse,
    AnalysisResponse,
    ResumeUpgradeResponse,
    RoleSuggestionResponse,
    TailorMyResume,
)
from app.services.free_analyzer import FreeResumeAnalyzerService
from app.services.groq_service import GroqConfigurationError, GroqService, GroqServiceError
from app.services.llm_service import LLMConfigurationError, LLMService, LLMServiceError
from app.services.local_llm_service import (
    LocalLLMConfigurationError,
    LocalLLMService,
    LocalLLMServiceError,
)
from app.services.resume_template_service import ResumeTemplateService


class ResumeJobAnalyzer:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        groq_service: GroqService | None = None,
        local_llm_service: LocalLLMService | None = None,
        free_service: FreeResumeAnalyzerService | None = None,
        resume_template_service: ResumeTemplateService | None = None,
        mode: str | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.groq_service = groq_service
        self.local_llm_service = local_llm_service
        self.free_service = free_service or FreeResumeAnalyzerService()
        self.resume_template_service = resume_template_service or ResumeTemplateService()
        configured_mode = (mode or os.getenv("ANALYZER_MODE", "auto")).strip().lower()
        self.mode = (
            configured_mode
            if configured_mode in {"auto", "openai", "groq", "local_llm", "free"}
            else "auto"
        )

    def analyze(self, resume_text: str, job_description: str) -> AnalysisResponse:
        raw_result = self._run_analysis(resume_text=resume_text, job_description=job_description)
        normalized = self._normalize_result(raw_result)
        return AnalysisResponse(**normalized)

    def suggest_roles(self, resume_text: str) -> RoleSuggestionResponse:
        raw_result = self._run_role_suggestion(resume_text=resume_text)
        normalized = self._normalize_role_suggestion(raw_result)
        return RoleSuggestionResponse(**normalized)

    def scan_cv(self, resume_text: str) -> CVScanResponse:
        role_suggestion = self.suggest_roles(resume_text=resume_text)
        primary_role = (
            role_suggestion.recommended_roles[0]
            if role_suggestion.recommended_roles
            else "Software Engineer"
        )
        baseline_job_description = (
            f"Target Role: {primary_role}\n"
            "Perform a standalone ATS readiness evaluation of this resume. "
            "Assess clarity, impact, measurable outcomes, role alignment, "
            "technical coverage, and communication strength."
        )
        cv_analysis = self.analyze(
            resume_text=resume_text,
            job_description=baseline_job_description,
        )

        return CVScanResponse(
            cv_score=cv_analysis.match_score,
            current_status=role_suggestion.current_status,
            profile_summary=role_suggestion.profile_summary,
            recommended_roles=role_suggestion.recommended_roles,
            resume_summary=cv_analysis.resume_summary,
            top_strengths=cv_analysis.matching_skills,
            improvement_areas=cv_analysis.missing_skills,
            ats_suggestions=cv_analysis.ats_suggestions,
            improved_bullets=cv_analysis.improved_bullets,
        )

    def generate_resume_upgrade(
        self,
        resume_text: str,
        job_description: str = "",
        baseline_score: int | None = None,
    ) -> ResumeUpgradeResponse:
        effective_job_description = job_description.strip()
        if not effective_job_description:
            role_suggestion = self.suggest_roles(resume_text=resume_text)
            primary_role = (
                role_suggestion.recommended_roles[0]
                if role_suggestion.recommended_roles
                else "Software Engineer"
            )
            effective_job_description = (
                f"Target Role: {primary_role}\n"
                "Generate an ATS-optimized upgraded resume and Overleaf-ready LaTeX rewrite. "
                "Preserve the original section structure where possible while improving clarity, keywords, and impact."
            )

        raw_result = self._run_resume_upgrade(
            resume_text=resume_text,
            job_description=effective_job_description,
        )
        template_bundle = self.resume_template_service.build_upgrade_bundle(
            resume_text=resume_text,
            upgrade_data=raw_result,
        )
        raw_result["original_resume_snapshot"] = template_bundle["original_resume_snapshot"]
        raw_result["updated_resume_snapshot"] = template_bundle["updated_resume_snapshot"]
        raw_result["latex_resume"] = template_bundle["latex_resume"]
        normalized = self._normalize_resume_upgrade_result(
            raw_result,
            baseline_score=baseline_score,
        )
        return ResumeUpgradeResponse(**normalized)

    def _run_analysis(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.mode == "free":
            return self.free_service.generate_structured_analysis(resume_text, job_description)

        if self.mode == "openai":
            return self._analyze_with_openai(resume_text, job_description)

        if self.mode == "groq":
            return self._analyze_with_groq(resume_text, job_description)

        if self.mode == "local_llm":
            return self._analyze_with_local_llm(resume_text, job_description)

        if os.getenv("OPENAI_API_KEY", "").strip():
            try:
                return self._analyze_with_openai(resume_text, job_description)
            except (LLMConfigurationError, LLMServiceError):
                pass

        if os.getenv("GROQ_API_KEY", "").strip():
            try:
                return self._analyze_with_groq(resume_text, job_description)
            except (GroqConfigurationError, GroqServiceError):
                pass

        try:
            return self._analyze_with_local_llm(resume_text, job_description)
        except (LocalLLMConfigurationError, LocalLLMServiceError):
            return self.free_service.generate_structured_analysis(resume_text, job_description)

    def _run_resume_upgrade(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.mode == "free":
            return self.free_service.generate_resume_upgrade(resume_text, job_description)

        if self.mode == "openai":
            return self._upgrade_with_openai(resume_text, job_description)

        if self.mode == "groq":
            return self._upgrade_with_groq(resume_text, job_description)

        if self.mode == "local_llm":
            return self._upgrade_with_local_llm(resume_text, job_description)

        if os.getenv("OPENAI_API_KEY", "").strip():
            try:
                return self._upgrade_with_openai(resume_text, job_description)
            except (LLMConfigurationError, LLMServiceError):
                pass

        if os.getenv("GROQ_API_KEY", "").strip():
            try:
                return self._upgrade_with_groq(resume_text, job_description)
            except (GroqConfigurationError, GroqServiceError):
                pass

        try:
            return self._upgrade_with_local_llm(resume_text, job_description)
        except (LocalLLMConfigurationError, LocalLLMServiceError):
            return self.free_service.generate_resume_upgrade(resume_text, job_description)

    def _run_role_suggestion(self, resume_text: str) -> dict[str, Any]:
        if self.mode == "free":
            return self.free_service.suggest_roles(resume_text)

        if self.mode == "openai":
            return self._suggest_roles_with_openai(resume_text)

        if self.mode == "groq":
            return self._suggest_roles_with_groq(resume_text)

        if self.mode == "local_llm":
            return self._suggest_roles_with_local_llm(resume_text)

        if os.getenv("OPENAI_API_KEY", "").strip():
            try:
                return self._suggest_roles_with_openai(resume_text)
            except (LLMConfigurationError, LLMServiceError):
                pass

        if os.getenv("GROQ_API_KEY", "").strip():
            try:
                return self._suggest_roles_with_groq(resume_text)
            except (GroqConfigurationError, GroqServiceError):
                pass

        try:
            return self._suggest_roles_with_local_llm(resume_text)
        except (LocalLLMConfigurationError, LocalLLMServiceError):
            return self.free_service.suggest_roles(resume_text)

    def _analyze_with_local_llm(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.local_llm_service is None:
            self.local_llm_service = LocalLLMService()

        return self.local_llm_service.generate_structured_analysis(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _analyze_with_openai(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.llm_service is None:
            self.llm_service = LLMService()

        return self.llm_service.generate_structured_analysis(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _analyze_with_groq(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.groq_service is None:
            self.groq_service = GroqService()

        return self.groq_service.generate_structured_analysis(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _upgrade_with_local_llm(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.local_llm_service is None:
            self.local_llm_service = LocalLLMService()

        return self.local_llm_service.generate_resume_upgrade(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _upgrade_with_openai(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.llm_service is None:
            self.llm_service = LLMService()

        return self.llm_service.generate_resume_upgrade(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _upgrade_with_groq(self, resume_text: str, job_description: str) -> dict[str, Any]:
        if self.groq_service is None:
            self.groq_service = GroqService()

        return self.groq_service.generate_resume_upgrade(
            resume_text=resume_text,
            job_description=job_description,
        )

    def _suggest_roles_with_local_llm(self, resume_text: str) -> dict[str, Any]:
        if self.local_llm_service is None:
            self.local_llm_service = LocalLLMService()

        return self.local_llm_service.generate_role_suggestions(resume_text=resume_text)

    def _suggest_roles_with_openai(self, resume_text: str) -> dict[str, Any]:
        if self.llm_service is None:
            self.llm_service = LLMService()

        return self.llm_service.generate_role_suggestions(resume_text=resume_text)

    def _suggest_roles_with_groq(self, resume_text: str) -> dict[str, Any]:
        if self.groq_service is None:
            self.groq_service = GroqService()

        return self.groq_service.generate_role_suggestions(resume_text=resume_text)

    def _normalize_result(self, data: dict[str, Any]) -> dict[str, Any]:
        tailor_data = data.get("tailor_my_resume", {})
        return {
            "match_score": self._normalize_score(data.get("match_score")),
            "matching_skills": self._normalize_list(data.get("matching_skills")),
            "missing_skills": self._normalize_list(data.get("missing_skills")),
            "resume_summary": self._normalize_text(data.get("resume_summary")),
            "ats_suggestions": self._normalize_list(data.get("ats_suggestions")),
            "improved_bullets": self._normalize_list(data.get("improved_bullets")),
            "interview_questions": self._normalize_list(data.get("interview_questions")),
            "tailor_my_resume": TailorMyResume(
                improved_professional_summary=self._normalize_text(
                    tailor_data.get("improved_professional_summary")
                ),
                stronger_project_bullets=self._normalize_list(
                    tailor_data.get("stronger_project_bullets")
                ),
                suggested_skills_keywords=self._normalize_list(
                    tailor_data.get("suggested_skills_keywords")
                ),
            ),
        }

    def _normalize_role_suggestion(self, data: dict[str, Any]) -> dict[str, Any]:
        roles = self._normalize_list(data.get("recommended_roles"))
        fallback_roles = ["Software Engineer", "Backend Engineer", "Full Stack Developer"]
        return {
            "current_status": self._normalize_text(data.get("current_status")) or "Early Career",
            "profile_summary": self._normalize_text(data.get("profile_summary")),
            "recommended_roles": roles[:8] if roles else fallback_roles,
        }

    def _normalize_resume_upgrade_result(
        self,
        data: dict[str, Any],
        baseline_score: int | None = None,
    ) -> dict[str, Any]:
        model_before = self._normalize_score(data.get("ats_score_before"))
        before = self._normalize_score(baseline_score) if baseline_score is not None else model_before
        after = self._normalize_score(data.get("ats_score_after"))

        latex_resume = self._normalize_text(data.get("latex_resume"))
        if not latex_resume:
            latex_resume = "% Resume upgrade output was empty. Please retry.\n"

        improvement_summary = self._normalize_text(data.get("improvement_summary"))
        key_improvements = self._normalize_list(data.get("key_improvements"))
        original_snapshot = self._normalize_text(data.get("original_resume_snapshot"))
        updated_snapshot = self._normalize_text(data.get("updated_resume_snapshot"))
        latex_notes = self._normalize_list(data.get("latex_notes"))

        if after <= before:
            if baseline_score is not None and self._has_meaningful_upgrade(
                improvement_summary=improvement_summary,
                key_improvements=key_improvements,
                original_snapshot=original_snapshot,
                updated_snapshot=updated_snapshot,
            ):
                after = min(100, before + self._estimate_upgrade_delta(key_improvements))
            else:
                after = before

        return {
            "ats_score_before": before,
            "ats_score_after": after,
            "improvement_summary": improvement_summary,
            "key_improvements": key_improvements,
            "original_resume_snapshot": original_snapshot,
            "updated_resume_snapshot": updated_snapshot,
            "latex_resume": latex_resume,
            "latex_notes": latex_notes,
        }

    @staticmethod
    def _normalize_score(value: Any) -> int:
        try:
            score = int(float(value))
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, score))

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _normalize_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    for candidate in [
                        str(item.get("description", "")).strip(),
                        str(item.get("note", "")).strip(),
                        str(item.get("text", "")).strip(),
                        str(item.get("section", "")).strip(),
                    ]:
                        if candidate:
                            normalized.append(candidate)
                            break
                    continue
                cleaned = str(item).strip()
                if cleaned:
                    normalized.append(cleaned)
            return normalized
        if isinstance(value, dict):
            return ResumeJobAnalyzer._normalize_list([value])
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _has_meaningful_upgrade(
        improvement_summary: str,
        key_improvements: list[str],
        original_snapshot: str,
        updated_snapshot: str,
    ) -> bool:
        if key_improvements:
            return True
        if improvement_summary:
            return True
        return bool(updated_snapshot and updated_snapshot != original_snapshot)

    @staticmethod
    def _estimate_upgrade_delta(key_improvements: list[str]) -> int:
        return min(12, 4 + min(len(key_improvements), 6))
