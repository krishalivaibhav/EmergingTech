import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillKeyword:
    label: str
    patterns: tuple[str, ...]


SKILL_CATALOG: tuple[SkillKeyword, ...] = (
    SkillKeyword("Python", ("python",)),
    SkillKeyword("Java", ("java",)),
    SkillKeyword("C++", ("c++", "cpp")),
    SkillKeyword("JavaScript", ("javascript", "js ")),
    SkillKeyword("TypeScript", ("typescript", "ts ")),
    SkillKeyword("SQL", ("sql", "postgresql", "mysql", "sqlite")),
    SkillKeyword("NoSQL", ("mongodb", "cassandra", "dynamodb", "nosql")),
    SkillKeyword("FastAPI", ("fastapi",)),
    SkillKeyword("Django", ("django",)),
    SkillKeyword("Flask", ("flask",)),
    SkillKeyword("Node.js", ("node.js", "nodejs")),
    SkillKeyword("React", ("react", "reactjs")),
    SkillKeyword("Angular", ("angular",)),
    SkillKeyword("Vue.js", ("vue", "vue.js")),
    SkillKeyword("REST APIs", ("rest api", "restful", "api design")),
    SkillKeyword("GraphQL", ("graphql",)),
    SkillKeyword("Microservices", ("microservices",)),
    SkillKeyword("Docker", ("docker", "containerization")),
    SkillKeyword("Kubernetes", ("kubernetes", "k8s")),
    SkillKeyword("AWS", ("aws", "amazon web services")),
    SkillKeyword("Azure", ("azure",)),
    SkillKeyword("GCP", ("gcp", "google cloud")),
    SkillKeyword("CI/CD", ("ci/cd", "continuous integration", "continuous delivery")),
    SkillKeyword("Git", ("git", "version control")),
    SkillKeyword("Linux", ("linux",)),
    SkillKeyword("Redis", ("redis",)),
    SkillKeyword("RabbitMQ", ("rabbitmq",)),
    SkillKeyword("Kafka", ("kafka",)),
    SkillKeyword("Pandas", ("pandas",)),
    SkillKeyword("NumPy", ("numpy",)),
    SkillKeyword("Scikit-learn", ("scikit", "sklearn")),
    SkillKeyword("TensorFlow", ("tensorflow",)),
    SkillKeyword("PyTorch", ("pytorch",)),
    SkillKeyword("Machine Learning", ("machine learning", "ml ")),
    SkillKeyword("Deep Learning", ("deep learning",)),
    SkillKeyword("NLP", ("nlp", "natural language processing")),
    SkillKeyword("Data Analysis", ("data analysis", "data analytics")),
    SkillKeyword("Data Visualization", ("tableau", "power bi", "data visualization")),
    SkillKeyword("Testing", ("unit test", "pytest", "jest", "testing")),
    SkillKeyword("System Design", ("system design", "scalability", "high availability")),
    SkillKeyword("Agile", ("agile", "scrum", "kanban")),
    SkillKeyword("Problem Solving", ("problem solving", "analytical")),
    SkillKeyword("Communication", ("communication", "stakeholder", "cross-functional")),
    SkillKeyword("Leadership", ("leadership", "mentoring", "lead ")),
    SkillKeyword("Project Management", ("project management", "roadmap", "delivery")),
    SkillKeyword("Security", ("security", "owasp", "authentication", "authorization")),
    SkillKeyword("DevOps", ("devops", "infrastructure as code", "terraform")),
    SkillKeyword("Monitoring", ("monitoring", "prometheus", "grafana", "observability")),
    SkillKeyword("Terraform", ("terraform",)),
    SkillKeyword("MLOps", ("mlops", "model deployment", "feature store")),
)


ROLE_HINTS = (
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack developer",
    "data analyst",
    "data scientist",
    "machine learning engineer",
    "devops engineer",
    "cloud engineer",
    "product manager",
    "business analyst",
)


