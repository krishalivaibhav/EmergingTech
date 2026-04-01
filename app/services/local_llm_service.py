import json
import os
import re
from textwrap import dedent
from typing import Any

import httpx


class LocalLLMConfigurationError(RuntimeError):
    """Raised when local LLM configuration is invalid."""


class LocalLLMServiceError(RuntimeError):
    """Raised when local LLM calls fail or output is malformed."""


class LocalLLMService:
    """Ollama-based local LLM service for keyless structured analysis."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).strip()
        self.model = (model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")).strip()

        configured_timeout = timeout_seconds
        if configured_timeout is None:
            timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")
            try:
                configured_timeout = float(timeout_raw)
            except ValueError:
                configured_timeout = 120.0

        if not self.base_url:
            raise LocalLLMConfigurationError("OLLAMA_BASE_URL cannot be empty.")
        if not self.model:
            raise LocalLLMConfigurationError("OLLAMA_MODEL cannot be empty.")

        self.client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=configured_timeout,
        )

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

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }

        try:
            response = self.client.post("/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise LocalLLMServiceError(
                "Could not connect to Ollama. Ensure Ollama is running and reachable."
            ) from exc

        if response.status_code >= 400:
            raise LocalLLMServiceError(
                f"Ollama returned an error ({response.status_code}): {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LocalLLMServiceError("Ollama returned a non-JSON response.") from exc

        content = (
            data.get("message", {}).get("content")
            or data.get("response")
            or ""
        )
        if not content:
            raise LocalLLMServiceError("Ollama returned empty content.")

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

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }

        try:
            response = self.client.post("/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise LocalLLMServiceError(
                "Could not connect to Ollama. Ensure Ollama is running and reachable."
            ) from exc

        if response.status_code >= 400:
            raise LocalLLMServiceError(
                f"Ollama role suggestion failed ({response.status_code}): {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LocalLLMServiceError("Ollama returned a non-JSON response.") from exc

        content = data.get("message", {}).get("content") or data.get("response") or ""
        if not content:
            raise LocalLLMServiceError("Ollama returned empty content for role suggestion.")

        return self._load_json(content)

    def generate_resume_upgrade(self, resume_text: str, job_description: str) -> dict[str, Any]:
        system_prompt = dedent(
            """
            You are an expert ATS recruiter and resume writer.
            Rebuild the candidate's resume into a stronger ATS-optimized version using the same underlying evidence from the original resume.
            Return valid JSON only.

            Rules:
            - Do not use markdown.
            - Return only JSON.
            - Do not invent employers, degrees, dates, projects, or achievements not supported by the resume text.
            - You may rewrite, reorder, and sharpen content for ATS fit.
            - ats_score_after must be greater than or equal to ats_score_before.
            - key_improvements and latex_notes must be arrays of short strings, not objects.
            - improved_experience_bullets must be an array of short bullet strings.
            - targeted_keywords must be an array of concise ATS keywords.
            - improved_summary must be one concise paragraph.
            - Keep the JSON compact. Do not include long full-resume snapshots.

            Required JSON shape:
            {
              "ats_score_before": 0,
              "ats_score_after": 0,
              "improvement_summary": "",
              "key_improvements": [],
              "improved_summary": "",
              "targeted_keywords": [],
              "improved_experience_bullets": [],
              "latex_notes": []
            }
            """
        ).strip()

        user_prompt = dedent(
            f"""
            Target Role / Job Context:
            {job_description}

            Candidate Resume:
            {resume_text}
            """
        ).strip()

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }

        try:
            response = self.client.post("/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise LocalLLMServiceError(
                "Could not connect to Ollama. Ensure Ollama is running and reachable."
            ) from exc

        if response.status_code >= 400:
            raise LocalLLMServiceError(
                f"Ollama resume upgrade failed ({response.status_code}): {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LocalLLMServiceError("Ollama returned a non-JSON response.") from exc

        content = data.get("message", {}).get("content") or data.get("response") or ""
        if not content:
            raise LocalLLMServiceError("Ollama returned empty content for resume upgrade.")

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

        raise LocalLLMServiceError("Local LLM response was not valid JSON.")
