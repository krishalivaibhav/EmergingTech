const scanCvButton = document.getElementById("scan-cv-btn");
const analyzeButton = document.getElementById("analyze-btn");
const toggleJobToolsButton = document.getElementById("toggle-job-tools-btn");
const useRoleTemplateButton = document.getElementById("use-role-template-btn");
const analysisForm = document.getElementById("analysis-form");

const statusMessage = document.getElementById("status-message");
const loadingIndicator = document.getElementById("loading-indicator");
const loadingText = document.getElementById("loading-text");
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
const liveJobsCard = document.getElementById("live-jobs-card");
const liveJobsNote = document.getElementById("live-jobs-note");
const liveJobsQuery = document.getElementById("live-jobs-query");
const liveJobsSourceLink = document.getElementById("live-jobs-source-link");
const liveJobsError = document.getElementById("live-jobs-error");
const liveJobsList = document.getElementById("live-jobs-list");
const jobSearchLocationInput = document.getElementById("job-search-location");
const useMyLocationButton = document.getElementById("use-my-location-btn");
const searchLocationJobsButton = document.getElementById("search-location-jobs-btn");
const loadMoreJobsButton = document.getElementById("load-more-jobs-btn");
const upgradeCard = document.getElementById("upgrade-card");
const generateUpgradeButton = document.getElementById("generate-upgrade-btn");
const downloadPdfButton = document.getElementById("download-pdf-btn");
const downloadLatexButton = document.getElementById("download-latex-btn");
const openOverleafButton = document.getElementById("open-overleaf-btn");
const copyLatexButton = document.getElementById("copy-latex-btn");
const upgradeStatusMessage = document.getElementById("upgrade-status-message");
const upgradePreviewStatus = document.getElementById("upgrade-preview-status");
const upgradeResults = document.getElementById("upgrade-results");
const upgradeScoreBefore = document.getElementById("upgrade-score-before");
const upgradeScoreAfter = document.getElementById("upgrade-score-after");
const upgradeSummary = document.getElementById("upgrade-summary");
const upgradeImprovementsList = document.getElementById("upgrade-improvements-list");
const upgradeOriginalPreview = document.getElementById("upgrade-original-preview");
const upgradeUpdatedPreview = document.getElementById("upgrade-updated-preview");
const upgradeLatexOutput = document.getElementById("upgrade-latex-output");
const upgradeLatexNotesList = document.getElementById("upgrade-latex-notes-list");

let suggestedRoles = [];
let loadingMessageTimer = null;
let activeLoadingButton = null;
let latestLatexResume = "";
let latestCompiledPdfUrl = "";
let latestCompiledPreviewUrl = "";
let roleAnalysisReady = false;
let latestCvScanScore = null;
let uploadedResumeFileUrl = "";
let uploadedResumePreviewUrl = "";
let renderedLiveJobKeys = new Set();
let liveJobsSearchState = {
  targetRole: "",
  locationQuery: "",
  latitude: null,
  longitude: null,
  page: 1,
  hasMore: false,
};

function setStatus(message, isError = false) {
  statusMessage.textContent = message || "";
  statusMessage.classList.toggle("error", isError);
}

function setRoleStatus(message, isError = false) {
  roleStatusMessage.textContent = message || "";
  roleStatusMessage.classList.toggle("error", isError);
}

function setUpgradeStatus(message, isError = false) {
  upgradeStatusMessage.textContent = message || "";
  upgradeStatusMessage.classList.toggle("error", isError);
}

function setUpgradePreviewStatus(message, isError = false) {
  upgradePreviewStatus.textContent = message || "";
  upgradePreviewStatus.classList.toggle("error", isError);
}

function releaseUploadedResumePreview() {
  if (uploadedResumeFileUrl) {
    window.URL.revokeObjectURL(uploadedResumeFileUrl);
    uploadedResumeFileUrl = "";
  }
  if (uploadedResumePreviewUrl) {
    window.URL.revokeObjectURL(uploadedResumePreviewUrl);
    uploadedResumePreviewUrl = "";
  }
}

function releaseCompiledPdfPreview() {
  releaseCompiledDownloadPdf();
  releaseCompiledPreviewImage();
}

function releaseCompiledDownloadPdf() {
  if (latestCompiledPdfUrl) {
    window.URL.revokeObjectURL(latestCompiledPdfUrl);
    latestCompiledPdfUrl = "";
  }
}

function releaseCompiledPreviewImage() {
  if (latestCompiledPreviewUrl) {
    window.URL.revokeObjectURL(latestCompiledPreviewUrl);
    latestCompiledPreviewUrl = "";
  }
}

