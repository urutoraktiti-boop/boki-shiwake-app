#!/usr/bin/env python3
"""Prepare the eight-question source packet for a 2025 Level 2 mock PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover - environment guidance
    raise SystemExit(
        "pdfplumber is required. Use the bundled workspace Python runtime."
    ) from exc


TOP_NUMBER_RE = re.compile(r"(?m)^\s*([1-5１-５])\s*[.．]")
PART2_RE = re.compile(r"(?m)^\s*[（(]\s*2\s*[）)]\s+")
PART2_EXPLANATION_RE = re.compile(
    r"(?m)^\s*[（(]\s*2\s*[）)]\s+[^\n]*問題である"
)


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def round_from_name(path: Path) -> int:
    match = re.search(r"第\s*([1-6１-６])\s*回", path.stem)
    if not match:
        raise ValueError("Filename must contain 第1回 through 第6回")
    return int(unicodedata.normalize("NFKC", match.group(1)))


def find_page(norm_pages: list[str], label: str, predicate, start: int = 0, end: int | None = None) -> int:
    stop = len(norm_pages) if end is None else end
    matches = [index for index in range(start, stop) if predicate(norm_pages[index])]
    if len(matches) != 1:
        pages = [index + 1 for index in matches]
        raise ValueError(f"Expected one {label} page, found {pages or 'none'}")
    return matches[0]


def slice_from(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return text[match.start() :] if match else text


def cut_part2_after_question3(text: str, explanation: bool = False) -> str:
    q3 = re.search(r"(?m)^\s*[3３]\s*[.．]", text)
    if not q3:
        return text
    pattern = PART2_EXPLANATION_RE if explanation else PART2_RE
    part2 = pattern.search(text, q3.end())
    return text[: part2.start()] if part2 else text


def collect_until(
    page_texts: list[str],
    start: int,
    start_pattern: str,
    stop_pattern: re.Pattern[str],
    max_pages: int = 4,
) -> tuple[list[int], str]:
    selected: list[int] = []
    chunks: list[str] = []
    for index in range(start, min(len(page_texts), start + max_pages)):
        text = page_texts[index]
        if index == start:
            text = slice_from(text, start_pattern)
        selected.append(index)
        chunks.append(text)
        joined = "\n".join(chunks)
        stop = stop_pattern.search(joined)
        if stop:
            previous = "\n".join(chunks[:-1])
            current_offset = len(previous) + (1 if previous else 0)
            if index > start and not joined[current_offset : stop.start()].strip():
                selected.pop()
            return selected, joined[: stop.start()]
    raise ValueError(f"Could not find section end within {max_pages} pages from page {start + 1}")


def top_numbers(text: str) -> list[int]:
    return [int(unicodedata.normalize("NFKC", value)) for value in TOP_NUMBER_RE.findall(text)]


def render_pages(pdf_path: Path, pages: list[int], output_dir: Path, binary: str, dpi: int) -> list[str]:
    image_dir = output_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[str] = []
    for page in pages:
        prefix = image_dir / f"page-{page:02d}"
        command = [
            binary,
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            "-png",
            "-r",
            str(dpi),
            str(pdf_path),
            str(prefix),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        rendered.append(str(prefix.with_suffix(".png").relative_to(output_dir)))
    return rendered


def skeleton_question(round_no: int, section: str, question_no: int, pages: dict[str, list[int]]) -> dict:
    if section == "commercial":
        suffix = "commercial"
        section_label = "第1問"
        group = f"2025年度2級直前模試 第{round_no}回・第1問"
    else:
        suffix = "industrial"
        section_label = "第4問(1)"
        group = f"2025年度2級直前模試 第{round_no}回・第4問(1)"
    return {
        "questionId": f"2025-mock-r{round_no}-{suffix}-q{question_no}",
        "section": section,
        "questionNo": question_no,
        "label": f"第{round_no}回 {section_label} 問{question_no}",
        "category": "",
        "topic": "",
        "text": "",
        "options": {},
        "debit": [],
        "credit": [],
        "subTransactions": [],
        "expl": "",
        "explanationImages": [],
        "group": group,
        "points": 4,
        "sourcePages": pages,
        "reviewStatus": "unreviewed",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="2025年度2級直前模試第N回.pdf")
    parser.add_argument("--output", required=True, type=Path, help="Output packet directory")
    parser.add_argument("--pdftoppm", help="pdftoppm executable path; omit to search PATH")
    parser.add_argument("--dpi", type=int, default=170)
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting packet files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise SystemExit(f"PDF not found: {pdf_path}")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"Output directory is not empty: {output_dir}; use --overwrite intentionally")
    output_dir.mkdir(parents=True, exist_ok=True)

    round_no = round_from_name(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        page_texts = [page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in pdf.pages]
    norm_pages = [normalized(text) for text in page_texts]

    answer_start = find_page(norm_pages, "試験解答 start", lambda value: "試験解答" in value)
    explanation_start = find_page(norm_pages, "試験解説 start", lambda value: "試験解説" in value)

    commercial_problem = find_page(
        norm_pages,
        "commercial problem",
        lambda value: "商業簿記" in value and "第1問" in value and "仕訳しなさい" in value,
        end=answer_start,
    )
    industrial_problem = find_page(
        norm_pages,
        "industrial problem",
        lambda value: "工業簿記" in value and "第4問" in value and "(1)" in value and "仕訳しなさい" in value,
        end=answer_start,
    )
    commercial_answer = find_page(
        norm_pages,
        "commercial answer",
        lambda value: "第1問(20点)" in value and "借方" in value and "貸方" in value,
        start=answer_start,
        end=explanation_start,
    )
    industrial_answer = find_page(
        norm_pages,
        "industrial answer",
        lambda value: "第4問(28点)" in value and "(1)" in value and "借方" in value and "貸方" in value,
        start=answer_start,
        end=explanation_start,
    )
    commercial_explanation = find_page(
        norm_pages,
        "commercial explanation",
        lambda value: "★商業簿記★" in value and "第1問" in value,
        start=explanation_start,
    )
    industrial_explanation = find_page(
        norm_pages,
        "industrial explanation",
        lambda value: "★工業簿記★" in value and "第4問" in value,
        start=explanation_start,
    )

    commercial_problem_text = slice_from(page_texts[commercial_problem], r"第\s*[1１]\s*問")
    industrial_problem_text = slice_from(
        page_texts[industrial_problem], r"[（(]\s*1\s*[）)]"
    )
    industrial_problem_text = cut_part2_after_question3(industrial_problem_text)

    commercial_answer_text = slice_from(page_texts[commercial_answer], r"第\s*[1１]\s*問")
    industrial_answer_text = slice_from(page_texts[industrial_answer], r"[（(]\s*1\s*[）)]")
    industrial_answer_text = cut_part2_after_question3(industrial_answer_text)

    commercial_explanation_pages, commercial_explanation_text = collect_until(
        page_texts,
        commercial_explanation,
        r"★\s*商\s*業\s*簿\s*記\s*★",
        re.compile(r"(?m)^\s*第\s*[2２]\s*問"),
        max_pages=3,
    )
    industrial_explanation_pages, industrial_explanation_text = collect_until(
        page_texts,
        industrial_explanation,
        r"★\s*工\s*業\s*簿\s*記\s*★",
        PART2_EXPLANATION_RE,
        max_pages=4,
    )

    commercial_numbers = top_numbers(commercial_problem_text)
    industrial_numbers = top_numbers(industrial_problem_text)
    if commercial_numbers != [1, 2, 3, 4, 5]:
        raise SystemExit(f"Commercial top-level question detection failed: {commercial_numbers}")
    if industrial_numbers != [1, 2, 3]:
        raise SystemExit(f"Industrial top-level question detection failed: {industrial_numbers}")

    pages = {
        "commercial": {
            "problem": [commercial_problem + 1],
            "answer": [commercial_answer + 1],
            "explanation": [index + 1 for index in commercial_explanation_pages],
        },
        "industrial": {
            "problem": [industrial_problem + 1],
            "answer": [industrial_answer + 1],
            "explanation": [index + 1 for index in industrial_explanation_pages],
        },
    }

    section_dir = output_dir / "sections"
    section_dir.mkdir(parents=True, exist_ok=True)
    section_texts = {
        "commercial-problem.txt": commercial_problem_text,
        "commercial-answer.txt": commercial_answer_text,
        "commercial-explanation.txt": commercial_explanation_text,
        "industrial-problem.txt": industrial_problem_text,
        "industrial-answer.txt": industrial_answer_text,
        "industrial-explanation.txt": industrial_explanation_text,
    }
    for name, text in section_texts.items():
        (section_dir / name).write_text(text.strip() + "\n", encoding="utf-8")

    selected_pages = sorted(
        set(
            pages["commercial"]["problem"]
            + pages["commercial"]["answer"]
            + pages["commercial"]["explanation"]
            + pages["industrial"]["problem"]
            + pages["industrial"]["answer"]
            + pages["industrial"]["explanation"]
        )
    )
    binary = args.pdftoppm or shutil.which("pdftoppm")
    rendered_images: list[str] = []
    warnings: list[str] = []
    if binary:
        rendered_images = render_pages(pdf_path, selected_pages, output_dir, binary, args.dpi)
    else:
        warnings.append("pdftoppm not found; render selected pages before review")

    manifest = {
        "schemaVersion": 1,
        "fileName": pdf_path.name,
        "sha256": sha256_file(pdf_path),
        "bytes": pdf_path.stat().st_size,
        "pageCount": len(page_texts),
        "round": round_no,
        "expectedQuestionCount": 8,
        "expectedPoints": 32,
        "sections": pages,
        "selectedPages": selected_pages,
        "renderedImages": rendered_images,
        "warnings": warnings,
    }

    questions = [
        skeleton_question(round_no, "commercial", number, pages["commercial"])
        for number in range(1, 6)
    ] + [
        skeleton_question(round_no, "industrial", number, pages["industrial"])
        for number in range(1, 4)
    ]
    draft = {
        "schemaVersion": 2,
        "name": f"2025年度2級直前模試 第{round_no}回（第1問・第4問(1)）",
        "status": "draft",
        "source": {
            "fileName": pdf_path.name,
            "sha256": manifest["sha256"],
            "round": round_no,
            "expectedQuestionCount": 8,
            "expectedPoints": 32,
            "sections": pages,
        },
        "questions": questions,
    }

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "draft-template.json").write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Prepared round {round_no}: 8 questions / 32 points; "
        f"selected pages {selected_pages}; output {output_dir}"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
