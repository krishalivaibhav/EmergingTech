const scanCvButton = document.getElementById("scan-cv-btn");
const analyzeButton = document.getElementById("analyze-btn");
const toggleJobToolsButton = document.getElementById("toggle-job-tools-btn");
const useRoleTemplateButton = document.getElementById("use-role-template-btn");
const analysisForm = document.getElementById("analysis-form");

const statusMessage = document.getElementById("status-message");
const roleStatusMessage = document.getElementById("role-status-message");
const roleProfileSummary = document.getElementById("role-profile-summary");
const roleTags = document.getElementById("role-tags");

const fileInput = document.getElementById("resume_file");
const resumeTextInput = document.getElementById("resume_text");
const targetRoleSelect = document.getElementById("target_role");
const jobDescriptionInput = document.getElementById("job_description");
const jobToolsSection = document.getElementById("job-tools-section");

const resultsSection = document.getElementById("results-section");
const snapshotGrid = document.getElementById("snapshot-grid");
const resumeSnapshotCard = document.getElementById("resume-snapshot-card");
const jobSnapshotCard = document.getElementById("job-snapshot-card");
const resumeSourceBadge = document.getElementById("resume-source-badge");
const resumePreview = document.getElementById("resume-preview");
const jobDescriptionPreview = document.getElementById("job-description-preview");
const jobTargetRole = document.getElementById("job-target-role");

const scoreLabel = document.getElementById("score-label");
const scoreValue = document.getElementById("score-value");
const scoreSubtitle = document.getElementById("score-subtitle");
const scoreBadge = document.getElementById("score-badge");

const cvProfileSummary = document.getElementById("cv-profile-summary");
const cvCurrentStatus = document.getElementById("cv-current-status");
const recommendedRolesList = document.getElementById("recommended-roles-list");

const listATitle = document.getElementById("list-a-title");
const listBTitle = document.getElementById("list-b-title");
const matchingSkillsList = document.getElementById("matching-skills-list");
const missingSkillsList = document.getElementById("missing-skills-list");
const resumeSummary = document.getElementById("resume-summary");
const atsSuggestionsList = document.getElementById("ats-suggestions-list");
const improvedBulletsList = document.getElementById("improved-bullets-list");
const interviewQuestionsList = document.getElementById("interview-questions-list");
const tailorSummary = document.getElementById("tailor-summary");
const tailorBulletsList = document.getElementById("tailor-bullets-list");
const tailorSkillsList = document.getElementById("tailor-skills-list");

let suggestedRoles = [];

function setStatus(message, isError = false) {
  statusMessage.textContent = message || "";
  statusMessage.classList.toggle("error", isError);
}

function setRoleStatus(message, isError = false) {
  roleStatusMessage.textContent = message || "";
  roleStatusMessage.classList.toggle("error", isError);
}

function getScoreLabel(score) {
  if (score >= 80) {
    return { label: "Strong Fit", className: "score-high" };
  }
  if (score >= 60) {
    return { label: "Moderate Fit", className: "score-mid" };
  }
  return { label: "Needs Work", className: "score-low" };
}

function buildEmptyState(text) {
  const item = document.createElement("li");
  item.className = "empty-state";
  item.textContent = text;
  return item;
}

function renderList(listEl, items, emptyText) {
  listEl.innerHTML = "";
  if (!Array.isArray(items) || items.length === 0) {
    listEl.appendChild(buildEmptyState(emptyText));
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = String(item);
    listEl.appendChild(li);
  });
}

function clipText(text, maxChars = 2200) {
  if (!text) {
    return "";
  }
  if (text.length <= maxChars) {
    return text;
  }
  return `${text.slice(0, maxChars)}\n\n... (truncated for display)`;
}