function buildPdfPreviewUrl(url) {
  if (!url) {
    return "";
  }
  return `${url}#page=1&toolbar=0&navpanes=0&scrollbar=0&zoom=page-width`;
}

function formatPublishedDate(value) {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(parsed);
}

function buildLiveJobKey(job) {
  return (
    String(job.application_link || "").trim().toLowerCase() ||
    `${String(job.title || "").trim().toLowerCase()}::${String(job.company_name || "")
      .trim()
      .toLowerCase()}`
  );
}

function setLiveJobsSearchState(nextState = {}) {
  liveJobsSearchState = {
    ...liveJobsSearchState,
    ...nextState,
  };
}

function updateLoadMoreJobsButton(hasMore, query) {
  if (!loadMoreJobsButton) {
    return;
  }

  const shouldShow = Boolean(query) && Boolean(hasMore);
  loadMoreJobsButton.classList.toggle("hidden", !shouldShow);
  loadMoreJobsButton.disabled = !shouldShow;
}

function startLoading(messages) {
  if (!loadingIndicator || !loadingText) {
    return;
  }

  const steps = Array.isArray(messages) && messages.length > 0 ? messages : ["Working..."];
  let currentIndex = 0;

  if (loadingMessageTimer) {
    window.clearInterval(loadingMessageTimer);
  }

  loadingText.textContent = steps[0];
  loadingIndicator.removeAttribute("hidden");
  analysisForm.setAttribute("aria-busy", "true");

  if (steps.length === 1) {
    loadingMessageTimer = null;
    return;
  }

  loadingMessageTimer = window.setInterval(() => {
    if (currentIndex >= steps.length - 1) {
      window.clearInterval(loadingMessageTimer);
      loadingMessageTimer = null;
      return;
    }

    currentIndex += 1;
    loadingText.textContent = steps[currentIndex];
  }, 1500);
}

function stopLoading() {
  if (!loadingIndicator || !loadingText) {
    return;
  }

  if (loadingMessageTimer) {
    window.clearInterval(loadingMessageTimer);
    loadingMessageTimer = null;
  }

  loadingIndicator.setAttribute("hidden", "");
  analysisForm.setAttribute("aria-busy", "false");
}

