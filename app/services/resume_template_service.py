import copy
import re
from dataclasses import dataclass, field


SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "Summary": ("summary", "professional summary", "profile"),
    "Experience": ("experience", "professional experience", "work experience"),
    "Projects": ("projects", "project experience", "project work"),
    "Skills": ("skills", "technical skills", "core skills"),
    "Education": ("education", "academic background"),
    "Certifications": ("certifications", "licenses", "certification"),
    "Keywords": ("keywords", "target keywords"),
    "Experience Highlights": ("experience highlights",),
}


@dataclass
class ExperienceEntry:
    title: str
    date: str = ""
    organization: str = ""
    location: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class ProjectEntry:
    title: str
    tech_stack: str = ""
    date: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    institution: str
    location: str = ""
    degree: str = ""
    date: str = ""


class ResumeTemplateService:
    """Build a consistent resume preview and LaTeX output from extracted resume text."""

    _date_token = r"(?:(?:\d{1,2}(?:st|nd|rd|th)?\s+)?[A-Za-z]{3,9}\.?\s*\d{4}|\d{4}|Present)"
    _date_regex = re.compile(
        r"^(.*?)"
        r"(?:\s{2,}|\s+)"
        rf"(({_date_token})(?:\s*[–-]\s*({_date_token}))?)$",
        re.IGNORECASE,
    )

    def build_upgrade_bundle(self, resume_text: str, upgrade_data: dict[str, object] | None = None) -> dict[str, str]:
        upgrade_data = upgrade_data or {}
        lines = self._clean_lines(resume_text)
        name, contact_lines, content_start = self._extract_header(lines)
        original_sections = self._extract_sections(lines[content_start:])
        original_section_order = list(original_sections.keys())
        updated_sections = self._extract_sections(
            self._clean_lines(str(upgrade_data.get("updated_resume_snapshot", "")))
        )

        original_experience = self._parse_experience_entries(original_sections.get("Experience", []))
        updated_experience = self._apply_updated_bullets(
            original_entries=copy.deepcopy(original_experience),
            improved_bullets=self._extract_improved_bullets(upgrade_data, updated_sections),
        )

        projects = self._parse_project_entries(original_sections.get("Projects", []))
        education = self._parse_education_entries(original_sections.get("Education", []))
        certifications = self._clean_section_lines(original_sections.get("Certifications", []))
        skills = self._merge_skill_lines(
            original_sections.get("Skills", []),
            self._extract_keywords_from_upgrade(upgrade_data, updated_sections),
        )
        summary = self._extract_summary_from_upgrade(upgrade_data, updated_sections)
        include_summary = "Summary" in original_section_order

        return {
            "original_resume_snapshot": self._build_original_snapshot(
                name=name,
                contact_lines=contact_lines,
                experience_entries=original_experience,
                projects=projects,
                skills=original_sections.get("Skills", []),
                education=education,
                certifications=certifications,
                section_order=original_section_order,
            ),
            "updated_resume_snapshot": self._build_updated_snapshot(
                name=name,
                contact_lines=contact_lines,
                summary=summary if include_summary else "",
                experience_entries=updated_experience,
                projects=projects,
                skills=skills,
                education=education,
                certifications=certifications,
                section_order=original_section_order,
            ),
            "latex_resume": self._build_reference_latex(
                name=name,
                contact_lines=contact_lines,
                summary=summary if include_summary else "",
                experience_entries=updated_experience,
                projects=projects,
                skills=skills,
                education=education,
                certifications=certifications,
                section_order=original_section_order,
            ),
        }

    def _clean_lines(self, value: str) -> list[str]:
        return [line.strip() for line in str(value or "").splitlines() if line.strip()]

    def _extract_header(self, lines: list[str]) -> tuple[str, list[str], int]:
        if not lines:
            return ("Candidate Name", [], 0)

        name = lines[0][:120]
        contact_lines: list[str] = []
        index = 1
        while index < len(lines):
            if self._canonical_heading(lines[index]):
                break
            contact_lines.append(lines[index])
            index += 1
        return (name, contact_lines[:3], index)

    def _canonical_heading(self, line: str) -> str | None:
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        for canonical, aliases in SECTION_ALIASES.items():
            if normalized in aliases:
                return canonical
        return None

    def _extract_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current_heading: str | None = None
        for line in lines:
            heading = self._canonical_heading(line)
            if heading:
                current_heading = heading
                sections.setdefault(heading, [])
                continue
            if current_heading:
                sections[current_heading].append(line)
        return sections

    def _clean_section_lines(self, lines: list[str]) -> list[str]:
        cleaned: list[str] = []
        for line in lines:
            text = line.strip()
            if text:
                cleaned.append(text)
        return cleaned

    def _extract_summary(self, updated_sections: dict[str, list[str]]) -> str:
        summary_lines = updated_sections.get("Summary", [])
        if summary_lines:
            return " ".join(summary_lines)
        return ""

    def _extract_keywords(self, updated_sections: dict[str, list[str]]) -> list[str]:
        raw_lines = updated_sections.get("Keywords", [])
        if not raw_lines:
            return []
        joined = ", ".join(raw_lines)
        return [item.strip() for item in joined.split(",") if item.strip()][:12]

    def _extract_highlight_bullets(self, updated_sections: dict[str, list[str]]) -> list[str]:
        candidates = updated_sections.get("Experience Highlights", []) or updated_sections.get("Experience", [])
        bullets: list[str] = []
        for line in candidates:
            cleaned = re.sub(r"^[-•*]\s*", "", line).strip()
            if cleaned:
                bullets.append(cleaned)
        return bullets[:8]

    def _extract_summary_from_upgrade(
        self,
        upgrade_data: dict[str, object],
        updated_sections: dict[str, list[str]],
    ) -> str:
        summary = str(upgrade_data.get("improved_summary", "")).strip()
        if summary:
            return summary
        return self._extract_summary(updated_sections)

    def _extract_keywords_from_upgrade(
        self,
        upgrade_data: dict[str, object],
        updated_sections: dict[str, list[str]],
    ) -> list[str]:
        keywords = self._normalize_string_list(upgrade_data.get("targeted_keywords"))
        if keywords:
            return keywords[:12]
        return self._extract_keywords(updated_sections)

    def _extract_improved_bullets(
        self,
        upgrade_data: dict[str, object],
        updated_sections: dict[str, list[str]],
    ) -> list[str]:
        bullets = self._normalize_string_list(upgrade_data.get("improved_experience_bullets"))
        if bullets:
            return bullets[:8]
        return self._extract_highlight_bullets(updated_sections)

    def _normalize_string_list(self, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    normalized.extend(
                        candidate
                        for candidate in [
                            str(item.get("description", "")).strip(),
                            str(item.get("note", "")).strip(),
                            str(item.get("text", "")).strip(),
                        ]
                        if candidate
                    )
                    continue
                cleaned = str(item).strip()
                if cleaned:
                    normalized.append(cleaned)
            return normalized
        if isinstance(value, dict):
            return self._normalize_string_list([value])
        cleaned = str(value).strip()
        return [cleaned] if cleaned else []

    def _parse_experience_entries(self, lines: list[str]) -> list[ExperienceEntry]:
        entries: list[ExperienceEntry] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if self._is_bullet(line):
                if not entries:
                    entries.append(ExperienceEntry(title="Experience Highlights"))
                entries[-1].bullets.append(self._clean_bullet(line))
                index += 1
                continue

            title, date = self._split_title_and_date(line)
            organization = ""
            location = ""
            index += 1
            if index < len(lines) and not self._is_bullet(lines[index]):
                organization, location = self._split_organization_and_location(lines[index])
                index += 1

            bullets, index = self._consume_bullets(lines, index, self._looks_like_experience_heading)

            entries.append(
                ExperienceEntry(
                    title=title or "Experience",
                    date=date,
                    organization=organization,
                    location=location,
                    bullets=bullets,
                )
            )
        return entries

    def _parse_project_entries(self, lines: list[str]) -> list[ProjectEntry]:
        entries: list[ProjectEntry] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if self._is_bullet(line):
                if not entries:
                    entries.append(ProjectEntry(title="Project Highlights"))
                entries[-1].bullets.append(self._clean_bullet(line))
                index += 1
                continue

            title, tech_stack, date = self._split_project_heading(line)
            index += 1
            bullets, index = self._consume_bullets(lines, index, self._looks_like_project_heading)

            entries.append(
                ProjectEntry(
                    title=title or "Project",
                    tech_stack=tech_stack,
                    date=date,
                    bullets=bullets,
                )
            )
        return entries

    def _parse_education_entries(self, lines: list[str]) -> list[EducationEntry]:
        entries: list[EducationEntry] = []
        index = 0
        while index < len(lines):
            institution_line = lines[index]
            institution, location = self._split_organization_and_location(institution_line)
            degree = ""
            date = ""
            index += 1
            if index < len(lines) and not self._is_bullet(lines[index]):
                degree, date = self._split_title_and_date(lines[index])
                index += 1
            entries.append(
                EducationEntry(
                    institution=institution or institution_line,
                    location=location,
                    degree=degree,
                    date=date,
                )
            )
        return entries

    def _apply_updated_bullets(
        self,
        original_entries: list[ExperienceEntry],
        improved_bullets: list[str],
    ) -> list[ExperienceEntry]:
        if not improved_bullets:
            return original_entries or [ExperienceEntry(title="Experience Highlights")]

        if not original_entries:
            return [ExperienceEntry(title="Experience Highlights", bullets=improved_bullets)]

        remaining = improved_bullets[:]
        for entry in original_entries:
            slot_count = max(1, len(entry.bullets))
            replacement = remaining[:slot_count]
            if replacement:
                remaining = remaining[slot_count:]
                if entry.bullets:
                    entry.bullets = replacement + entry.bullets[len(replacement):]
                else:
                    entry.bullets = replacement
            if not remaining:
                break
        return original_entries

    def _is_bullet(self, line: str) -> bool:
        return bool(re.match(r"^[-•*]\s+", line))

    def _clean_bullet(self, line: str) -> str:
        cleaned = re.sub(r"^[-•*]\s*", "", line).strip()
        cleaned = re.sub(r"[*_`]+", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _consume_bullets(
        self,
        lines: list[str],
        index: int,
        heading_detector,
    ) -> tuple[list[str], int]:
        bullets: list[str] = []
        while index < len(lines):
            line = lines[index]
            if self._is_bullet(line):
                bullet_parts = [self._clean_bullet(line)]
                index += 1
                while index < len(lines):
                    continuation = lines[index]
                    if self._is_bullet(continuation) or heading_detector(continuation):
                        break
                    bullet_parts.append(self._clean_bullet(continuation))
                    index += 1
                bullets.append(" ".join(part for part in bullet_parts if part).strip())
                continue
            if bullets and not heading_detector(line):
                bullets[-1] = f"{bullets[-1]} {self._clean_bullet(line)}".strip()
                index += 1
                continue
            break
        return bullets, index

    def _looks_like_experience_heading(self, line: str) -> bool:
        title, date = self._split_title_and_date(line)
        return bool(title and date)

    def _looks_like_project_heading(self, line: str) -> bool:
        title, tech_stack, date = self._split_project_heading(line)
        return bool(title and (date or tech_stack))

    def _split_title_and_date(self, line: str) -> tuple[str, str]:
        match = self._date_regex.match(line.strip())
        if match:
            return (match.group(1).strip(), match.group(2).strip())
        return (line.strip(), "")

    def _split_project_heading(self, line: str) -> tuple[str, str, str]:
        working_line = line.strip()
        date = ""
        date_match = re.search(
            rf"(({self._date_token})(?:\s*[–-]\s*({self._date_token}))?)$",
            working_line,
            flags=re.IGNORECASE,
        )
        if date_match:
            date = date_match.group(1).strip()
            working_line = working_line[: date_match.start()].strip(" |-")

        if "|" in working_line:
            title, tech_stack = working_line.split("|", 1)
            return (title.strip(), tech_stack.strip(), date)
        return (working_line, "", date)

    def _split_organization_and_location(self, line: str) -> tuple[str, str]:
        text = line.strip()
        if "," in text:
            left, right = text.rsplit(",", 1)
            left_tokens = left.split()
            if len(left_tokens) >= 2:
                city = left_tokens[-1]
                institution = " ".join(left_tokens[:-1]).strip(" ,")
                location = f"{city}, {right.strip()}".strip()
                if institution and location:
                    return (institution, location)
        if " | " in line:
            left, right = line.split(" | ", 1)
            return (left.strip(), right.strip())
        return (text, "")

    def _merge_skill_lines(self, original_skill_lines: list[str], keywords: list[str]) -> list[str]:
        cleaned = self._clean_section_lines(original_skill_lines)
        return cleaned

    def _build_original_snapshot(
        self,
        name: str,
        contact_lines: list[str],
        experience_entries: list[ExperienceEntry],
        projects: list[ProjectEntry],
        skills: list[str],
        education: list[EducationEntry],
        certifications: list[str],
        section_order: list[str],
    ) -> str:
        sections: list[str] = [name]
        if contact_lines:
            sections.append(" | ".join(contact_lines))
        sections.extend(
            self._build_snapshot_sections(
                summary="",
                experience_entries=experience_entries,
                projects=projects,
                skills=self._clean_section_lines(skills),
                education=education,
                certifications=certifications,
                section_order=section_order,
            )
        )
        return "\n".join(part for part in sections if part.strip()).strip()

    def _build_updated_snapshot(
        self,
        name: str,
        contact_lines: list[str],
        summary: str,
        experience_entries: list[ExperienceEntry],
        projects: list[ProjectEntry],
        skills: list[str],
        education: list[EducationEntry],
        certifications: list[str],
        section_order: list[str],
    ) -> str:
        sections: list[str] = [name]
        if contact_lines:
            sections.append(" | ".join(contact_lines))
        sections.extend(
            self._build_snapshot_sections(
                summary=summary,
                experience_entries=experience_entries,
                projects=projects,
                skills=skills,
                education=education,
                certifications=certifications,
                section_order=section_order,
            )
        )
        return "\n".join(part for part in sections if part.strip()).strip()

    def _build_snapshot_sections(
        self,
        summary: str,
        experience_entries: list[ExperienceEntry],
        projects: list[ProjectEntry],
        skills: list[str],
        education: list[EducationEntry],
        certifications: list[str],
        section_order: list[str],
    ) -> list[str]:
        lines: list[str] = []
        ordered_sections = section_order or ["Experience", "Projects", "Skills", "Education", "Certifications"]
        for section_name in ordered_sections:
            if section_name == "Summary" and summary:
                lines.extend(["", "Summary", summary])
                continue

            if section_name == "Experience" and experience_entries:
                lines.append("")
                lines.append("Experience")
                for entry in experience_entries:
                    heading = entry.title if not entry.date else f"{entry.title} {entry.date}"
                    lines.append(heading.strip())
                    org_line = " ".join(part for part in [entry.organization, entry.location] if part)
                    if org_line:
                        lines.append(org_line)
                    lines.extend(f"- {bullet}" for bullet in entry.bullets)
                continue

            if section_name == "Projects" and projects:
                lines.append("")
                lines.append("Projects")
                for project in projects:
                    heading_parts = [project.title]
                    if project.tech_stack:
                        heading_parts.append(f"| {project.tech_stack}")
                    if project.date:
                        heading_parts.append(project.date)
                    lines.append(" ".join(part for part in heading_parts if part).strip())
                    lines.extend(f"- {bullet}" for bullet in project.bullets)
                continue

            if section_name == "Skills" and skills:
                lines.append("")
                lines.append("Skills")
                lines.extend(skills)
                continue

            if section_name == "Education" and education:
                lines.append("")
                lines.append("Education")
                for item in education:
                    top_line = item.institution if not item.location else f"{item.institution} {item.location}"
                    lines.append(top_line.strip())
                    lower_line = item.degree if not item.date else f"{item.degree} {item.date}".strip()
                    if lower_line:
                        lines.append(lower_line)
                continue

            if section_name == "Certifications" and certifications:
                lines.append("")
                lines.append("Certifications")
                lines.extend(certifications)

        return lines

    def _build_reference_latex(
        self,
        name: str,
        contact_lines: list[str],
        summary: str,
        experience_entries: list[ExperienceEntry],
        projects: list[ProjectEntry],
        skills: list[str],
        education: list[EducationEntry],
        certifications: list[str],
        section_order: list[str],
    ) -> str:
        heading_links = self._format_contact_links(contact_lines)
        summary_block = ""
        if summary:
            summary_block = (
                "%-----------SUMMARY-----------\n"
                "\\resumeSection{Summary}\n"
                "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
                f"  \\small{{\\item{{{self._latex_escape(summary)}}}}}\n"
                "\\end{itemize}\n\n"
            )

        content_blocks = self._build_ordered_latex_blocks(
            summary=summary,
            experience_entries=experience_entries,
            projects=projects,
            skills=skills,
            education=education,
            certifications=certifications,
            section_order=section_order,
        )

        return (
            "%-------------------------\n"
            "% Resume in Latex\n"
            "% Author : Jake Gutierrez\n"
            "% Based off of: https://github.com/sb2nov/resume\n"
            "% License : MIT\n"
            "%------------------------\n\n"
            "\\documentclass[letterpaper,11pt]{article}\n\n"
            "\\usepackage{latexsym}\n"
            "\\usepackage[empty]{fullpage}\n"
            "\\usepackage{titlesec}\n"
            "\\usepackage{marvosym}\n"
            "\\usepackage[usenames,dvipsnames]{color}\n"
            "\\usepackage{verbatim}\n"
            "\\usepackage{array}\n"
            "\\usepackage{enumitem}\n"
            "\\usepackage[hidelinks]{hyperref}\n"
            "\\usepackage{fancyhdr}\n"
            "\\usepackage[english]{babel}\n"
            "\\usepackage{tabularx}\n"
            "\\input{glyphtounicode}\n\n"
            "\\pagestyle{fancy}\n"
            "\\fancyhf{}\n"
            "\\fancyfoot{}\n"
            "\\renewcommand{\\headrulewidth}{0pt}\n"
            "\\renewcommand{\\footrulewidth}{0pt}\n\n"
            "\\addtolength{\\oddsidemargin}{-0.5in}\n"
            "\\addtolength{\\evensidemargin}{-0.5in}\n"
            "\\addtolength{\\textwidth}{1in}\n"
            "\\addtolength{\\topmargin}{-.5in}\n"
            "\\addtolength{\\textheight}{1.0in}\n\n"
            "\\urlstyle{same}\n"
            "\\raggedbottom\n"
            "\\raggedright\n"
            "\\setlength{\\tabcolsep}{0in}\n\n"
            "\\titleformat{\\section}{\n"
            "  \\vspace{-4pt}\\scshape\\raggedright\\large\n"
            "}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]\n\n"
            "\\pdfgentounicode=1\n\n"
            "\\newcolumntype{Y}{>{\\raggedright\\arraybackslash}X}\n\n"
            "\\newcommand{\\resumeItem}[1]{\n"
            "  \\item\\small{\n"
            "    {#1 \\vspace{-2pt}}\n"
            "  }\n"
            "}\n\n"
            "\\newcommand{\\resumeSubheading}[4]{\n"
            "  \\vspace{-2pt}\\item\n"
            "    \\begin{tabularx}{0.97\\textwidth}[t]{@{}Y r@{}}\n"
            "      \\textbf{#1} & #2 \\\\\n"
            "      \\textit{\\small#3} & \\textit{\\small #4} \\\\\n"
            "    \\end{tabularx}\\vspace{-7pt}\n"
            "}\n\n"
            "\\newcommand{\\resumeSubSubheading}[2]{\n"
            "    \\item\n"
            "    \\begin{tabularx}{0.97\\textwidth}{@{}Y r@{}}\n"
            "      \\textit{\\small#1} & \\textit{\\small #2} \\\\\n"
            "    \\end{tabularx}\\vspace{-7pt}\n"
            "}\n\n"
            "\\newcommand{\\resumeProjectHeading}[2]{\n"
            "    \\item\n"
            "    \\begin{tabularx}{0.97\\textwidth}{@{}Y r@{}}\n"
            "      \\small#1 & #2 \\\\\n"
            "    \\end{tabularx}\\vspace{-7pt}\n"
            "}\n\n"
            "\\newcommand{\\resumeSubItem}[1]{\\resumeItem{#1}\\vspace{-4pt}}\n\n"
            "\\renewcommand\\labelitemii{$\\vcenter{\\hbox{\\tiny$\\bullet$}}$}\n\n"
            "\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0.15in, label={}]}\n"
            "\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}\n"
            "\\newcommand{\\resumeItemListStart}{\\begin{itemize}}\n"
            "\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{-5pt}}\n\n"
            "%-------------------------------------------\n"
            "\\begin{document}\n\n"
            "%----------HEADING----------\n"
            "\\begin{center}\n"
            f"    \\textbf{{\\Huge \\scshape {self._latex_escape(name)}}} \\\\ \\vspace{{1pt}}\n"
            f"    \\small {heading_links}\n"
            "\\end{center}\n\n"
            f"{content_blocks}"
            "\\end{document}\n"
        )

    def _build_ordered_latex_blocks(
        self,
        summary: str,
        experience_entries: list[ExperienceEntry],
        projects: list[ProjectEntry],
        skills: list[str],
        education: list[EducationEntry],
        certifications: list[str],
        section_order: list[str],
    ) -> str:
        blocks: list[str] = []
        ordered_sections = section_order or ["Experience", "Projects", "Skills", "Education", "Certifications"]
        for section_name in ordered_sections:
            if section_name == "Summary" and summary:
                blocks.append(
                    "%-----------SUMMARY-----------\n"
                    "\\section{Summary}\n"
                    "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
                    f"  \\small{{\\item{{{self._latex_escape(summary)}}}}}\n"
                    "\\end{itemize}\n\n"
                )
            elif section_name == "Education" and education:
                blocks.append(self._build_education_block(education))
            elif section_name == "Experience" and experience_entries:
                blocks.append(self._build_experience_block(experience_entries))
            elif section_name == "Projects" and projects:
                blocks.append(self._build_projects_block(projects))
            elif section_name == "Skills" and skills:
                blocks.append(self._build_skills_block(skills))
            elif section_name == "Certifications" and certifications:
                blocks.append(self._build_certifications_block(certifications))

        return "".join(blocks)

    def _build_experience_block(self, entries: list[ExperienceEntry]) -> str:
        if not entries:
            return ""

        parts = ["%-----------EXPERIENCE-----------\n", "\\section{Experience}\n", "  \\resumeSubHeadingListStart\n\n"]
        for entry in entries:
            parts.append("    \\resumeSubheading\n")
            parts.append(
                f"      {{{self._latex_escape(entry.title)}}}{{{self._latex_escape(entry.date)}}}\n"
            )
            parts.append(
                f"      {{{self._latex_escape(entry.organization)}}}{{{self._latex_escape(entry.location)}}}\n"
            )
            if entry.bullets:
                parts.append("      \\resumeItemListStart\n")
                for bullet in entry.bullets:
                    parts.append(f"        \\resumeItem{{{self._latex_escape(bullet)}}}\n")
                parts.append("      \\resumeItemListEnd\n")
            parts.append("\n")
        parts.append("  \\resumeSubHeadingListEnd\n\n")
        return "".join(parts)

    def _build_projects_block(self, entries: list[ProjectEntry]) -> str:
        if not entries:
            return ""

        parts = ["%-----------PROJECTS-----------\n", "\\section{Projects}\n", "  \\resumeSubHeadingListStart\n\n"]
        for entry in entries:
            left = f"\\textbf{{{self._latex_escape(entry.title)}}}"
            if entry.tech_stack:
                left = f"{left} $|$ \\emph{{{self._latex_escape(entry.tech_stack)}}}"
            parts.append("    \\resumeProjectHeading\n")
            parts.append(f"      {{{left}}}{{{self._latex_escape(entry.date)}}}\n")
            if entry.bullets:
                parts.append("      \\resumeItemListStart\n")
                for bullet in entry.bullets:
                    parts.append(f"        \\resumeItem{{{self._latex_escape(bullet)}}}\n")
                parts.append("      \\resumeItemListEnd\n")
            parts.append("\n")
        parts.append("  \\resumeSubHeadingListEnd\n\n")
        return "".join(parts)

    def _build_skills_block(self, skill_lines: list[str]) -> str:
        if not skill_lines:
            return ""

        formatted_lines = []
        for line in skill_lines:
            if ":" in line:
                label, values = line.split(":", 1)
                formatted_lines.append(
                    f"    \\textbf{{{self._latex_escape(label.strip())}}}{{: {self._latex_escape(values.strip())}}} \\\\"
                )
            else:
                formatted_lines.append(f"    {self._latex_escape(line)} \\\\")

        joined = "\n".join(formatted_lines).rstrip("\\")
        return (
            "%-----------SKILLS-----------\n"
            "\\section{Skills}\n"
            "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
            f"  \\small{{\\item{{\n{joined}\n  }}}}\n"
            "\\end{itemize}\n\n"
        )

    def _build_education_block(self, entries: list[EducationEntry]) -> str:
        if not entries:
            return ""

        parts = ["%-----------EDUCATION-----------\n", "\\section{Education}\n", "  \\resumeSubHeadingListStart\n"]
        for entry in entries:
            parts.append("    \\resumeSubheading\n")
            parts.append(
                f"      {{{self._latex_escape(entry.institution)}}}{{{self._latex_escape(entry.location)}}}\n"
            )
            parts.append(
                f"      {{{self._latex_escape(entry.degree)}}}{{{self._latex_escape(entry.date)}}}\n"
            )
        parts.append("  \\resumeSubHeadingListEnd\n\n")
        return "".join(parts)

    def _build_certifications_block(self, certifications: list[str]) -> str:
        if not certifications:
            return ""

        formatted_lines = []
        for line in certifications:
            if ":" in line:
                label, values = line.split(":", 1)
                formatted_lines.append(
                    f"    \\textbf{{{self._latex_escape(label.strip())}}}{{: {self._latex_escape(values.strip())}}} \\\\"
                )
            else:
                formatted_lines.append(f"    {self._latex_escape(line)} \\\\")

        joined = "\n".join(formatted_lines).rstrip("\\")
        return (
            "%-----------CERTIFICATIONS-----------\n"
            "\\section{Certifications}\n"
            "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
            f"  \\small{{\\item{{\n{joined}\n  }}}}\n"
            "\\end{itemize}\n\n"
        )

    def _format_contact_links(self, contact_lines: list[str]) -> str:
        tokens: list[str] = []
        for line in contact_lines:
            pieces = [piece.strip() for piece in line.split("|") if piece.strip()]
            tokens.extend(pieces if pieces else [line.strip()])

        formatted: list[str] = []
        for token in tokens:
            if "@" in token:
                safe = self._latex_escape(token)
                formatted.append(f"\\href{{mailto:{safe}}}{{\\underline{{{safe}}}}}")
                continue
            if "linkedin.com" in token or "github.com" in token or token.startswith("http"):
                url = token if token.startswith("http") else f"https://{token}"
                formatted.append(
                    f"\\href{{{self._latex_escape(url)}}}{{\\underline{{{self._latex_escape(token)}}}}}"
                )
                continue
            formatted.append(self._latex_escape(token))

        return " $|$ ".join(formatted) or "Phone $|$ Email $|$ LinkedIn $|$ GitHub"

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