function setRoleOptions(roles) {
  const currentSelection = targetRoleSelect.value;
  targetRoleSelect.innerHTML = '<option value="">Select a suggested role...</option>';

  roles.forEach((role) => {
    const option = document.createElement("option");
    option.value = role;
    option.textContent = role;
    targetRoleSelect.appendChild(option);
  });

  if (roles.includes(currentSelection)) {
    targetRoleSelect.value = currentSelection;
  }
}

function renderRoleChips(roles, selectedRole = "") {
  roleTags.innerHTML = "";
  roles.forEach((role) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `role-chip${selectedRole === role ? " active" : ""}`;
    chip.textContent = role;
    chip.addEventListener("click", () => {
      targetRoleSelect.value = role;
      renderRoleChips(suggestedRoles, role);
      setStatus(`Selected role: ${role}`);
    });
    roleTags.appendChild(chip);
  });
}

function buildRoleTemplate(role) {
  return [
    `Role Title: ${role}`,
    "",
    "Responsibilities:",
    "- Build and deliver production-quality features for this role scope.",
    "- Collaborate with cross-functional stakeholders to ship measurable outcomes.",
    "- Maintain quality through testing, documentation, and iterative improvement.",
    "",
    "Required Skills:",
    "- Role-relevant technical foundations and problem-solving.",
    "- Strong communication and execution ownership.",
    "",
    "Preferred:",
    "- Experience with modern tooling, deployment, and team collaboration.",
  ].join("\n");
}

function resetResults() {
  scoreLabel.textContent = "CV Score";
  scoreValue.textContent = "0";
  scoreSubtitle.textContent = "ATS readiness out of 100";
  scoreBadge.textContent = "Needs Work";
  scoreBadge.classList.remove("score-high", "score-mid");
  scoreBadge.classList.add("score-low");

  listATitle.textContent = "Top Strengths";
  listBTitle.textContent = "Improvement Areas";

  cvProfileSummary.textContent = "";
  cvCurrentStatus.textContent = "";
  recommendedRolesList.innerHTML = "";

  resumeSourceBadge.textContent = "";
  resumePreview.textContent = "";
  jobDescriptionPreview.textContent = "";
  jobTargetRole.textContent = "";

  resumeSnapshotCard.classList.remove("hidden");
  jobSnapshotCard.classList.add("hidden");
  snapshotGrid.classList.add("single-column");
}

function renderInputPreview(context) {
  const { resumeText, hasFile, fileName, selectedRole, jobDescription, showJobSnapshot } = context;

  if (resumeText) {
    resumeSourceBadge.textContent = "Source: resume text";
    resumePreview.textContent = clipText(resumeText);
  } else if (hasFile) {
    resumeSourceBadge.textContent = `Source: uploaded PDF (${fileName || "resume.pdf"})`;
    resumePreview.textContent =
      "The uploaded PDF was analyzed on the server. Resume preview is not shown because this flow now uses upload-only input.";
  } else {
    resumeSourceBadge.textContent = "Source: not provided";
    resumePreview.textContent = "No resume content provided.";
  }

  if (!showJobSnapshot) {
    jobSnapshotCard.classList.add("hidden");
    snapshotGrid.classList.add("single-column");
    return;
  }

  jobSnapshotCard.classList.remove("hidden");
  snapshotGrid.classList.remove("single-column");
  jobTargetRole.textContent = selectedRole ? `Selected Role: ${selectedRole}` : "Selected Role: Not set";

  if (jobDescription) {
    jobDescriptionPreview.textContent = clipText(jobDescription);
    return;
  }

  if (selectedRole) {
    jobDescriptionPreview.textContent = `No JD text pasted. Analysis used role benchmark for "${selectedRole}".`;
    return;
  }

  jobDescriptionPreview.textContent = "No job description provided.";
}

