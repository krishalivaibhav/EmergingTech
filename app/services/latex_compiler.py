import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class LaTeXCompilerUnavailableError(RuntimeError):
    pass


class LaTeXCompilationError(RuntimeError):
    pass


class LaTeXCompilerService:
    _compat_files = {
        "fullpage.sty": (
            "\\NeedsTeXFormat{LaTeX2e}\n"
            "\\ProvidesPackage{fullpage}[compat shim]\n"
            "\\DeclareOption*{}\n"
            "\\ProcessOptions\\relax\n"
            "\\endinput\n"
        ),
        "marvosym.sty": (
            "\\NeedsTeXFormat{LaTeX2e}\n"
            "\\ProvidesPackage{marvosym}[compat shim]\n"
            "\\endinput\n"
        ),
        "titlesec.sty": (
            "\\NeedsTeXFormat{LaTeX2e}\n"
            "\\ProvidesPackage{titlesec}[compat shim]\n"
            "\\newcommand{\\titlerule}{\\hrule}\n"
            "\\def\\titleformat#1#2#3#4#5[#6]{%\n"
            "  \\renewcommand{\\section}[1]{%\n"
            "    {#2 ##1}\\par\n"
            "    #6\\par\n"
            "  }%\n"
            "}\n"
            "\\endinput\n"
        ),
        "glyphtounicode.tex": "% compat shim for restricted TeX environments\n",
    }

    def __init__(self) -> None:
        self.compiler = os.getenv("LATEX_COMPILER", "pdflatex").strip().lower() or "pdflatex"
        self.timeout_seconds = int(os.getenv("LATEX_TIMEOUT_SECONDS", "30"))
        self.compile_runs = max(1, int(os.getenv("LATEX_COMPILE_RUNS", "2")))
        self.kpsewhich_path = shutil.which("kpsewhich")
        self.latexmk_path = shutil.which("latexmk")

    def compile_pdf(self, latex_source: str) -> bytes:
        source = str(latex_source or "").strip()
        if not source:
            raise LaTeXCompilationError("No LaTeX source was provided for compilation.")

        command_builder = self._build_latexmk_command if self.latexmk_path else self._build_direct_command
        command = command_builder()
        if not command:
            raise LaTeXCompilerUnavailableError(
                f"LaTeX compiler '{self.compiler}' is not installed on the server."
            )

        with tempfile.TemporaryDirectory(prefix="resume-latex-") as tmp_dir:
            workdir = Path(tmp_dir)
            tex_file = workdir / "resume.tex"
            tex_file.write_text(source, encoding="utf-8")
            self._write_compat_files(workdir)

            combined_logs: list[str] = []
            result = None
            run_count = 1 if self.latexmk_path else self.compile_runs
            for _ in range(run_count):
                try:
                    result = subprocess.run(
                        [*command, tex_file.name],
                        cwd=workdir,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout_seconds,
                        check=False,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise LaTeXCompilationError(
                        f"LaTeX compilation timed out after {self.timeout_seconds} seconds."
                    ) from exc

                combined_logs.extend(part for part in [result.stdout, result.stderr] if part)
                if result.returncode != 0:
                    break

            pdf_file = workdir / "resume.pdf"
            if result is None or result.returncode != 0 or not pdf_file.exists():
                combined_log = "\n".join(combined_logs).strip()
                error_hint = self._extract_error_hint(combined_log)
                raise LaTeXCompilationError(
                    f"LaTeX compilation failed. {error_hint}".strip()
                )

            return pdf_file.read_bytes()

    def _build_latexmk_command(self) -> list[str]:
        if not self.latexmk_path:
            return []

        engine_flag = {
            "pdflatex": "-pdf",
            "xelatex": "-xelatex",
            "lualatex": "-lualatex",
        }.get(self.compiler)
        if not engine_flag:
            return []

        return [
            self.latexmk_path,
            engine_flag,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-cd",
        ]

    def _build_direct_command(self) -> list[str]:
        compiler_path = shutil.which(self.compiler)
        if not compiler_path:
            return []

        return [
            compiler_path,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-no-shell-escape",
        ]

    def _write_compat_files(self, workdir: Path) -> None:
        for filename, contents in self._compat_files.items():
            if self._tex_asset_exists(filename):
                continue
            (workdir / filename).write_text(contents, encoding="utf-8")

    def _tex_asset_exists(self, filename: str) -> bool:
        if not self.kpsewhich_path:
            return False
        result = subprocess.run(
            [self.kpsewhich_path, filename],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    @staticmethod
    def _extract_error_hint(log_output: str) -> str:
        if not log_output:
            return "Check the generated LaTeX for syntax or package issues."

        for line in log_output.splitlines():
            stripped = line.strip()
            if stripped.startswith("!"):
                return stripped.lstrip("!").strip()

        return "Check the generated LaTeX for syntax or package issues."
