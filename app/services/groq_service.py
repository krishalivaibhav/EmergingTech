import json
import os
import re
from textwrap import dedent
from typing import Any


class GroqConfigurationError(RuntimeError):
    """Raised when required Groq configuration is missing."""


class GroqServiceError(RuntimeError):
    """Raised when the Groq request fails or returns malformed output."""


class GroqService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key or os.getenv("GROQ_API_KEY", "")).strip()
        self.model = (model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")).strip()

        if not self.api_key:
            raise GroqConfigurationError(
                "GROQ_API_KEY is not set. Add it to your environment or .env file."
            )

        try:
            from groq import Groq
        except ModuleNotFoundError as exc:
            raise GroqConfigurationError(
                "The `groq` package is not installed. Install dependencies or switch to ANALYZER_MODE=free."
            ) from exc

        self.client = Groq(api_key=self.api_key)

    def generate_structured_analysis(self, resume_text: str, job_description: str) -> dict[str, Any]:
        system_prompt = dedent(
            """
            You are an expert recruiter and ATS evaluator.
            Compare the candidate resume with the provided job description.
            Return practical, concise, specific output as valid JSON only.

            Rules:
            - Do not use markdown.
            - Return only JSON.
            - match_score must be an integer in [0, 100].
            - Keep lists focused and role-relevant.

            Required JSON shape:
            {
              "match_score": 0,
              "matching_skills": [],
              "missing_skills": [],
              "resume_summary": "",
              "ats_suggestions": [],
              "improved_bullets": [],
              "interview_questions": [],
              "tailor_my_resume": {
                "improved_professional_summary": "",
                "stronger_project_bullets": [],
                "suggested_skills_keywords": []
              }
            }
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Job Description:
            {job_description}

            Candidate Resume:
            {resume_text}
            """
        ).strip()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - network/API failures
            raise GroqServiceError(f"Groq request failed: {exc}") from exc

        if not completion.choices:
            raise GroqServiceError("Groq returned no choices.")

        content = completion.choices[0].message.content
        if not content:
            raise GroqServiceError("Groq returned empty content.")

        return self._load_json(content)

    def generate_role_suggestions(self, resume_text: str) -> dict[str, Any]:
        system_prompt = dedent(
            """
            You are an expert recruiter.
            Infer the candidate's current status and suggest realistic target job roles from the resume.
            Return valid JSON only.

            Rules:
            - Do not use markdown.
            - Return only JSON.
            - recommended_roles should be 4 to 8 concise role titles.
            - current_status should be one of: Entry Level, Early Career, Mid Level, Senior Level.

            Required JSON shape:
            {
              "current_status": "",
              "profile_summary": "",
              "recommended_roles": []
            }
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Candidate Resume:
            {resume_text}
            """
        ).strip()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - network/API failures
            raise GroqServiceError(f"Groq role suggestion failed: {exc}") from exc

        if not completion.choices:
            raise GroqServiceError("Groq returned no choices for role suggestion.")

        content = completion.choices[0].message.content
        if not content:
            raise GroqServiceError("Groq returned empty content for role suggestion.")

        return self._load_json(content)

    def _load_json(self, raw_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        json_match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        raise GroqServiceError("Groq response was not valid JSON.")