function setButtonLoading(button, isLoading, idleLabel, loadingLabel) {
  if (!button) {
    return;
  }

  if (isLoading) {
    activeLoadingButton = button;
    button.disabled = true;
    button.classList.add("is-loading");
    button.textContent = loadingLabel;
    return;
  }

  button.disabled = false;
  button.classList.remove("is-loading");
  button.textContent = idleLabel;

  if (activeLoadingButton === button) {
    activeLoadingButton = null;
  }
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

function slugify(value) {
  return String(value || "resume")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "resume";
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
      roleAnalysisReady = false;
      upgradeCard.classList.add("hidden");
      resetUpgradeResults();
      updateUpgradeAvailability();
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
  liveJobsCard.classList.add("hidden");
  liveJobsList.innerHTML = "";
  liveJobsNote.textContent = "";
  liveJobsQuery.textContent = "";
  liveJobsError.textContent = "";
  if (jobSearchLocationInput) {
    jobSearchLocationInput.value = "";
  }
  liveJobsSourceLink.classList.add("hidden");
  liveJobsSourceLink.removeAttribute("href");
  renderedLiveJobKeys = new Set();
  setLiveJobsSearchState({
    targetRole: "",
    locationQuery: "",
    latitude: null,
    longitude: null,
    page: 1,
    hasMore: false,
  });
  updateLoadMoreJobsButton(false, "");

  resumeSnapshotCard.classList.remove("hidden");
  jobSnapshotCard.classList.add("hidden");
  snapshotGrid.classList.add("single-column");
  latestCvScanScore = null;
  roleAnalysisReady = false;
  upgradeCard.classList.add("hidden");
  resetUpgradeResults();
}

function resetUpgradeResults() {
  latestLatexResume = "";
  releaseCompiledPdfPreview();
  upgradeScoreBefore.textContent = "0";
  upgradeScoreAfter.textContent = "0";
  upgradeSummary.textContent = "";
  upgradeOriginalPreview.classList.remove("pdf-preview-shell");
  upgradeUpdatedPreview.classList.remove("pdf-preview-shell");
  upgradeOriginalPreview.innerHTML = "";
  upgradeUpdatedPreview.innerHTML = "";
  upgradeLatexOutput.textContent = "";
  upgradeImprovementsList.innerHTML = "";
  upgradeLatexNotesList.innerHTML = "";
  upgradeResults.classList.add("hidden");
  downloadPdfButton.classList.add("hidden");
  downloadLatexButton.classList.add("hidden");
  openOverleafButton.classList.add("hidden");
  copyLatexButton.classList.add("hidden");
  setUpgradePreviewStatus("");
}

function isSectionHeading(line) {
  const normalized = String(line || "").trim();
  if (!normalized) {
    return false;
  }

  const normalizedKey = normalized.toLowerCase().replace(/[:\s]+$/g, "");
  const knownHeadings = new Set([
    "summary",
    "professional summary",
    "technical skills",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "achievements",
    "leadership",
    "activities",
  ]);

  return knownHeadings.has(normalizedKey);
}

function parseResumeSnapshot(snapshotText) {
  const lines = String(snapshotText || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return {
      name: "Resume Preview",
      contact: "",
      sections: [],
    };
  }

  const parsed = {
    name: lines[0],
    contact: "",
    sections: [],
  };

  let index = 1;
  if (
    lines[1] &&
    /[@|]|linkedin|github|phone|\+\d|\d{10}/i.test(lines[1])
  ) {
    parsed.contact = lines[1];
    index = 2;
  }

  let currentSection = null;

  const ensureSection = (title) => {
    currentSection = { title, items: [] };
    parsed.sections.push(currentSection);
  };

  for (; index < lines.length; index += 1) {
    const line = lines[index];
    if (isSectionHeading(line)) {
      ensureSection(line.replace(/:$/, ""));
      continue;
    }

    if (!currentSection) {
      ensureSection("Profile");
    }

    if (/^[-•*]\s+/.test(line)) {
      currentSection.items.push({
        type: "bullet",
        text: line.replace(/^[-•*]\s+/, "").trim(),
      });
      continue;
    }

    const itemType =
      line.includes(":") && line.length <= 140 ? "inline-meta" : "line";

    currentSection.items.push({
      type: itemType,
      text: line,
    });
  }

  return parsed;
}

function renderResumePreview(container, snapshotText) {
  container.innerHTML = "";

  const parsed = parseResumeSnapshot(snapshotText);
  const sheet = document.createElement("article");
  sheet.className = "resume-sheet";

  const header = document.createElement("header");
  header.className = "resume-sheet-header";

  const name = document.createElement("h5");
  name.className = "resume-sheet-name";
  name.textContent = parsed.name || "Resume Preview";
  header.appendChild(name);

  if (parsed.contact) {
    const contact = document.createElement("p");
    contact.className = "resume-sheet-contact";
    contact.textContent = parsed.contact;
    header.appendChild(contact);
  }

  sheet.appendChild(header);

  if (!parsed.sections.length) {
    const empty = document.createElement("p");
    empty.className = "resume-sheet-empty";
    empty.textContent = "No resume preview data available.";
    sheet.appendChild(empty);
    container.appendChild(sheet);
    return;
  }

  parsed.sections.forEach((sectionData) => {
    const section = document.createElement("section");
    section.className = "resume-sheet-section";

    const title = document.createElement("h6");
    title.className = "resume-sheet-section-title";
    title.textContent = sectionData.title;
    section.appendChild(title);

    let bulletList = null;

    const flushBullets = () => {
      if (bulletList) {
        section.appendChild(bulletList);
        bulletList = null;
      }
    };

    sectionData.items.forEach((item) => {
      if (item.type === "bullet") {
        if (!bulletList) {
          bulletList = document.createElement("ul");
          bulletList.className = "resume-sheet-bullets";
        }
        const li = document.createElement("li");
        li.textContent = item.text;
        bulletList.appendChild(li);
        return;
      }

      flushBullets();
      const line = document.createElement("p");
      line.className =
        item.type === "inline-meta" ? "resume-sheet-inline-meta" : "resume-sheet-line";
      line.textContent = item.text;
      section.appendChild(line);
    });

    flushBullets();
    sheet.appendChild(section);
  });

  container.appendChild(sheet);
}

async function renderOriginalResumePreview(snapshotText) {
  if (fileInput.files.length > 0) {
    if (!uploadedResumePreviewUrl) {
      try {
        const formData = new FormData();
        formData.append("resume_file", fileInput.files[0]);
        const response = await fetch("/api/render-pdf-preview", {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.detail || "Unable to render the original resume preview.");
        }
        const previewBlob = await response.blob();
        uploadedResumePreviewUrl = window.URL.createObjectURL(previewBlob);
      } catch (error) {
        uploadedResumePreviewUrl = "";
      }
    }
  }

  if (uploadedResumePreviewUrl) {
    upgradeOriginalPreview.innerHTML = "";
    const previewImage = document.createElement("img");
    previewImage.className = "pdf-preview-image";
    previewImage.src = uploadedResumePreviewUrl;
    previewImage.alt = "Uploaded original resume preview";
    previewImage.loading = "lazy";
    upgradeOriginalPreview.classList.add("pdf-preview-shell");
    upgradeOriginalPreview.appendChild(previewImage);
    return;
  }

  if (uploadedResumeFileUrl) {
    upgradeOriginalPreview.innerHTML = "";
    const frame = document.createElement("iframe");
    frame.className = "pdf-preview-object";
    frame.src = buildPdfPreviewUrl(uploadedResumeFileUrl);
    frame.title = "Uploaded original resume PDF preview";
    frame.loading = "lazy";
    upgradeOriginalPreview.classList.add("pdf-preview-shell");
    upgradeOriginalPreview.appendChild(frame);
    return;
  }

  upgradeOriginalPreview.classList.remove("pdf-preview-shell");
  renderResumePreview(upgradeOriginalPreview, snapshotText);
}

async function compileResumePreview(latexSource, selectedRole) {
  if (!latexSource) {
    setUpgradePreviewStatus("No LaTeX source available for PDF compilation.", true);
    return;
  }

  setUpgradePreviewStatus("Rendering updated resume preview...");
  upgradeUpdatedPreview.classList.remove("pdf-preview-shell");

  try {
    const response = await fetch("/api/compile-latex-preview-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latex_resume: latexSource }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Unable to compile the PDF preview right now.");
    }

    const previewBlob = await response.blob();
    releaseCompiledPreviewImage();
    latestCompiledPreviewUrl = window.URL.createObjectURL(previewBlob);
    upgradeUpdatedPreview.innerHTML = "";
    upgradeUpdatedPreview.classList.add("pdf-preview-shell");

    const previewImage = document.createElement("img");
    previewImage.className = "pdf-preview-image";
    previewImage.src = latestCompiledPreviewUrl;
    previewImage.alt = `Updated resume preview for ${selectedRole || "selected role"}`;
    previewImage.loading = "lazy";
    upgradeUpdatedPreview.appendChild(previewImage);

    downloadPdfButton.classList.remove("hidden");
    setUpgradePreviewStatus("Updated resume preview is ready.");
  } catch (error) {
    downloadPdfButton.classList.add("hidden");
    upgradeUpdatedPreview.classList.remove("pdf-preview-shell");
    setUpgradePreviewStatus(
      `${error.message || "Preview rendering failed."} Showing structured preview instead.`,
      true
    );
  }
}

