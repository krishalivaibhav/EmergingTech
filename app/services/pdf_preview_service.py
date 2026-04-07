import shutil
import subprocess
import tempfile
from pathlib import Path


class PDFPreviewUnavailableError(RuntimeError):
    pass


class PDFPreviewRenderError(RuntimeError):
    pass


class PDFPreviewService:
    def __init__(self) -> None:
        self.pdftoppm_path = shutil.which("pdftoppm")
        self.sips_path = shutil.which("sips")
        self.render_dpi = 144

    def render_first_page_png(self, pdf_bytes: bytes) -> bytes:
        if not pdf_bytes:
            raise PDFPreviewRenderError("No PDF bytes were provided for preview rendering.")

        with tempfile.TemporaryDirectory(prefix="resume-preview-") as tmp_dir:
            workdir = Path(tmp_dir)
            pdf_path = workdir / "resume.pdf"
            pdf_path.write_bytes(pdf_bytes)

            png_path = self._render_pdf_to_png(pdf_path, workdir)
            if not png_path.exists():
                raise PDFPreviewRenderError("Preview image was not created.")

            return png_path.read_bytes()

    def _render_pdf_to_png(self, pdf_path: Path, workdir: Path) -> Path:
        if self.pdftoppm_path:
            output_base = workdir / "preview"
            result = subprocess.run(
                [
                    self.pdftoppm_path,
                    "-r",
                    str(self.render_dpi),
                    "-png",
                    "-singlefile",
                    str(pdf_path),
                    str(output_base),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise PDFPreviewRenderError(
                    result.stderr.strip() or "pdftoppm failed while rendering the preview."
                )
            return output_base.with_suffix(".png")

        if self.sips_path:
            output_path = workdir / "preview.png"
            result = subprocess.run(
                [self.sips_path, "-s", "format", "png", str(pdf_path), "--out", str(output_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise PDFPreviewRenderError(
                    result.stderr.strip() or result.stdout.strip() or "sips failed while rendering the preview."
                )
            return output_path

        raise PDFPreviewUnavailableError(
            "No PDF preview renderer is installed. Install pdftoppm or use a macOS environment with sips."
        )
