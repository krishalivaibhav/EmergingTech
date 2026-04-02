#!/usr/bin/env python3
"""
Capture comprehensive full-page screenshots showing all information.
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_screenshots():
    """Capture comprehensive screenshots with full content visible."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1600, "height": 3000})
        page = await context.new_page()
        
        url = "http://localhost:8000"
        await page.goto(url, wait_until="networkidle")
        
        output_dir = "/Users/vaibhavkrishali/Desktop/College/emerging tech/reports/report_assets"
        os.makedirs(output_dir, exist_ok=True)
        
        print("Capturing comprehensive screenshots...")
        
        # 1. Home page full view
        await page.screenshot(path=f"{output_dir}/01_home_interface.png", full_page=True)
        print("✓ 01_home_interface.png")
        
        # 2. Upload resume and prepare for scan
        resume_path = "/Users/vaibhavkrishali/Desktop/College/emerging tech/Vaibhav_s_resume(updated).pdf"
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(resume_path)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{output_dir}/02_resume_selected.png", full_page=True)
        print("✓ 02_resume_selected.png")
        
        # 3. Click Scan CV button
        buttons = await page.locator("button").all()
        scan_button = None
        for btn in buttons:
            text = await btn.text_content()
            if "Scan" in text:
                scan_button = btn
                break
        
        if scan_button:
            await scan_button.click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{output_dir}/03_cv_scan_top.png", full_page=True)
        print("✓ 03_cv_scan_top.png")
        
        # 4. Scroll down to see more CV scan results
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/04_cv_scan_middle.png", full_page=True)
        print("✓ 04_cv_scan_middle.png")
        
        # 5. Continue scrolling
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/05_cv_scan_bottom.png", full_page=True)
        print("✓ 05_cv_scan_bottom.png")
        
        # 6. Back to top and find role selection
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(800)
        
        # Look for role/role button and click ML Engineer
        role_buttons = await page.locator("button, div[role='button']").all()
        ml_clicked = False
        for btn in role_buttons:
            try:
                text = await btn.text_content()
                if "Machine Learning" in text or "ML Engineer" in text:
                    await btn.click()
                    ml_clicked = True
                    print("  → Clicked ML Engineer role")
                    break
            except:
                pass
        
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{output_dir}/06_role_selected.png", full_page=True)
        print("✓ 06_role_selected.png")
        
        # 7. Find and fill job description textarea
        textarea = page.locator("textarea")
        if await textarea.count() > 0:
            job_desc = """Machine Learning Engineer

Core Requirements:
- Python (3.8+)
- TensorFlow / PyTorch
- Deep Learning & Neural Networks
- Model Optimization & Deployment
- MLOps & Model Monitoring
- Docker & Kubernetes
- Cloud Platforms (AWS/GCP/Azure)
- Data Pipelines & ETL
- SQL & Data Structures
- Git & CI/CD Pipelines

Nice to Have:
- Computer Vision
- NLP Experience
- Distributed Computing
- A/B Testing & Experimentation
- Communication & Collaboration"""
            await textarea.fill(job_desc)
            await page.wait_for_timeout(500)
        
        await page.screenshot(path=f"{output_dir}/07_job_description.png", full_page=True)
        print("✓ 07_job_description.png")
        
        # 8. Find and click Analyze button
        buttons = await page.locator("button").all()
        for btn in buttons:
            text = await btn.text_content()
            if "Analyze" in text:
                await btn.click()
                print("  → Clicked Analyze button")
                break
        
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{output_dir}/08_analysis_top.png", full_page=True)
        print("✓ 08_analysis_top.png")
        
        # 9. Scroll to see analysis results
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/09_analysis_middle.png", full_page=True)
        print("✓ 09_analysis_middle.png")
        
        # 10. Continue scrolling analysis
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/10_analysis_bottom.png", full_page=True)
        print("✓ 10_analysis_bottom.png")
        
        # 11. Back to top for resume upgrade
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(800)
        
        # Find and click Upgrade Resume button
        buttons = await page.locator("button").all()
        for btn in buttons:
            try:
                text = await btn.text_content()
                if "Upgrade" in text:
                    await btn.click()
                    print("  → Clicked Upgrade Resume button")
                    break
            except:
                pass
        
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{output_dir}/11_upgrade_top.png", full_page=True)
        print("✓ 11_upgrade_top.png")
        
        # 12. Scroll upgrade results
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/12_upgrade_middle.png", full_page=True)
        print("✓ 12_upgrade_middle.png")
        
        # 13. Continue scrolling
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/13_upgrade_bottom.png", full_page=True)
        print("✓ 13_upgrade_bottom.png")
        
        # 14. Final scroll
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{output_dir}/14_final_results.png", full_page=True)
        print("✓ 14_final_results.png")
        
        await browser.close()
        print(f"\n✅ Comprehensive screenshots captured!")
        print(f"📁 Saved to: {output_dir}")

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