function renderAnalysisCards(result, context) {
  const score = Number.isFinite(result.match_score) ? result.match_score : Number(result.match_score || 0);
  const scoreMeta = getScoreLabel(score);

  renderInputPreview(context);
  scoreValue.textContent = String(score);
  scoreBadge.textContent = scoreMeta.label;
  scoreBadge.classList.remove("score-high", "score-mid", "score-low");
  scoreBadge.classList.add(scoreMeta.className);

  renderList(matchingSkillsList, result.matching_skills, "No items available.");
  renderList(missingSkillsList, result.missing_skills, "No items available.");

  resumeSummary.textContent = result.resume_summary || "No summary was generated.";
  renderList(atsSuggestionsList, result.ats_suggestions, "No ATS suggestions available.");
  renderList(improvedBulletsList, result.improved_bullets, "No rewritten bullet points generated.");
  renderList(interviewQuestionsList, result.interview_questions, "No interview questions were generated.");

  const tailor = result.tailor_my_resume || {};
  tailorSummary.textContent = tailor.improved_professional_summary || "No professional summary recommendation available.";
  renderList(tailorBulletsList, tailor.stronger_project_bullets, "No stronger project bullets generated.");
  renderList(tailorSkillsList, tailor.suggested_skills_keywords, "No extra skills keywords suggested.");

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function buildResumeFormData() {
  const resumeText = resumeTextInput ? resumeTextInput.value.trim() : "";
  const hasFile = fileInput.files.length > 0;
  const formData = new FormData();

  if (resumeText) {
    formData.append("resume_text", resumeText);
  }
  if (hasFile) {
    formData.append("resume_file", fileInput.files[0]);
  }

  return {
    formData,
    resumeText,
    hasFile,
    fileName: hasFile ? fileInput.files[0].name : "",
  };
}

function ensureResumeInput(resumeText, hasFile) {
  if (!resumeText && !hasFile) {
    setStatus("Upload a PDF resume first.", true);
    return false;
  }
  return true;
}

function renderCvScanResult(data, context) {
  scoreLabel.textContent = "CV Score";
  scoreSubtitle.textContent = "ATS readiness out of 100";
  listATitle.textContent = "Top Strengths";
  listBTitle.textContent = "Improvement Areas";

  renderAnalysisCards(
    {
      match_score: data.cv_score,
      matching_skills: data.top_strengths,
      missing_skills: data.improvement_areas,
      resume_summary: data.resume_summary,
      ats_suggestions: data.ats_suggestions,
      improved_bullets: data.improved_bullets,
      interview_questions: [],
      tailor_my_resume: {
        improved_professional_summary: data.profile_summary,
        stronger_project_bullets: data.improved_bullets,
        suggested_skills_keywords: data.recommended_roles,
      },
    },
    { ...context, showJobSnapshot: false, selectedRole: "", jobDescription: "" }
  );

  cvProfileSummary.textContent = data.profile_summary || "No profile summary generated.";
  cvCurrentStatus.textContent = data.current_status ? `Current status: ${data.current_status}` : "";
  renderList(recommendedRolesList, data.recommended_roles, "No role suggestions available.");

  suggestedRoles = Array.isArray(data.recommended_roles) ? data.recommended_roles : [];
  setRoleOptions(suggestedRoles);
  renderRoleChips(suggestedRoles, targetRoleSelect.value);

  roleProfileSummary.textContent = data.profile_summary || "";
  roleProfileSummary.classList.toggle("hidden", !data.profile_summary);
  setRoleStatus(
    suggestedRoles.length
      ? `CV scan complete. Suggested ${suggestedRoles.length} role options.`
      : "CV scan complete, but no role suggestions were found.",
    suggestedRoles.length === 0
  );
}

async function scanCv() {
  setStatus("");
  const { formData, resumeText, hasFile, fileName } = buildResumeFormData();
  if (!ensureResumeInput(resumeText, hasFile)) {
    return;
  }

  scanCvButton.disabled = true;
  scanCvButton.textContent = "Scanning...";
  setStatus("Scanning CV and generating role recommendations...");

  try {
    const response = await fetch("/api/scan-cv", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to scan CV right now.");
    }

    renderCvScanResult(data, { resumeText, hasFile, fileName });
    setStatus("CV scan complete.");
  } catch (error) {
    setStatus(error.message || "Unexpected error while scanning CV.", true);
  } finally {
    scanCvButton.disabled = false;
    scanCvButton.textContent = "Scan CV";
  }
}

async function analyzeSelectedRole() {
  setStatus("");
  const { formData, resumeText, hasFile, fileName } = buildResumeFormData();
  if (!ensureResumeInput(resumeText, hasFile)) {
    return;
  }

  const selectedRole = targetRoleSelect.value.trim();
  const jobDescription = jobDescriptionInput.value.trim();
  formData.append("target_role", selectedRole);
  formData.append("job_description", jobDescription);

  if (!selectedRole && !jobDescription) {
    setStatus("Select a role or paste a job description before running role analysis.", true);
    return;
  }

  scoreLabel.textContent = "Match Score";
  scoreSubtitle.textContent = "Role fit out of 100";
  listATitle.textContent = "Matching Skills";
  listBTitle.textContent = "Missing Skills";

  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing...";
  setStatus("Running role-specific match analysis...");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to analyze right now.");
    }

    renderAnalysisCards(data, {
      resumeText,
      hasFile,
      fileName,
      selectedRole,
      jobDescription,
      showJobSnapshot: true,
    });

    cvProfileSummary.textContent = selectedRole
      ? `Role-targeted analysis completed for ${selectedRole}.`
      : "Role-targeted analysis completed.";
    cvCurrentStatus.textContent = selectedRole ? `Target role: ${selectedRole}` : "";
    if (suggestedRoles.length > 0) {
      renderList(recommendedRolesList, suggestedRoles, "No role suggestions available.");
    } else if (selectedRole) {
      renderList(recommendedRolesList, [selectedRole], "No role suggestions available.");
    }

    setStatus("Role analysis complete.");
  } catch (error) {
    resetResults();
    resultsSection.classList.add("hidden");
    setStatus(error.message || "Unexpected error. Please try again.", true);
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze Selected Role";
  }
}

