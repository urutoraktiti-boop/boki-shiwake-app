#!/usr/bin/env python3
"""Validate an eight-question mock-exam draft JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SYMBOLS = tuple("アイウエオカキク")
UNSAFE_HTML_RE = re.compile(r"<\s*/?\s*[a-zA-Z]|javascript\s*:|onerror\s*=", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
IMAGE_SRC_RE = re.compile(r"assets/explanations/[A-Za-z0-9._/-]+\.png", re.IGNORECASE)
VERIFIED_FIGURE_COUNTS = {
    "2025-mock-r1-industrial-q2": 1,
    "2025-mock-r2-industrial-q2": 1,
    "2025-mock-r5-industrial-q2": 1,
}
TITLE_MAP_PATH = Path(__file__).resolve().parent.parent / "references" / "title-map.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Validate a generated skeleton while reporting empty content as warnings",
    )
    parser.add_argument(
        "--asset-root",
        type=Path,
        help="Root used to resolve explanation image src paths (default: JSON directory)",
    )
    return parser.parse_args()


def validate_text(value, path: str, errors: list[str]) -> None:
    if isinstance(value, str):
        if UNSAFE_HTML_RE.search(value):
            errors.append(f"{path}: HTML/script-like content is not allowed")
        if CONTROL_RE.search(value):
            errors.append(f"{path}: control characters are not allowed")


def counter_for_entries(
    value,
    path: str,
    options: dict,
    errors: list[str],
) -> Counter:
    result: Counter = Counter()
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: at least one entry is required")
        return result
    for index, row in enumerate(value):
        row_path = f"{path}[{index}]"
        if not isinstance(row, list) or len(row) != 2:
            errors.append(f"{row_path}: expected [symbol, amount]")
            continue
        symbol, amount = row
        if symbol not in options:
            errors.append(f"{row_path}: symbol {symbol!r} is not in options")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            errors.append(f"{row_path}: amount must be a positive integer")
            continue
        result[(symbol, amount)] += 1
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_explanation_images(
    value,
    path: str,
    question_id: str,
    round_no: int,
    explanation_pages: list[int],
    asset_root: Path,
    allow_incomplete: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return
    expected_count = VERIFIED_FIGURE_COUNTS.get(question_id, 0)
    if len(value) != expected_count:
        message = (
            f"{path}: expected {expected_count} verified figure(s) for {question_id}, "
            f"found {len(value)}"
        )
        (warnings if allow_incomplete else errors).append(message)
    root = asset_root.resolve()
    for index, record in enumerate(value):
        record_path = f"{path}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{record_path}: expected object")
            continue

        for field in ("alt", "caption"):
            text = record.get(field)
            validate_text(text, f"{record_path}.{field}", errors)
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{record_path}.{field}: non-empty string required")

        src = record.get("src")
        expected_src = (
            f"assets/explanations/2025-mock/r{round_no}/"
            f"{question_id}-figure-{index + 1}.png"
        )
        if (
            not isinstance(src, str)
            or not IMAGE_SRC_RE.fullmatch(src)
            or ".." in Path(src).parts
            or "\\" in src
        ):
            errors.append(
                f"{record_path}.src: safe relative assets/explanations/*.png path required"
            )
            image_path = None
        else:
            if src != expected_src:
                errors.append(f"{record_path}.src: expected {expected_src!r}")
            candidate = (root / src).resolve()
            if candidate != root and root not in candidate.parents:
                errors.append(f"{record_path}.src: path escapes asset root")
                image_path = None
            else:
                image_path = candidate

        if record.get("mimeType") != "image/png":
            errors.append(f"{record_path}.mimeType: expected image/png")

        source_page = record.get("sourcePage")
        if (
            isinstance(source_page, bool)
            or not isinstance(source_page, int)
            or source_page not in explanation_pages
        ):
            errors.append(
                f"{record_path}.sourcePage: expected one of question explanation pages {explanation_pages}"
            )

        render_dpi = record.get("renderDpi")
        if (
            isinstance(render_dpi, bool)
            or not isinstance(render_dpi, int)
            or not 170 <= render_dpi <= 220
        ):
            errors.append(f"{record_path}.renderDpi: expected integer 170..220")

        box = record.get("cropBox")
        box_width = box_height = None
        if (
            not isinstance(box, list)
            or len(box) != 4
            or any(isinstance(item, bool) or not isinstance(item, int) for item in box)
        ):
            errors.append(f"{record_path}.cropBox: expected four integer coordinates")
        else:
            left, top, right, bottom = box
            if min(box) < 0 or right <= left or bottom <= top:
                errors.append(f"{record_path}.cropBox: expected a positive rectangle")
            else:
                box_width, box_height = right - left, bottom - top

        width, height = record.get("width"), record.get("height")
        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            errors.append(f"{record_path}.width: positive integer required")
        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            errors.append(f"{record_path}.height: positive integer required")
        if box_width is not None and (width, height) != (box_width, box_height):
            errors.append(
                f"{record_path}: dimensions {width}x{height} do not match cropBox {box_width}x{box_height}"
            )

        expected_hash = record.get("sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(expected_hash or "")):
            errors.append(f"{record_path}.sha256: expected lowercase SHA-256")

        if record.get("reviewStatus") != "reviewed":
            message = f"{record_path}.reviewStatus: expected reviewed after crop inspection"
            (warnings if allow_incomplete else errors).append(message)

        if image_path is None:
            continue
        if not image_path.is_file():
            errors.append(f"{record_path}.src: file not found under asset root")
            continue
        try:
            with Image.open(image_path) as image:
                image.load()
                if image.format != "PNG":
                    errors.append(f"{record_path}.src: file is not a PNG")
                if image.size != (width, height):
                    errors.append(
                        f"{record_path}: file dimensions {image.width}x{image.height} "
                        f"do not match metadata {width}x{height}"
                    )
        except (OSError, UnidentifiedImageError) as exc:
            errors.append(f"{record_path}.src: unreadable image ({exc})")
        if re.fullmatch(r"[0-9a-f]{64}", str(expected_hash or "")):
            actual_hash = sha256_file(image_path)
            if actual_hash != expected_hash:
                errors.append(f"{record_path}.sha256: file hash mismatch")


def main() -> int:
    args = parse_args()
    asset_root = (args.asset_root or args.json_file.parent).expanduser()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = json.loads(args.json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        title_map_data = json.loads(TITLE_MAP_PATH.read_text(encoding="utf-8"))
        title_map = title_map_data.get("titles", {})
        if not isinstance(title_map, dict):
            raise ValueError("titles must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"title-map: could not load {TITLE_MAP_PATH} ({exc})")
        title_map = {}

    if not isinstance(data, dict):
        errors.append("root: expected object")
        data = {}
    if data.get("schemaVersion") != 2:
        errors.append("schemaVersion: expected 2")
    if data.get("status") != "draft":
        errors.append("status: expected draft")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source: expected object")
        source = {}
    round_no = source.get("round")
    if isinstance(round_no, bool) or not isinstance(round_no, int) or not 1 <= round_no <= 6:
        errors.append("source.round: expected integer 1..6")
        round_no = 0
    if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", ""))):
        errors.append("source.sha256: expected lowercase SHA-256")
    if source.get("expectedQuestionCount") != 8:
        errors.append("source.expectedQuestionCount: expected 8")
    if source.get("expectedPoints") != 32:
        errors.append("source.expectedPoints: expected 32")
    source_sections = source.get("sections")
    if not isinstance(source_sections, dict):
        errors.append("source.sections: expected object")
        source_sections = {}

    questions = data.get("questions")
    if not isinstance(questions, list):
        errors.append("questions: expected array")
        questions = []
    if len(questions) != 8:
        errors.append(f"questions: expected 8, found {len(questions)}")

    ids: set[str] = set()
    seen_pairs: list[tuple[str, int]] = []
    total_points = 0
    for index, question in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path}: expected object")
            continue

        section = question.get("section")
        question_no = question.get("questionNo")
        if section not in {"commercial", "industrial"}:
            errors.append(f"{path}.section: expected commercial or industrial")
        if isinstance(question_no, bool) or not isinstance(question_no, int):
            errors.append(f"{path}.questionNo: expected integer")
        else:
            seen_pairs.append((section, question_no))

        expected_id = f"2025-mock-r{round_no}-{section}-q{question_no}"
        question_id = question.get("questionId")
        if question_id != expected_id:
            errors.append(f"{path}.questionId: expected {expected_id!r}")
        if question_id in ids:
            errors.append(f"{path}.questionId: duplicate {question_id!r}")
        ids.add(question_id)

        expected_group = (
            f"2025年度2級直前模試 第{round_no}回・第1問"
            if section == "commercial"
            else f"2025年度2級直前模試 第{round_no}回・第4問(1)"
        )
        if question.get("group") != expected_group:
            errors.append(f"{path}.group: expected {expected_group!r}")
        if question.get("points") != 4:
            errors.append(f"{path}.points: expected 4")
        else:
            total_points += 4

        for field in ("label", "category", "topic", "text", "expl"):
            value = question.get(field)
            validate_text(value, f"{path}.{field}", errors)
            if not isinstance(value, str) or not value.strip():
                message = f"{path}.{field}: non-empty string required"
                (warnings if args.allow_incomplete else errors).append(message)
        expected_topic = title_map.get(str(question_id))
        topic = question.get("topic")
        if expected_topic and isinstance(topic, str) and topic.strip() and topic != expected_topic:
            errors.append(f"{path}.topic: expected {expected_topic!r} for {question_id}")
        if question.get("category") in {"未分類", "要確認"}:
            errors.append(f"{path}.category: review and assign a specific category")

        options = question.get("options")
        if not isinstance(options, dict) or not options:
            message = f"{path}.options: non-empty object required"
            (warnings if args.allow_incomplete else errors).append(message)
            options = {}
        else:
            expected_option_count = 8 if section == "commercial" else 6
            if len(options) != expected_option_count:
                errors.append(
                    f"{path}.options: expected {expected_option_count} symbols for {section}, found {len(options)}"
                )
            for symbol, account in options.items():
                if symbol not in SYMBOLS:
                    errors.append(f"{path}.options: unsupported symbol {symbol!r}")
                if not isinstance(account, str) or not account.strip():
                    errors.append(f"{path}.options.{symbol}: account name required")
                validate_text(account, f"{path}.options.{symbol}", errors)

        debit = question.get("debit")
        credit = question.get("credit")
        incomplete_entries = not debit or not credit or not options
        if incomplete_entries and args.allow_incomplete:
            warnings.append(f"{path}: answer entries are incomplete")
            debit_counter = Counter()
            credit_counter = Counter()
        else:
            debit_counter = counter_for_entries(debit, f"{path}.debit", options, errors)
            credit_counter = counter_for_entries(credit, f"{path}.credit", options, errors)
            debit_total = sum(amount * count for (_, amount), count in debit_counter.items())
            credit_total = sum(amount * count for (_, amount), count in credit_counter.items())
            if debit_total != credit_total:
                errors.append(f"{path}: debit {debit_total} != credit {credit_total}")

        subtransactions = question.get("subTransactions", [])
        if not isinstance(subtransactions, list):
            errors.append(f"{path}.subTransactions: expected array")
            subtransactions = []
        if subtransactions and not incomplete_entries:
            sub_debit = Counter()
            sub_credit = Counter()
            sub_points = 0
            points_are_explicit = True
            for sub_index, sub in enumerate(subtransactions):
                sub_path = f"{path}.subTransactions[{sub_index}]"
                if not isinstance(sub, dict):
                    errors.append(f"{sub_path}: expected object")
                    continue
                d = counter_for_entries(sub.get("debit"), f"{sub_path}.debit", options, errors)
                c = counter_for_entries(sub.get("credit"), f"{sub_path}.credit", options, errors)
                d_total = sum(amount * count for (_, amount), count in d.items())
                c_total = sum(amount * count for (_, amount), count in c.items())
                if d_total != c_total:
                    errors.append(f"{sub_path}: debit {d_total} != credit {c_total}")
                sub_debit.update(d)
                sub_credit.update(c)
                if "points" in sub:
                    value = sub.get("points")
                    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                        errors.append(f"{sub_path}.points: positive integer required")
                    else:
                        sub_points += value
                else:
                    points_are_explicit = False
            if sub_debit != debit_counter or sub_credit != credit_counter:
                errors.append(f"{path}.subTransactions: flattened entries do not match debit/credit")
            if points_are_explicit and sub_points != question.get("points"):
                errors.append(f"{path}.subTransactions: explicit points total {sub_points}, expected 4")

        source_pages = question.get("sourcePages")
        explanation_pages: list[int] = []
        if not isinstance(source_pages, dict):
            errors.append(f"{path}.sourcePages: expected object")
        else:
            for field in ("problem", "answer", "explanation"):
                values = source_pages.get(field)
                if not isinstance(values, list) or not values or any(
                    isinstance(value, bool) or not isinstance(value, int) or value <= 0
                    for value in values
                ):
                    errors.append(f"{path}.sourcePages.{field}: positive page array required")
                else:
                    if field == "explanation":
                        explanation_pages = values
                    section_pages = source_sections.get(section, {})
                    allowed = section_pages.get(field, []) if isinstance(section_pages, dict) else []
                    if not isinstance(allowed, list) or not set(values).issubset(set(allowed)):
                        errors.append(
                            f"{path}.sourcePages.{field}: {values} is outside source section pages {allowed}"
                        )

        validate_explanation_images(
            question.get("explanationImages"),
            f"{path}.explanationImages",
            str(question_id or ""),
            round_no,
            explanation_pages,
            asset_root,
            args.allow_incomplete,
            errors,
            warnings,
        )

        if question.get("reviewStatus") != "reviewed":
            message = f"{path}.reviewStatus: expected reviewed after visual comparison"
            (warnings if args.allow_incomplete else errors).append(message)

    expected_pairs = [("commercial", number) for number in range(1, 6)] + [
        ("industrial", number) for number in range(1, 4)
    ]
    if sorted(seen_pairs) != sorted(expected_pairs):
        errors.append(f"questions: section/questionNo set is invalid: {seen_pairs}")
    if total_points != 32:
        errors.append(f"questions: expected 32 total points, found {total_points}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: 8 questions / 32 points; {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
