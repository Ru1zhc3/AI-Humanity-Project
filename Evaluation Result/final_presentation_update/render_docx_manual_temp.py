from __future__ import annotations

import os
import runpy
from pathlib import Path


ROOT = Path(r"E:\CourseProject\cs4501_26spring_final_project")
DOCX = ROOT / "Political Content Moderation Across Different Models and Languages_script.docx"
OUT = ROOT / "Evaluation Result" / "final_presentation_update" / "docx_render"
PROFILE = ROOT / "Evaluation Result" / "final_presentation_update" / "render_profile"
CONVERT = ROOT / "Evaluation Result" / "final_presentation_update" / "render_convert"
RENDER_SCRIPT = Path(
    r"C:\Users\Yi Ping\.codex\plugins\cache\openai-primary-runtime\documents\26.426.12240\skills\documents\render_docx.py"
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PROFILE.mkdir(parents=True, exist_ok=True)
    CONVERT.mkdir(parents=True, exist_ok=True)

    ns = runpy.run_path(str(RENDER_SCRIPT))
    stem = DOCX.stem
    pdf_path, debug = ns["convert_to_pdf"](
        str(DOCX.resolve()),
        str(PROFILE.resolve()),
        str(CONVERT.resolve()),
        stem,
        False,
    )
    if not pdf_path or not Path(pdf_path).exists():
        raise RuntimeError("DOCX to PDF conversion failed.\n" + debug)

    paths_raw = ns["convert_from_path"](
        pdf_path,
        dpi=150,
        fmt="png",
        thread_count=4,
        output_folder=str(OUT.resolve()),
        paths_only=True,
        output_file="page",
    )
    page_paths = []
    for src in paths_raw:
        src_path = Path(src)
        page_num = int(src_path.stem.split("-")[-1])
        dst = OUT / f"page-{page_num}.png"
        os.replace(src_path, dst)
        page_paths.append(dst)

    for path in sorted(page_paths, key=lambda p: int(p.stem.split("-")[-1])):
        print(path)


if __name__ == "__main__":
    main()