scanCvButton.addEventListener("click", scanCv);

toggleJobToolsButton.addEventListener("click", () => {
  const shouldShow = jobToolsSection.classList.contains("hidden");
  jobToolsSection.classList.toggle("hidden", !shouldShow);
  toggleJobToolsButton.textContent = shouldShow ? "Hide Job Match Tools" : "Show Job Match Tools";
});

targetRoleSelect.addEventListener("change", () => {
  renderRoleChips(suggestedRoles, targetRoleSelect.value);
});

useRoleTemplateButton.addEventListener("click", () => {
  const selectedRole = targetRoleSelect.value.trim();
  if (!selectedRole) {
    setStatus("Select a suggested role before using the template.", true);
    return;
  }

  if (!jobDescriptionInput.value.trim()) {
    jobDescriptionInput.value = buildRoleTemplate(selectedRole);
  } else if (!jobDescriptionInput.value.toLowerCase().includes(selectedRole.toLowerCase())) {
    jobDescriptionInput.value = `Role Focus: ${selectedRole}\n\n${jobDescriptionInput.value}`;
  }

  setStatus(`Applied role context for ${selectedRole}.`);
});

if (resumeTextInput) {
  resumeTextInput.addEventListener("input", () => {
    if (suggestedRoles.length > 0) {
      setRoleStatus("Resume text changed. Re-run CV scan for updated role suggestions.");
    }
  });
}

fileInput.addEventListener("change", () => {
  if (suggestedRoles.length > 0) {
    setRoleStatus("Resume file changed. Re-run CV scan for updated role suggestions.");
  }
});

analyzeButton.addEventListener("click", analyzeSelectedRole);

analysisForm.addEventListener("submit", (event) => {
  event.preventDefault();
});
// error states
// loading states
// error states
// loading states
// error states
// loading states