function updateUpgradeAvailability() {
  const selectedRole = targetRoleSelect.value.trim();
  const isUnlocked = roleAnalysisReady && !!selectedRole;
  generateUpgradeButton.disabled = !isUnlocked;

  if (!roleAnalysisReady) {
    setUpgradeStatus("Run role analysis first to unlock this feature.");
    return;
  }

  if (!selectedRole) {
    setUpgradeStatus("Select a target role in Job Match Tools to unlock this feature.");
    return;
  }

  setUpgradeStatus(`Upgrade is ready to generate for ${selectedRole}.`);
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
  renderLiveJobs(result);

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderLiveJobs(result, options = {}) {
  const { append = false } = options;
  const jobs = Array.isArray(result.live_market_jobs) ? result.live_market_jobs : [];
  const sourceName = result.live_market_jobs_source_name || "";
  const sourceUrl = result.live_market_jobs_source_url || "";
  const query = result.live_market_jobs_query || "";
  const note = result.live_market_jobs_note || "";
  const error = result.live_market_jobs_error || "";
  const resolvedLocationLabel = result.resolved_location_label || "";
  const page = Number(result.live_market_jobs_page || 1);
  const hasMore = Boolean(result.live_market_jobs_has_more);

  if (!query) {
    liveJobsCard.classList.add("hidden");
    liveJobsList.innerHTML = "";
    liveJobsNote.textContent = "";
    liveJobsQuery.textContent = "";
    liveJobsError.textContent = "";
    liveJobsSourceLink.classList.add("hidden");
    liveJobsSourceLink.removeAttribute("href");
    renderedLiveJobKeys = new Set();
    updateLoadMoreJobsButton(false, "");
    return;
  }

  liveJobsCard.classList.remove("hidden");
  liveJobsNote.textContent = note || "Live remote job listings related to the selected role.";
  liveJobsQuery.textContent = resolvedLocationLabel
    ? `Role query: ${query} • Location: ${resolvedLocationLabel}`
    : `Role query: ${query}`;
  if (resolvedLocationLabel && jobSearchLocationInput) {
    jobSearchLocationInput.value = resolvedLocationLabel;
  }
  liveJobsError.textContent = error || "";
  liveJobsError.classList.toggle("error", Boolean(error));
  updateLoadMoreJobsButton(hasMore, query);
  setLiveJobsSearchState({
    page,
    hasMore,
    targetRole: query,
  });

  if (sourceUrl) {
    liveJobsSourceLink.href = sourceUrl;
    liveJobsSourceLink.textContent = sourceName ? `Source: ${sourceName}` : "View Source";
    liveJobsSourceLink.classList.remove("hidden");
  } else {
    liveJobsSourceLink.classList.add("hidden");
  }

  if (!append) {
    liveJobsList.innerHTML = "";
    renderedLiveJobKeys = new Set();
  }

  if (jobs.length === 0) {
    if (!append) {
      const emptyState = document.createElement("p");
      emptyState.className = "body-copy";
      emptyState.textContent = error
        ? "Role analysis completed, but live jobs could not be loaded right now."
        : "No live jobs were found for this role right now.";
      liveJobsList.appendChild(emptyState);
    }
    return;
  }

  jobs.forEach((job) => {
    const key = buildLiveJobKey(job);
    if (!key || renderedLiveJobKeys.has(key)) {
      return;
    }
    renderedLiveJobKeys.add(key);

    const card = document.createElement("article");
    card.className = "live-job-item";

    const title = document.createElement("a");
    title.className = "live-job-title";
    title.href = job.application_link || "#";
    title.target = "_blank";
    title.rel = "noreferrer";
    title.textContent = job.title || "Untitled role";
    card.appendChild(title);

    const company = document.createElement("p");
    company.className = "live-job-company";
    company.textContent = job.company_name || "Unknown company";
    card.appendChild(company);

    const metaBits = [
      job.location_summary,
      job.employment_type,
      job.seniority,
      job.salary_summary,
      formatPublishedDate(job.published_at),
    ].filter(Boolean);

    const meta = document.createElement("p");
    meta.className = "live-job-meta";
    meta.textContent = metaBits.join(" • ");
    card.appendChild(meta);

    const excerpt = document.createElement("p");
    excerpt.className = "live-job-excerpt";
    excerpt.textContent = job.excerpt || "No job summary available.";
    card.appendChild(excerpt);

    const apply = document.createElement("a");
    apply.className = "live-job-apply";
    apply.href = job.application_link || "#";
    apply.target = "_blank";
    apply.rel = "noreferrer";
    apply.textContent = "Open Listing";
    card.appendChild(apply);

    liveJobsList.appendChild(card);
  });
}

function requestBrowserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Browser location access is not available on this device."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => resolve(position),
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          reject(new Error("Location access was denied. Allow location to run nearby job search."));
          return;
        }
        if (error.code === error.POSITION_UNAVAILABLE) {
          reject(new Error("Your location could not be determined right now."));
          return;
        }
        if (error.code === error.TIMEOUT) {
          reject(new Error("Location request timed out. Try again."));
          return;
        }
        reject(new Error("Unable to access your location right now."));
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000,
      }
    );
  });
}