ROLE_SKILL_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Backend Engineer",
        ("Python", "Java", "SQL", "FastAPI", "Django", "Flask", "REST APIs", "Microservices"),
    ),
    (
        "Full Stack Developer",
        ("JavaScript", "TypeScript", "React", "Node.js", "SQL", "REST APIs", "Git"),
    ),
    (
        "Frontend Engineer",
        ("JavaScript", "TypeScript", "React", "Angular", "Vue.js", "Testing"),
    ),
    (
        "Data Analyst",
        ("SQL", "Pandas", "NumPy", "Data Analysis", "Data Visualization", "Communication"),
    ),
    (
        "Data Scientist",
        (
            "Python",
            "Pandas",
            "NumPy",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Scikit-learn",
        ),
    ),
    (
        "Machine Learning Engineer",
        (
            "Python",
            "Machine Learning",
            "Scikit-learn",
            "TensorFlow",
            "PyTorch",
            "Docker",
            "MLOps",
        ),
    ),
    (
        "DevOps Engineer",
        ("Docker", "Kubernetes", "CI/CD", "Linux", "AWS", "Azure", "GCP", "DevOps", "Monitoring"),
    ),
    (
        "Cloud Engineer",
        ("AWS", "Azure", "GCP", "Kubernetes", "Terraform", "DevOps", "Security"),
    ),
    (
        "Software Engineer",
        (
            "Python",
            "Java",
            "C++",
            "SQL",
            "Git",
            "Testing",
            "System Design",
            "Problem Solving",
        ),
    ),
    (
        "Product Manager",
        ("Project Management", "Communication", "Leadership", "Data Analysis", "Agile"),
    ),
)


ACTION_VERBS = ("Led", "Built", "Designed", "Improved", "Implemented", "Optimized", "Delivered")


