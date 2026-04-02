from pathlib import Path
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "reports" / "report_assets"
ASSETS.mkdir(parents=True, exist_ok=True)

resume_pdf = ROOT / "Vaibhav_s_resume(updated).pdf"
if not resume_pdf.exists():
    raise FileNotFoundError(f"Resume not found at {resume_pdf}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 2200})
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    time.sleep(1)

    # Full home page
    page.screenshot(path=str(ASSETS / "01_home_page.png"), full_page=True)

    # Upload resume and scan
    page.set_input_files("#resume_file", str(resume_pdf))
    page.click("#scan-cv-btn")
    page.wait_for_selector("#results-section:not(.hidden)", timeout=120000)
    time.sleep(2)

    # Crop and save CV score card
    score_card = page.locator(".score-panel")
    score_card.screenshot(path=str(ASSETS / "02_cv_score_card.png"))

    # Crop profile status section
    profile_section = page.locator("text='Profile Status & Role Direction'").locator("..").locator("..")
    profile_section.screenshot(path=str(ASSETS / "03_profile_status.png"))

    # Crop recommended roles
    roles_section = page.locator("#recommended-roles-list").locator("..")
    roles_section.screenshot(path=str(ASSETS / "04_recommended_roles.png"))

    # Full CV scan results for context
    page.screenshot(path=str(ASSETS / "05_cv_scan_full.png"), full_page=True)

    # Open job tools
    page.click("#toggle-job-tools-btn")
    page.wait_for_selector("#job-tools-section:not(.hidden)", timeout=10000)
    time.sleep(1)

    # Try to select ML-related role
    try:
        page.select_option("#target_role", label="Machine Learning Engineer")
        print("Selected: Machine Learning Engineer")
    except:
        try:
            page.select_option("#target_role", label="Data Scientist")
            print("Selected: Data Scientist")
        except:
            # Fallback: select first available role
            role_select = page.locator("#target_role")
            options = role_select.locator("option")
            if options.count() > 1:
                val = options.nth(1).get_attribute("value")
                if val:
                    page.select_option("#target_role", value=val)
                    print(f"Selected role with value: {val}")
    time.sleep(1)

    # Add a sample job description focused on ML Engineer
    jd_text = """
Machine Learning Engineer - Senior Level
We are looking for an experienced Machine Learning Engineer to build and deploy AI/ML solutions.

Key Responsibilities:
- Design and implement machine learning models and algorithms
- Work with large-scale datasets and distributed systems
- Develop end-to-end ML pipelines (data collection, preprocessing, training, evaluation)
- Collaborate with data engineers and product teams
- Optimize model performance and inference latency
- Create production-ready code with proper testing and documentation

Required Skills:
- Python, scikit-learn, TensorFlow, PyTorch
- Data analysis and statistical modeling
- SQL and database design
- Machine Learning fundamentals (supervised/unsupervised learning)
- Deep Learning and neural networks
- Model evaluation and hyperparameter tuning

Preferred:
- MLOps and model deployment
- Cloud platforms (AWS, GCP, Azure)
- Computer Vision or NLP experience
- Docker and Kubernetes
- CI/CD pipelines
    """
    page.fill("#job_description", jd_text)
    time.sleep(1)

    # Click analyze
    page.click("#analyze-btn")
    page.wait_for_function(
        "() => document.querySelector('#upgrade-card') && !document.querySelector('#upgrade-card').classList.contains('hidden')",
        timeout=120000,
    )
    time.sleep(2)

    # Crop matching skills
    matching_section = page.locator("text='Matching Skills'").locator("..").locator("..")
    matching_section.screenshot(path=str(ASSETS / "06_matching_skills.png"))

    # Crop missing skills
    missing_section = page.locator("text='Missing Skills'").locator("..").locator("..")
    missing_section.screenshot(path=str(ASSETS / "07_missing_skills.png"))

    # Crop ATS suggestions
    ats_section = page.locator("text='ATS Improvement Suggestions'").locator("..").locator("..")
    ats_section.screenshot(path=str(ASSETS / "08_ats_suggestions.png"))

    # Full role analysis
    page.screenshot(path=str(ASSETS / "09_role_analysis_full.png"), full_page=True)

    # Resume upgrade
    if page.locator("#generate-upgrade-btn").is_enabled():
        page.click("#generate-upgrade-btn")
        page.wait_for_function(
            "() => document.querySelector('#upgrade-results') && !document.querySelector('#upgrade-results').classList.contains('hidden')",
            timeout=120000,
        )
        time.sleep(2)

        # Crop upgrade score comparison
        upgrade_scores = page.locator(".upgrade-score-grid")
        upgrade_scores.screenshot(path=str(ASSETS / "10_upgrade_score_comparison.png"))

        # Crop upgrade summary
        upgrade_summary = page.locator("text='Upgrade Summary'").locator("..").locator("..")
        upgrade_summary.screenshot(path=str(ASSETS / "11_upgrade_summary.png"))

        # Crop key improvements
        improvements = page.locator("text='Key Improvements'").locator("..").locator("..")
        improvements.screenshot(path=str(ASSETS / "12_key_improvements.png"))

        # Full resume upgrade view
        page.screenshot(path=str(ASSETS / "13_resume_upgrade_full.png"), full_page=True)

    browser.close()

print("Screenshots captured and organized!")
print(f"Assets folder: {ASSETS}")