async function findJobsNearMe() {
  const selectedRole = targetRoleSelect.value.trim();
  if (!selectedRole) {
    setStatus("Select a target role before using location-based job search.", true);
    return;
  }

  const confirmed = window.confirm("Your location will be asked for job finding. Continue?");
  if (!confirmed) {
    return;
  }

  setButtonLoading(useMyLocationButton, true, "Use My Location", "Detecting Location...");
  liveJobsError.textContent = "Requesting location access for job finding...";
  liveJobsError.classList.remove("error");

  try {
    const position = await requestBrowserLocation();
    const formData = new FormData();
    formData.append("target_role", selectedRole);
    formData.append("latitude", String(position.coords.latitude));
    formData.append("longitude", String(position.coords.longitude));
    formData.append("page", "1");

    liveJobsError.textContent = "Finding live jobs for your location...";

    const response = await fetch("/api/location-jobs", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to load location-based jobs right now.");
    }

    if (data.resolved_location_label && jobSearchLocationInput) {
      jobSearchLocationInput.value = data.resolved_location_label;
    }
    renderLiveJobs(data);
    setLiveJobsSearchState({
      targetRole: selectedRole,
      locationQuery: data.resolved_location_label || "",
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      page: Number(data.live_market_jobs_page || 1),
      hasMore: Boolean(data.live_market_jobs_has_more),
    });
    if (data.live_market_jobs_error) {
      liveJobsError.textContent = data.live_market_jobs_error;
      liveJobsError.classList.add("error");
      return;
    }

    liveJobsError.textContent = data.resolved_location_label
      ? `Showing live role matches filtered for ${data.resolved_location_label}.`
      : "Showing live jobs filtered using your current location.";
    liveJobsError.classList.remove("error");
  } catch (error) {
    liveJobsError.textContent = error.message || "Unable to load location-based jobs right now.";
    liveJobsError.classList.add("error");
  } finally {
    setButtonLoading(useMyLocationButton, false, "Use My Location", "Detecting Location...");
  }
}

