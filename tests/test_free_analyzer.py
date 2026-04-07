"""Tests for FreeResumeAnalyzerService — covers skill extraction, score calculation,
bullet rewriting, role suggestion, and ATS suggestion generation."""

import pytest

from app.services.free_analyzer import FreeResumeAnalyzerService


@pytest.fixture
def analyzer():
    return FreeResumeAnalyzerService()


# ─── 1. Skill Extraction ───────────────────────────────────────────────

SAMPLE_RESUME = (
    "3+ years of experience with Python, FastAPI, and PostgreSQL. "
    "Built REST APIs and microservices on AWS using Docker and Kubernetes. "
    "Proficient with Git, CI/CD pipelines, and agile methodologies."
)


class TestSkillExtraction:
    def test_detects_known_skills(self, analyzer):
        normalized = analyzer._normalize_text(SAMPLE_RESUME)
        skills = analyzer._extract_skills(normalized)

        assert "Python" in skills
        assert "FastAPI" in skills
        assert "Docker" in skills
        assert "Kubernetes" in skills
        assert "AWS" in skills
        assert "Git" in skills
        assert "CI/CD" in skills
        assert "Microservices" in skills

    def test_does_not_hallucinate_skills(self, analyzer):
        normalized = analyzer._normalize_text(SAMPLE_RESUME)
        skills = analyzer._extract_skills(normalized)

        assert "TensorFlow" not in skills
        assert "PyTorch" not in skills
        assert "React" not in skills
        assert "Angular" not in skills

    def test_empty_text_returns_empty_set(self, analyzer):
        skills = analyzer._extract_skills("")
        assert skills == set()


# ─── 2. Score Calculation ───────────────────────────────────────────────

class TestScoreCalculation:
    def test_full_match_scores_high(self, analyzer):
        jd_skills = {"Python", "Docker", "AWS"}
        matching = sorted(jd_skills)
        missing = []
        score = analyzer._calculate_match_score(matching, missing, jd_skills)
        assert score >= 80, f"Full match should score ≥80, got {score}"

    def test_no_match_scores_low(self, analyzer):
        jd_skills = {"Python", "Docker", "AWS", "Kubernetes", "Terraform"}
        matching = []
        missing = sorted(jd_skills)
        score = analyzer._calculate_match_score(matching, missing, jd_skills)
        assert score <= 40, f"No match should score ≤40, got {score}"

    def test_partial_match_in_range(self, analyzer):
        jd_skills = {"Python", "Docker", "AWS", "Kubernetes"}
        matching = ["Python", "Docker"]
        missing = ["AWS", "Kubernetes"]
        score = analyzer._calculate_match_score(matching, missing, jd_skills)
        assert 30 <= score <= 80, f"Partial match should be 30-80, got {score}"

    def test_empty_jd_returns_baseline(self, analyzer):
        score = analyzer._calculate_match_score([], [], set())
        assert score == 65, "Empty JD should return baseline of 65"


# ─── 3. Bullet Rewriting ───────────────────────────────────────────────

class TestBulletRewriting:
    def test_rewrites_produce_correct_count(self, analyzer):
        resume = (
            "- Developed backend services using Python and FastAPI\n"
            "- Built CI/CD pipelines that reduced deployment time by 40%\n"
            "- Designed REST APIs consumed by 10k+ daily active users\n"
        )
        bullets = analyzer._rewrite_bullets(
            resume_text=resume,
            role_focus="Backend Engineer",
            matching_skills=["Python", "FastAPI"],
            jd_skills={"Python", "FastAPI", "Docker"},
        )
        assert len(bullets) == 3
        for bullet in bullets:
            assert len(bullet) > 20, "Each rewritten bullet should be substantial"

    def test_rewrites_contain_action_verbs(self, analyzer):
        resume = "- Built a machine learning pipeline for fraud detection"
        bullets = analyzer._rewrite_bullets(
            resume_text=resume,
            role_focus="ML Engineer",
            matching_skills=["Python"],
            jd_skills={"Python", "TensorFlow"},
        )
        action_verbs = {"Led", "Built", "Designed", "Improved", "Implemented", "Optimized", "Delivered"}
        assert any(b.split()[0] in action_verbs for b in bullets), \
            "At least one bullet should start with an action verb"

    def test_empty_resume_still_produces_output(self, analyzer):
        bullets = analyzer._rewrite_bullets(
            resume_text="",
            role_focus="Software Engineer",
            matching_skills=[],
            jd_skills={"Python"},
        )
        assert len(bullets) >= 1, "Should produce at least one fallback bullet"


# ─── 4. Role Suggestion ────────────────────────────────────────────────

class TestRoleSuggestion:
    def test_backend_resume_suggests_backend_roles(self, analyzer):
        result = analyzer.suggest_roles(SAMPLE_RESUME)

        assert "recommended_roles" in result
        assert len(result["recommended_roles"]) >= 1
        roles_lower = [r.lower() for r in result["recommended_roles"]]
        assert any("backend" in r or "software" in r or "devops" in r for r in roles_lower), \
            f"Python/Docker/AWS resume should suggest backend-ish roles, got {result['recommended_roles']}"

    def test_current_status_is_valid(self, analyzer):
        result = analyzer.suggest_roles(SAMPLE_RESUME)
        valid_statuses = {"Entry Level", "Early Career", "Mid Level", "Senior Level"}
        assert result["current_status"] in valid_statuses

    def test_profile_summary_is_non_empty(self, analyzer):
        result = analyzer.suggest_roles(SAMPLE_RESUME)
        assert len(result["profile_summary"]) > 20


# ─── 5. ATS Suggestion Generation ──────────────────────────────────────

class TestAtsSuggestions:
    def test_missing_skills_trigger_keyword_suggestion(self, analyzer):
        suggestions = analyzer._build_ats_suggestions(
            resume_text="Python developer with 2 years experience",
            matching_skills=["Python"],
            missing_skills=["Docker", "Kubernetes", "AWS"],
            role_focus="DevOps Engineer",
        )
        joined = " ".join(suggestions).lower()
        assert "docker" in joined or "kubernetes" in joined or "aws" in joined, \
            "Should suggest adding missing keywords"

    def test_no_metrics_triggers_quantify_suggestion(self, analyzer):
        suggestions = analyzer._build_ats_suggestions(
            resume_text="Built backend services and improved performance",
            matching_skills=["Python"],
            missing_skills=[],
            role_focus="Backend Engineer",
        )
        joined = " ".join(suggestions).lower()
        assert "quantify" in joined or "metric" in joined, \
            "Should suggest adding quantified impact"
