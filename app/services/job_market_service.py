from __future__ import annotations

from dataclasses import dataclass
import os

import httpx


class JobMarketServiceError(RuntimeError):
    pass


@dataclass
class ResolvedLocation:
    city: str = ""
    state: str = ""
    country_code: str = ""
    country_name: str = ""
    label: str = ""
    query: str = ""


@dataclass
class LiveJobResult:
    jobs: list[dict]
    source_name: str = ""
    source_url: str = ""
    note: str = ""
    resolved_location_label: str = ""
    page: int = 1
    has_more: bool = False


class JobMarketService:
    def __init__(self) -> None:
        self.himalayas_url = "https://himalayas.app/jobs/api/search"
        self.adzuna_base_url = "https://api.adzuna.com/v1/api/jobs"
        self.reverse_geocode_url = "https://nominatim.openstreetmap.org/reverse"
        self.timeout_seconds = 12.0
        self.user_agent = "AI-Resume-Analyzer/1.0 (india-first job search)"
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID", "").strip()
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        self.adzuna_country = os.getenv("ADZUNA_COUNTRY", "in").strip().lower() or "in"

    async def fetch_live_jobs(
        self,
        role_query: str,
        limit: int = 8,
        page: int = 1,
        location_query: str = "",
        country_code: str = "",
        resolved_location_label: str = "",
    ) -> LiveJobResult:
        cleaned_query = str(role_query or "").strip()
        cleaned_location = str(location_query or "").strip()
        current_page = max(int(page or 1), 1)
        if not cleaned_query:
            return LiveJobResult(jobs=[])

        combined_jobs: list[dict] = []
        source_labels: list[str] = []
        non_fatal_errors: list[str] = []
        has_more_sources = False

        if self._has_adzuna_credentials():
            try:
                adzuna_jobs, adzuna_has_more = await self._fetch_adzuna_jobs(
                    role_query=cleaned_query,
                    location_query=cleaned_location,
                    limit=max(4, limit),
                    page=current_page,
                )
                if adzuna_jobs:
                    combined_jobs.extend(adzuna_jobs)
                    source_labels.append("Adzuna")
                has_more_sources = has_more_sources or adzuna_has_more
            except JobMarketServiceError as exc:
                non_fatal_errors.append(str(exc))

        himalayas_country = country_code.upper().strip()
        if not himalayas_country and self.adzuna_country == "in":
            himalayas_country = "IN"

        try:
            remote_jobs, himalayas_has_more = await self._fetch_himalayas_jobs(
                role_query=cleaned_query,
                limit=max(3, limit // 2),
                country_code=himalayas_country,
                page=current_page,
            )
            if remote_jobs:
                combined_jobs.extend(remote_jobs)
                source_labels.append("Himalayas")
            has_more_sources = has_more_sources or himalayas_has_more
        except JobMarketServiceError as exc:
            non_fatal_errors.append(str(exc))

        deduped_jobs = self._dedupe_jobs(combined_jobs)[:limit]
        if not deduped_jobs and non_fatal_errors:
            raise JobMarketServiceError("; ".join(non_fatal_errors))

        source_name = " + ".join(source_labels) if source_labels else "Job Market Sources"
        source_url = self._build_source_url(source_labels)
        note = self._build_note(
            source_labels=source_labels,
            location_label=resolved_location_label or cleaned_location,
            local_enabled=self._has_adzuna_credentials(),
        )
        if non_fatal_errors and deduped_jobs:
            note = f"{note} Some sources were unavailable during this refresh."

        return LiveJobResult(
            jobs=deduped_jobs,
            source_name=source_name,
            source_url=source_url,
            note=note,
            resolved_location_label=resolved_location_label or cleaned_location,
            page=current_page,
            has_more=has_more_sources,
        )

    async def fetch_live_jobs_by_location_query(
        self,
        role_query: str,
        location_query: str,
        limit: int = 8,
        page: int = 1,
    ) -> LiveJobResult:
        cleaned_location = str(location_query or "").strip()
        if not cleaned_location:
            raise JobMarketServiceError("Enter a city or state before running location-based job search.")

        return await self.fetch_live_jobs(
            role_query=role_query,
            limit=limit,
            page=page,
            location_query=cleaned_location,
            country_code="IN" if self.adzuna_country == "in" else "",
            resolved_location_label=cleaned_location,
        )

    async def fetch_live_jobs_by_coordinates(
        self,
        role_query: str,
        latitude: float,
        longitude: float,
        limit: int = 8,
        page: int = 1,
    ) -> LiveJobResult:
        location = await self.reverse_geocode_location(latitude, longitude)
        return await self.fetch_live_jobs(
            role_query=role_query,
            limit=limit,
            page=page,
            location_query=location.query,
            country_code=location.country_code,
            resolved_location_label=location.label,
        )

    async def reverse_geocode_location(self, latitude: float, longitude: float) -> ResolvedLocation:
        params = {
            "format": "jsonv2",
            "lat": latitude,
            "lon": longitude,
            "zoom": 10,
            "addressdetails": 1,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.get(self.reverse_geocode_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # pragma: no cover - network/API failures
            raise JobMarketServiceError(f"Location lookup failed: {exc}") from exc

        address = payload.get("address", {}) if isinstance(payload, dict) else {}
        city = self._first_non_empty(
            address.get("city"),
            address.get("town"),
            address.get("village"),
            address.get("municipality"),
            address.get("county"),
        )
        state = self._first_non_empty(address.get("state_district"), address.get("state"))
        country_code = str(address.get("country_code", "")).strip().upper()
        country_name = str(address.get("country", "")).strip()

        label_parts = [part for part in [city, state] if part]
        label = ", ".join(label_parts) if label_parts else country_name
        query = ", ".join(label_parts) if label_parts else country_name
        if not country_code:
            raise JobMarketServiceError("Location lookup did not return a usable country code.")
        if not query:
            raise JobMarketServiceError("Location lookup did not return a usable city or state.")

        return ResolvedLocation(
            city=city,
            state=state,
            country_code=country_code,
            country_name=country_name,
            label=label,
            query=query,
        )

    async def _fetch_adzuna_jobs(
        self,
        role_query: str,
        location_query: str,
        limit: int,
        page: int,
    ) -> tuple[list[dict], bool]:
        if not self._has_adzuna_credentials():
            return [], False

        current_page = max(int(page or 1), 1)
        endpoint = f"{self.adzuna_base_url}/{self.adzuna_country}/search/{current_page}"
        per_page = min(max(limit, 1), 20)
        params = {
            "app_id": self.adzuna_app_id,
            "app_key": self.adzuna_app_key,
            "results_per_page": per_page,
            "what": role_query,
            "content-type": "application/json",
        }
        if location_query:
            params["where"] = location_query

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # pragma: no cover - network/API failures
            raise JobMarketServiceError(f"Adzuna job lookup failed: {exc}") from exc

        raw_jobs = payload.get("results", []) if isinstance(payload, dict) else []
        jobs = [
            self._normalize_adzuna_job(job)
            for job in raw_jobs[:limit]
            if isinstance(job, dict) and str(job.get("redirect_url", "")).strip()
        ]
        total_count = int(payload.get("count", 0)) if isinstance(payload, dict) else 0
        has_more = total_count > current_page * per_page
        return jobs, has_more

    async def _fetch_himalayas_jobs(
        self,
        role_query: str,
        limit: int,
        country_code: str,
        page: int,
    ) -> tuple[list[dict], bool]:
        params = {
            "q": role_query,
            "sort": "recent",
            "page": max(int(page or 1), 1),
        }
        if country_code:
            params["country"] = country_code.upper()

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.get(self.himalayas_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # pragma: no cover - network/API failures
            raise JobMarketServiceError(f"Himalayas job lookup failed: {exc}") from exc

        raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        normalized_jobs = [self._normalize_himalayas_job(job) for job in raw_jobs[:limit] if isinstance(job, dict)]
        jobs = [job for job in normalized_jobs if job.get("title") and job.get("application_link")]
        has_more = len(raw_jobs) >= limit
        return jobs, has_more

    def _normalize_adzuna_job(self, job: dict) -> dict:
        location = job.get("location") or {}
        area = location.get("area") or []
        display_name = str(location.get("display_name", "")).strip()
        location_summary = display_name or ", ".join(str(part).strip() for part in area if str(part).strip())

        employment_bits = [
            str(job.get("contract_time", "")).strip().replace("_", " "),
            str(job.get("contract_type", "")).strip().replace("_", " "),
        ]
        employment_type = " / ".join(bit.title() for bit in employment_bits if bit)

        return {
            "title": str(job.get("title", "")).strip(),
            "company_name": str((job.get("company") or {}).get("display_name", "")).strip(),
            "location_summary": location_summary or "India",
            "seniority": "",
            "employment_type": employment_type,
            "salary_summary": self._build_adzuna_salary_summary(job),
            "excerpt": self._clip_text(str(job.get("description", "")).strip(), 260),
            "application_link": str(job.get("redirect_url", "")).strip(),
            "source_name": "Adzuna",
            "source_url": "https://www.adzuna.in/",
            "published_at": str(job.get("created", "")).strip(),
        }

    def _normalize_himalayas_job(self, job: dict) -> dict:
        return {
            "title": str(job.get("title", "")).strip(),
            "company_name": str(job.get("companyName", "")).strip(),
            "location_summary": self._build_himalayas_location_summary(job),
            "seniority": str(job.get("seniority", "")).strip(),
            "employment_type": str(job.get("employmentType", "")).strip(),
            "salary_summary": self._build_himalayas_salary_summary(job),
            "excerpt": str(job.get("excerpt", "")).strip(),
            "application_link": str(job.get("applicationLink", "")).strip(),
            "source_name": "Himalayas",
            "source_url": str(job.get("applicationLink", "")).strip() or "https://himalayas.app/jobs",
            "published_at": str(job.get("pubDate", "")).strip(),
        }

    def _build_himalayas_location_summary(self, job: dict) -> str:
        restrictions = job.get("locationRestrictions") or []
        if isinstance(restrictions, list) and restrictions:
            return ", ".join(str(item).strip() for item in restrictions if str(item).strip())
        return "Remote / Worldwide"

    def _build_himalayas_salary_summary(self, job: dict) -> str:
        minimum = job.get("minSalary")
        maximum = job.get("maxSalary")
        currency = str(job.get("currency", "")).strip()
        if minimum and maximum and currency:
            return f"{currency} {int(minimum):,} - {int(maximum):,}"
        if minimum and currency:
            return f"{currency} {int(minimum):,}+"
        if maximum and currency:
            return f"Up to {currency} {int(maximum):,}"
        return ""

    def _build_adzuna_salary_summary(self, job: dict) -> str:
        minimum = job.get("salary_min")
        maximum = job.get("salary_max")
        if minimum and maximum:
            return f"Salary {int(minimum):,} - {int(maximum):,}"
        if minimum:
            return f"Salary {int(minimum):,}+"
        if maximum:
            return f"Up to {int(maximum):,}"
        return ""

    def _build_source_url(self, source_labels: list[str]) -> str:
        if "Adzuna" in source_labels:
            return "https://www.adzuna.in/"
        if "Himalayas" in source_labels:
            return "https://himalayas.app/jobs"
        return ""

    def _build_note(self, source_labels: list[str], location_label: str, local_enabled: bool) -> str:
        if "Adzuna" in source_labels and "Himalayas" in source_labels:
            if location_label:
                return (
                    f"Showing India-focused jobs near {location_label} from Adzuna, plus remote role matches from Himalayas."
                )
            return "Showing India-focused job matches from Adzuna, plus remote role matches from Himalayas."

        if "Adzuna" in source_labels:
            if location_label:
                return f"Showing India-focused jobs near {location_label} from Adzuna."
            return "Showing India-focused job matches from Adzuna."

        if "Himalayas" in source_labels:
            if location_label:
                return f"Showing remote role matches filtered for {location_label} from Himalayas."
            if local_enabled:
                return "Showing remote role matches from Himalayas because local listings were unavailable."
            return "Showing remote role matches from Himalayas. Configure Adzuna to add India local jobs."

        if location_label:
            return f"No matching jobs were found for {location_label} right now."
        return "No matching jobs were found right now."

    def _dedupe_jobs(self, jobs: list[dict]) -> list[dict]:
        deduped: list[dict] = []
        seen: set[str] = set()

        for job in jobs:
            title = str(job.get("title", "")).strip().lower()
            company = str(job.get("company_name", "")).strip().lower()
            link = str(job.get("application_link", "")).strip().lower()
            key = link or f"{title}::{company}"
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(job)

        return deduped

    def _has_adzuna_credentials(self) -> bool:
        return bool(self.adzuna_app_id and self.adzuna_app_key)

    def _clip_text(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def _first_non_empty(self, *values: object) -> str:
        for value in values:
            cleaned = str(value or "").strip()
            if cleaned:
                return cleaned
        return ""