async function searchJobsByLocation() {
  const selectedRole = targetRoleSelect.value.trim();
  if (!selectedRole) {
    setStatus("Select a target role before searching jobs by location.", true);
    return;
  }

  const locationQuery = jobSearchLocationInput ? jobSearchLocationInput.value.trim() : "";
  if (!locationQuery) {
    liveJobsError.textContent = "Enter a city or state before searching location-based jobs.";
    liveJobsError.classList.add("error");
    return;
  }

  setButtonLoading(searchLocationJobsButton, true, "Search Location Jobs", "Searching Jobs...");
  liveJobsError.textContent = `Finding live jobs for ${locationQuery}...`;
  liveJobsError.classList.remove("error");

  try {
    const formData = new FormData();
    formData.append("target_role", selectedRole);
    formData.append("location_query", locationQuery);
    formData.append("page", "1");

    const response = await fetch("/api/location-jobs", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to search jobs for that location right now.");
    }

    renderLiveJobs(data);
    setLiveJobsSearchState({
      targetRole: selectedRole,
      locationQuery: data.resolved_location_label || locationQuery,
      latitude: null,
      longitude: null,
      page: Number(data.live_market_jobs_page || 1),
      hasMore: Boolean(data.live_market_jobs_has_more),
    });
    if (data.live_market_jobs_error) {
      liveJobsError.textContent = data.live_market_jobs_error;
      liveJobsError.classList.add("error");
      return;
    }

    liveJobsError.textContent = data.resolved_location_label
      ? `Showing live role matches for ${data.resolved_location_label}.`
      : `Showing live role matches for ${locationQuery}.`;
    liveJobsError.classList.remove("error");
  } catch (error) {
    liveJobsError.textContent = error.message || "Unable to search jobs for that location right now.";
    liveJobsError.classList.add("error");
  } finally {
    setButtonLoading(searchLocationJobsButton, false, "Search Location Jobs", "Searching Jobs...");
  }
}

async function loadMoreJobs() {
  const { targetRole, locationQuery, latitude, longitude, page, hasMore } = liveJobsSearchState;
  if (!targetRole || !hasMore) {
    return;
  }

  const nextPage = Number(page || 1) + 1;
  setButtonLoading(loadMoreJobsButton, true, "Load More Jobs", "Loading More...");
  liveJobsError.textContent = "Loading more jobs...";
  liveJobsError.classList.remove("error");

  try {
    const formData = new FormData();
    formData.append("target_role", targetRole);
    formData.append("page", String(nextPage));

    if (latitude !== null && longitude !== null) {
      formData.append("latitude", String(latitude));
      formData.append("longitude", String(longitude));
    } else if (locationQuery) {
      formData.append("location_query", locationQuery);
    }

    const response = await fetch("/api/location-jobs", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to load more jobs right now.");
    }

    renderLiveJobs(data, { append: true });
    setLiveJobsSearchState({
      page: Number(data.live_market_jobs_page || nextPage),
      hasMore: Boolean(data.live_market_jobs_has_more),
      locationQuery: data.resolved_location_label || locationQuery,
    });

    if (data.live_market_jobs_error) {
      liveJobsError.textContent = data.live_market_jobs_error;
      liveJobsError.classList.add("error");
      return;
    }

    if (Array.isArray(data.live_market_jobs) && data.live_market_jobs.length > 0) {
      liveJobsError.textContent = "Loaded more jobs.";
      liveJobsError.classList.remove("error");
    } else {
      liveJobsError.textContent = "No more jobs were found for this search.";
      liveJobsError.classList.remove("error");
    }
  } catch (error) {
    liveJobsError.textContent = error.message || "Unable to load more jobs right now.";
    liveJobsError.classList.add("error");
  } finally {
    setButtonLoading(loadMoreJobsButton, false, "Load More Jobs", "Loading More...");
    updateLoadMoreJobsButton(liveJobsSearchState.hasMore, liveJobsSearchState.targetRole);
  }
}