class FreeResumeAnalyzerService:
    """Heuristic ATS-like analyzer that works without paid APIs."""

    def suggest_roles(self, resume_text: str) -> dict:
        normalized_resume = self._normalize_text(resume_text)
        resume_skills = self._extract_skills(normalized_resume)
        current_status = self._infer_current_status(resume_text)
        recommended_roles = self._recommend_roles(resume_skills, normalized_resume)

        top_skills = ", ".join(sorted(resume_skills)[:6]) if resume_skills else "foundational technical exposure"
        profile_summary = (
            f"Profile appears {current_status.lower()} with strengths around {top_skills}. "
            "Targeting role-specific projects and quantified outcomes will improve role fit confidence."
        )

        return {
            "current_status": current_status,
            "profile_summary": profile_summary,
            "recommended_roles": recommended_roles[:8],
        }

    def generate_structured_analysis(self, resume_text: str, job_description: str) -> dict:
        resume_clean = self._normalize_text(resume_text)
        jd_clean = self._normalize_text(job_description)

        jd_skills = self._extract_skills(jd_clean)
        resume_skills = self._extract_skills(resume_clean)
        matching_skills = sorted(jd_skills.intersection(resume_skills))
        missing_skills = sorted(jd_skills.difference(resume_skills))

        role_focus = self._detect_role(jd_clean)
        match_score = self._calculate_match_score(matching_skills, missing_skills, jd_skills)
        improved_bullets = self._rewrite_bullets(resume_text, role_focus, matching_skills, jd_skills)
        ats_suggestions = self._build_ats_suggestions(
            resume_text=resume_text,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            role_focus=role_focus,
        )
        interview_questions = self._build_interview_questions(
            role_focus=role_focus,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
        )
        resume_summary = self._build_summary(
            resume_text=resume_text,
            role_focus=role_focus,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
        )

        suggested_keywords = self._ordered_unique(missing_skills + matching_skills + sorted(jd_skills))

        return {
            "match_score": match_score,
            "matching_skills": matching_skills[:12],
            "missing_skills": missing_skills[:12],
            "resume_summary": resume_summary,
            "ats_suggestions": ats_suggestions[:8],
            "improved_bullets": improved_bullets[:6],
            "interview_questions": interview_questions[:8],
            "tailor_my_resume": {
                "improved_professional_summary": self._tailored_professional_summary(
                    role_focus, matching_skills, missing_skills
                ),
                "stronger_project_bullets": improved_bullets[:4],
                "suggested_skills_keywords": suggested_keywords[:12],
            },
        }

    def generate_resume_upgrade(self, resume_text: str, job_description: str) -> dict:
        analysis = self.generate_structured_analysis(resume_text, job_description)
        role_focus = self._detect_role(self._normalize_text(job_description))
        tailored = analysis.get("tailor_my_resume", {})
        suggested_keywords = tailored.get("suggested_skills_keywords", [])
        improved_summary = (
            tailored.get("improved_professional_summary")
            or analysis.get("resume_summary")
            or f"Professional targeting {role_focus} opportunities."
        )
        improved_bullets = analysis.get("improved_bullets", [])[:5]

        original_snapshot = self._build_original_snapshot(resume_text)
        updated_snapshot = self._build_updated_snapshot(
            improved_summary=improved_summary,
            suggested_keywords=suggested_keywords,
            improved_bullets=improved_bullets,
        )
        score_before = int(analysis.get("match_score", 0))
        score_after = min(
            100,
            max(
                score_before,
                score_before + 8 + min(len(analysis.get("missing_skills", [])), 4),
            ),
        )
        latex_resume = self._build_latex_resume(
            resume_text=resume_text,
            improved_summary=improved_summary,
            suggested_keywords=suggested_keywords,
            improved_bullets=improved_bullets,
        )

        improvement_summary = (
            f"This upgraded resume keeps the original profile direction but rewrites it for stronger {role_focus} ATS alignment. "
            "The draft prioritizes clearer summary language, keyword density, and stronger impact bullets."
        )
        key_improvements = self._ordered_unique(
            [
                *analysis.get("ats_suggestions", [])[:4],
                "Rebuilt the resume into an Overleaf-ready LaTeX layout with ATS-friendly section headings.",
                "Concentrated the strongest evidence into a tighter summary, skills block, and rewritten experience bullets.",
            ]
        )[:6]

        latex_notes = [
            "Review names, dates, and organization titles before submitting because PDF text extraction can flatten original formatting.",
            "Compile this .tex file in Overleaf and adjust spacing if your resume content is longer than one page.",
            "If you have exact project names or metrics in the original resume, keep them in the final version for credibility.",
        ]

        return {
            "ats_score_before": score_before,
            "ats_score_after": score_after,
            "improvement_summary": improvement_summary,
            "key_improvements": key_improvements,
            "original_resume_snapshot": original_snapshot,
            "updated_resume_snapshot": updated_snapshot,
            "latex_resume": latex_resume,
            "latex_notes": latex_notes,
        }

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.lower()).strip()

    def _contains_pattern(self, text: str, pattern: str) -> bool:
        normalized = pattern.strip().lower()
        if not normalized:
            return False
        if re.fullmatch(r"[a-z0-9 ]+", normalized):
            escaped = re.escape(normalized)
            return bool(re.search(rf"\b{escaped}\b", text))
        return normalized in text

    def _extract_skills(self, text: str) -> set[str]:
        found: set[str] = set()
        for skill in SKILL_CATALOG:
            if any(self._contains_pattern(text, pattern) for pattern in skill.patterns):
                found.add(skill.label)
        return found

    def _detect_role(self, jd_text: str) -> str:
        for role in ROLE_HINTS:
            if role in jd_text:
                return role.title()

        lines = [line.strip() for line in jd_text.split(".") if line.strip()]
        if lines:
            first = lines[0]
            return " ".join(first.split()[:7]).title()
        return "Target Role"

    def _calculate_match_score(
        self,
        matching_skills: list[str],
        missing_skills: list[str],
        jd_skills: set[str],
    ) -> int:
        if not jd_skills:
            return 65

        ratio = len(matching_skills) / max(len(jd_skills), 1)
        missing_penalty = min(len(missing_skills) * 2, 20)
        score = int(35 + (ratio * 65) - missing_penalty)
        return max(20, min(100, score))

    def _rewrite_bullets(
        self,
        resume_text: str,
        role_focus: str,
        matching_skills: list[str],
        jd_skills: set[str],
    ) -> list[str]:
        source_bullets = self._extract_resume_bullets(resume_text)
        if not source_bullets:
            source_bullets = self._fallback_sentences(resume_text)

        if not source_bullets:
            source_bullets = ["Contributed to engineering and delivery tasks across projects."]

        keywords = matching_skills or sorted(jd_skills)
        rewritten: list[str] = []
        for i, bullet in enumerate(source_bullets[:6]):
            verb = ACTION_VERBS[i % len(ACTION_VERBS)]
            keyword = keywords[i % len(keywords)] if keywords else "role-critical skills"
            cleaned = bullet.strip(" -•*\t")
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.rstrip(".")
            if cleaned:
                core_phrase = cleaned[0].lower() + cleaned[1:]
            else:
                core_phrase = "deliver project outcomes"
            rewritten.append(
                f"{verb} initiatives to {core_phrase}, leveraging {keyword} to align outcomes with {role_focus} expectations."
            )
        return rewritten

    def _extract_resume_bullets(self, resume_text: str) -> list[str]:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        bullets = [line for line in lines if re.match(r"^[-•*]\s+", line)]
        if bullets:
            return bullets
        return [line for line in lines if 40 <= len(line) <= 180][:8]

    def _fallback_sentences(self, text: str) -> list[str]:
        parts = [segment.strip() for segment in re.split(r"[.!?]\s+", text) if segment.strip()]
        return [segment for segment in parts if 40 <= len(segment) <= 200][:6]

    def _build_ats_suggestions(
        self,
        resume_text: str,
        matching_skills: list[str],
        missing_skills: list[str],
        role_focus: str,
    ) -> list[str]:
        suggestions: list[str] = []
        if missing_skills:
            top_missing = ", ".join(missing_skills[:4])
            suggestions.append(
                f"Add evidence-backed references to these missing keywords where relevant: {top_missing}."
            )

        if not re.search(r"\b\d+%|\$\d+|\b\d+\s*(users|clients|ms|seconds|hours|days)\b", resume_text.lower()):
            suggestions.append(
                "Quantify impact with metrics (e.g., %, latency, revenue, user growth) for stronger ATS and recruiter signals."
            )

        if len(matching_skills) < 4:
            suggestions.append(
                "Increase overlap with the job by mirroring exact skill phrasing from the JD in your experience and skills sections."
            )

        suggestions.append(
            f"Prioritize the most relevant {role_focus} achievements in the top third of the resume."
        )
        suggestions.append(
            "Use strong action verbs and one clear outcome per bullet to improve skimmability."
        )
        suggestions.append(
            "Ensure section headers are ATS-friendly: Summary, Skills, Experience, Projects, Education."
        )
        return suggestions

    def _build_interview_questions(
        self,
        role_focus: str,
        matching_skills: list[str],
        missing_skills: list[str],
    ) -> list[str]:
        questions = [
            f"Walk us through a project that best demonstrates your fit for this {role_focus} role.",
            "Describe a time you handled a difficult technical tradeoff and what decision framework you used.",
            "How do you prioritize tasks when deadlines shift and multiple stakeholders are involved?",
        ]

        for skill in matching_skills[:3]:
            questions.append(f"How have you used {skill} to deliver measurable business or product impact?")

        for skill in missing_skills[:2]:
            questions.append(
                f"The role requires {skill}. How would you ramp up quickly and apply it in your first 60 days?"
            )

        return self._ordered_unique(questions)

    def _build_summary(
        self,
        resume_text: str,
        role_focus: str,
        matching_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        years_match = re.search(r"\b(\d{1,2})\+?\s+years\b", resume_text.lower())
        years_text = f"{years_match.group(1)}+ years of experience" if years_match else "relevant experience"

        strengths = ", ".join(matching_skills[:5]) if matching_skills else "core technical foundations"
        gap_text = (
            f" Key gaps include {', '.join(missing_skills[:3])}."
            if missing_skills
            else " Skill alignment is strong across the listed requirements."
        )

        return (
            f"Candidate shows {years_text} with focus areas aligned to {role_focus}. "
            f"Notable strengths include {strengths}.{gap_text}"
        )

    def _tailored_professional_summary(
        self,
        role_focus: str,
        matching_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        top_match = ", ".join(matching_skills[:4]) if matching_skills else "modern engineering practices"
        if missing_skills:
            learning_focus = f" Currently strengthening exposure to {', '.join(missing_skills[:3])}."
        else:
            learning_focus = " Demonstrates strong end-to-end alignment with the role requirements."
        return (
            f"Results-driven professional targeting {role_focus} opportunities, with proven capability in {top_match}."
            f"{learning_focus}"
        )

    def _ordered_unique(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                ordered.append(item)
        return ordered

    def _recommend_roles(self, resume_skills: set[str], normalized_resume: str) -> list[str]:
        scored_roles: list[tuple[int, str]] = []
        for role_name, role_skills in ROLE_SKILL_MAP:
            overlap = len(resume_skills.intersection(set(role_skills)))
            if overlap > 0:
                scored_roles.append((overlap, role_name))

        ranked = [
            role
            for _, role in sorted(scored_roles, key=lambda item: (-item[0], item[1]))
        ]
        if ranked:
            return ranked

        if any(term in normalized_resume for term in ("machine learning", "data science", "nlp")):
            return ["Data Scientist", "Machine Learning Engineer", "Data Analyst"]
        if any(term in normalized_resume for term in ("react", "frontend", "ui")):
            return ["Frontend Engineer", "Full Stack Developer", "Software Engineer"]
        if any(term in normalized_resume for term in ("aws", "kubernetes", "devops", "cloud")):
            return ["DevOps Engineer", "Cloud Engineer", "Backend Engineer"]

        return ["Software Engineer", "Backend Engineer", "Full Stack Developer"]

    def _infer_current_status(self, resume_text: str) -> str:
        lower_text = resume_text.lower()
        year_matches = [int(match) for match in re.findall(r"\b(\d{1,2})\+?\s+years?\b", lower_text)]
        max_years = max(year_matches) if year_matches else 0

        if max_years >= 8:
            return "Senior Level"
        if max_years >= 4:
            return "Mid Level"
        if max_years >= 1:
            return "Early Career"
        if any(term in lower_text for term in ("student", "intern", "fresher", "graduate")):
            return "Entry Level"
        return "Early Career"

    def _build_original_snapshot(self, resume_text: str) -> str:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        if not lines:
            return "Original resume text could not be summarized."

        preview_lines = lines[:12]
        return "\n".join(preview_lines)

    def _build_updated_snapshot(
        self,
        improved_summary: str,
        suggested_keywords: list[str],
        improved_bullets: list[str],
    ) -> str:
        parts = [
            "SUMMARY",
            improved_summary,
            "",
            "KEYWORDS",
            ", ".join(suggested_keywords[:10]) if suggested_keywords else "Add role-matched ATS keywords here.",
            "",
            "EXPERIENCE HIGHLIGHTS",
            *[f"- {bullet}" for bullet in improved_bullets[:4]],
        ]
        return "\n".join(part for part in parts if part is not None).strip()

    def _extract_resume_header(self, resume_text: str) -> tuple[str, list[str]]:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        if not lines:
            return ("Candidate Name", [])

        name = lines[0][:80]
        metadata: list[str] = []
        for line in lines[1:5]:
            if any(token in line.lower() for token in ("@", "linkedin", "github", "+", "www", "http")):
                metadata.append(line)
        return (name, metadata[:2])

    def _latex_escape(self, value: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        escaped = value
        for raw, replacement in replacements.items():
            escaped = escaped.replace(raw, replacement)
        return escaped

    def _build_latex_resume(
        self,
        resume_text: str,
        improved_summary: str,
        suggested_keywords: list[str],
        improved_bullets: list[str],
    ) -> str:
        name, metadata = self._extract_resume_header(resume_text)
        education_lines = self._extract_section_lines(
            resume_text,
            ("education", "academic background"),
        )
        projects_lines = self._extract_section_lines(
            resume_text,
            ("projects", "project experience"),
        )

        header_meta = " $\\vert$ ".join(self._latex_escape(item) for item in metadata) or "Email $\\vert$ LinkedIn $\\vert$ GitHub"
        bullets_block = "\n".join(
            f"  \\item {self._latex_escape(bullet)}" for bullet in (improved_bullets or ["Add your strongest experience bullets here."])
        )
        education_block = "\n".join(
            f"  \\item {self._latex_escape(line)}" for line in (education_lines[:4] or ["Add your degree, institution, and graduation details here."])
        )
        projects_block = "\n".join(
            f"  \\item {self._latex_escape(line)}" for line in (projects_lines[:4] or improved_bullets[:3] or ["Add project evidence that supports the target role."])
        )
        skills_line = self._latex_escape(", ".join(suggested_keywords[:12])) or "Role-aligned skills"

        return (
            "\\documentclass[11pt]{article}\n"
            "\\usepackage[margin=0.7in]{geometry}\n"
            "\\usepackage[hidelinks]{hyperref}\n"
            "\\usepackage{enumitem}\n"
            "\\setlength{\\parindent}{0pt}\n"
            "\\pagenumbering{gobble}\n\n"
            "\\begin{document}\n"
            f"{{\\LARGE \\textbf{{{self._latex_escape(name)}}}}}\\\\\n"
            f"{header_meta}\\\\[0.6em]\n\n"
            "\\section*{Professional Summary}\n"
            f"{self._latex_escape(improved_summary)}\n\n"
            "\\section*{Skills}\n"
            f"{skills_line}\n\n"
            "\\section*{Experience Highlights}\n"
            "\\begin{itemize}[leftmargin=1.2em]\n"
            f"{bullets_block}\n"
            "\\end{itemize}\n\n"
            "\\section*{Projects}\n"
            "\\begin{itemize}[leftmargin=1.2em]\n"
            f"{projects_block}\n"
            "\\end{itemize}\n\n"
            "\\section*{Education}\n"
            "\\begin{itemize}[leftmargin=1.2em]\n"
            f"{education_block}\n"
            "\\end{itemize}\n"
            "\\end{document}\n"
        )

    def _extract_section_lines(self, resume_text: str, aliases: tuple[str, ...]) -> list[str]:
        lines = [line.strip() for line in resume_text.splitlines()]
        collected: list[str] = []
        inside_section = False
        for line in lines:
            normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
            if any(alias in normalized for alias in aliases):
                inside_section = True
                continue
            if inside_section and normalized in {
                "summary",
                "skills",
                "technical skills",
                "experience",
                "professional experience",
                "projects",
                "education",
                "certifications",
            }:
                break
            if inside_section and line.strip():
                collected.append(line.strip())
        return collected