async function renderResumeUpgrade(data, selectedRole) {
  latestLatexResume = data.latex_resume || "";
  const beforeScore = Number(data.ats_score_before || 0);
  const afterScore = Number(data.ats_score_after || beforeScore);
  upgradeScoreBefore.textContent = String(beforeScore);
  upgradeScoreAfter.textContent = String(afterScore);
  upgradeSummary.textContent = data.improvement_summary || "No upgrade summary available.";
  await renderOriginalResumePreview(data.original_resume_snapshot || "No original snapshot available.");
  upgradeUpdatedPreview.classList.remove("pdf-preview-shell");
  renderResumePreview(
    upgradeUpdatedPreview,
    data.updated_resume_snapshot || "No updated snapshot available."
  );
  upgradeLatexOutput.textContent = latestLatexResume || "% No LaTeX output was generated.";
  renderList(upgradeImprovementsList, data.key_improvements, "No improvements were generated.");
  renderList(upgradeLatexNotesList, data.latex_notes, "No LaTeX notes available.");
  upgradeResults.classList.remove("hidden");
  downloadLatexButton.classList.remove("hidden");
  openOverleafButton.classList.remove("hidden");
  copyLatexButton.classList.remove("hidden");
  setUpgradeStatus(`Generated a role-tailored resume upgrade for ${selectedRole}.`);
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

async function generateResumeUpgrade() {
  setStatus("");
  const { formData, resumeText, hasFile } = buildResumeFormData();
  if (!ensureResumeInput(resumeText, hasFile)) {
    return;
  }

  const selectedRole = targetRoleSelect.value.trim();
  const jobDescription = jobDescriptionInput.value.trim();
  if (!selectedRole) {
    setUpgradeStatus("Select a target role before generating the updated resume.", true);
    return;
  }

  formData.append("target_role", selectedRole);
  formData.append("job_description", jobDescription);
  if (Number.isFinite(latestCvScanScore) && latestCvScanScore > 0) {
    formData.append("baseline_score", String(latestCvScanScore));
  }

  setButtonLoading(generateUpgradeButton, true, "Generate Resume Difference", "Building ATS Resume...");
  setUpgradeStatus(`Generating a role-tailored resume upgrade for ${selectedRole}...`);
  startLoading([
    "Reviewing the selected role context...",
    "Rewriting resume content for ATS alignment...",
    "Building the before vs after comparison...",
    "Preparing Overleaf LaTeX output...",
  ]);

  try {
    const response = await fetch("/api/resume-upgrade", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to generate the resume upgrade right now.");
    }

    await renderResumeUpgrade(data, selectedRole);
    await compileResumePreview(data.latex_resume || "", selectedRole);
  } catch (error) {
    setUpgradeStatus(error.message || "Unexpected error while generating the updated resume.", true);
  } finally {
    stopLoading();
    setButtonLoading(
      generateUpgradeButton,
      false,
      "Generate Resume Difference",
      "Building ATS Resume..."
    );
  }
}

function downloadLatexResume() {
  if (!latestLatexResume) {
    setUpgradeStatus("Generate the updated resume before downloading the LaTeX file.", true);
    return;
  }

  const selectedRole = targetRoleSelect.value.trim();
  const fileName = `${slugify(selectedRole || "ats-upgrade")}-resume.tex`;
  const blob = new Blob([latestLatexResume], { type: "text/plain;charset=utf-8" });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

async function copyLatexResume() {
  if (!latestLatexResume) {
    setUpgradeStatus("Generate the updated resume before copying the LaTeX code.", true);
    return;
  }

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(latestLatexResume);
    } else {
      const textArea = document.createElement("textarea");
      textArea.value = latestLatexResume;
      textArea.setAttribute("readonly", "");
      textArea.style.position = "absolute";
      textArea.style.left = "-9999px";
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      textArea.remove();
    }

    setUpgradeStatus("LaTeX code copied. Paste it directly into Overleaf.");
  } catch (error) {
    setUpgradeStatus("Unable to copy the LaTeX code automatically. Use the code block below.", true);
  }
}

function openResumeInOverleaf() {
  if (!latestLatexResume) {
    setUpgradeStatus("Generate the updated resume before opening it in Overleaf.", true);
    return;
  }

  const form = document.createElement("form");
  form.action = "https://www.overleaf.com/docs";
  form.method = "post";
  form.target = "_blank";
  form.style.display = "none";

  const encodedSnip = document.createElement("input");
  encodedSnip.type = "hidden";
  encodedSnip.name = "encoded_snip";
  encodedSnip.value = encodeURIComponent(latestLatexResume);
  form.appendChild(encodedSnip);

  const snipName = document.createElement("input");
  snipName.type = "hidden";
  snipName.name = "snip_name";
  snipName.value = "resume.tex";
  form.appendChild(snipName);

  document.body.appendChild(form);
  form.submit();
  form.remove();
  setUpgradeStatus("Opened the generated LaTeX in Overleaf.");
}

async function downloadPdfResume() {
  if (!latestLatexResume) {
    setUpgradePreviewStatus("Generate the updated resume preview before downloading the PDF.", true);
    return;
  }

  try {
    setUpgradePreviewStatus("Preparing PDF download...");
    const response = await fetch("/api/compile-latex", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latex_resume: latestLatexResume }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Unable to compile the PDF for download.");
    }

    const pdfBlob = await response.blob();
    releaseCompiledDownloadPdf();
    latestCompiledPdfUrl = window.URL.createObjectURL(pdfBlob);

    const selectedRole = targetRoleSelect.value.trim();
    const fileName = `${slugify(selectedRole || "ats-upgrade")}-resume.pdf`;
    const link = document.createElement("a");
    link.href = latestCompiledPdfUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setUpgradePreviewStatus("PDF download is ready.");
  } catch (error) {
    setUpgradePreviewStatus(error.message || "Unable to download the PDF right now.", true);
  }
}

function renderCvScanResult(data, context) {
  scoreLabel.textContent = "CV Score";
  scoreSubtitle.textContent = "ATS readiness out of 100";
  listATitle.textContent = "Top Strengths";
  listBTitle.textContent = "Improvement Areas";
  latestCvScanScore = Number.isFinite(data.cv_score) ? data.cv_score : Number(data.cv_score || 0);

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
  roleAnalysisReady = false;
  upgradeCard.classList.add("hidden");
  updateUpgradeAvailability();

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
  resetUpgradeResults();
  updateUpgradeAvailability();
  const { formData, resumeText, hasFile, fileName } = buildResumeFormData();
  if (!ensureResumeInput(resumeText, hasFile)) {
    return;
  }

  setButtonLoading(scanCvButton, true, "Scan CV", "Scanning CV...");
  setStatus("Scanning your CV. This can take a few seconds...");
  startLoading([
    "Checking resume structure...",
    "Extracting skills and experience...",
    "Scoring ATS readiness...",
    "Finding relevant roles...",
  ]);

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
    stopLoading();
    setButtonLoading(scanCvButton, false, "Scan CV", "Scanning CV...");
  }
}

async function analyzeSelectedRole() {
  setStatus("");
  resetUpgradeResults();
  updateUpgradeAvailability();
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

  setButtonLoading(analyzeButton, true, "Analyze Selected Role", "Analyzing Role...");
  setStatus("Running role-specific analysis. This can take a few seconds...");
  startLoading([
    "Reading your resume context...",
    "Comparing role requirements...",
    "Checking skill overlap...",
    "Preparing tailored suggestions...",
  ]);

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
    setLiveJobsSearchState({
      targetRole: selectedRole,
      locationQuery: "",
      latitude: null,
      longitude: null,
      page: Number(data.live_market_jobs_page || 1),
      hasMore: Boolean(data.live_market_jobs_has_more),
    });

    roleAnalysisReady = true;
    upgradeCard.classList.remove("hidden");
    updateUpgradeAvailability();

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
    roleAnalysisReady = false;
    upgradeCard.classList.add("hidden");
    resetResults();
    resultsSection.classList.add("hidden");
    setStatus(error.message || "Unexpected error. Please try again.", true);
  } finally {
    stopLoading();
    setButtonLoading(analyzeButton, false, "Analyze Selected Role", "Analyzing Role...");
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
  roleAnalysisReady = false;
  upgradeCard.classList.add("hidden");
  resetUpgradeResults();
  updateUpgradeAvailability();
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

if (jobSearchLocationInput) {
  jobSearchLocationInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchJobsByLocation();
    }
  });
}

fileInput.addEventListener("change", () => {
  releaseUploadedResumePreview();
  if (fileInput.files.length > 0) {
    const selectedFile = fileInput.files[0];
    uploadedResumeFileUrl = window.URL.createObjectURL(selectedFile);
    setStatus(`Selected resume: ${selectedFile.name}`);
  } else {
    setStatus("");
  }

  roleAnalysisReady = false;
  upgradeCard.classList.add("hidden");
  resetUpgradeResults();
  updateUpgradeAvailability();

  if (suggestedRoles.length > 0) {
    setRoleStatus("Resume file changed. Re-run CV scan for updated role suggestions.");
  }
});

analyzeButton.addEventListener("click", analyzeSelectedRole);
generateUpgradeButton.addEventListener("click", generateResumeUpgrade);
useMyLocationButton.addEventListener("click", findJobsNearMe);
searchLocationJobsButton.addEventListener("click", searchJobsByLocation);
loadMoreJobsButton.addEventListener("click", loadMoreJobs);
downloadPdfButton.addEventListener("click", downloadPdfResume);
downloadLatexButton.addEventListener("click", downloadLatexResume);
openOverleafButton.addEventListener("click", openResumeInOverleaf);
copyLatexButton.addEventListener("click", copyLatexResume);
updateUpgradeAvailability();

window.addEventListener("beforeunload", releaseUploadedResumePreview);
window.addEventListener("beforeunload", releaseCompiledPdfPreview);

analysisForm.addEventListener("submit", (event) => {
  event.preventDefault();
});
