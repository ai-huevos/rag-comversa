#!/usr/bin/env python3
"""
Lightweight Markdown-to-PDF converter tailored for the Bolivian Foods context documents.
It supports headings, paragraphs, unordered/ordered lists, horizontal rules, and basic tables.
"""
from __future__ import annotations

import math
import os
import re
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

PAGE_WIDTH = 612  # Letter size in points
PAGE_HEIGHT = 792
MARGIN_LEFT = 56
MARGIN_RIGHT = 56
MARGIN_TOP = 56
MARGIN_BOTTOM = 64

BASE_FONT_SIZE = 12
LIST_FONT_SIZE = 11
TABLE_FONT_SIZE = 10


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handler:
        return handler.read()


# ---------- Markdown parsing ----------

Block = Dict[str, object]
ListItem = Dict[str, object]


def parse_blocks(text: str) -> List[Block]:
    lines = text.splitlines()
    blocks: List[Block] = []
    index = 0
    total = len(lines)

    while index < total:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            blocks.append({"type": "heading", "level": level, "text": content})
            index += 1
            continue

        if maybe_table(lines, index):
            table_lines, index = collect_table(lines, index)
            header = split_table_row(table_lines[0])
            rows = [split_table_row(row_line) for row_line in table_lines[2:]]
            blocks.append({"type": "table", "header": header, "rows": rows})
            continue

        if re.match(r"^\s*[-*_]{3,}\s*$", stripped):
            blocks.append({"type": "hr"})
            index += 1
            continue

        if re.match(r"^\s*[-+*]\s+", line):
            items, index = parse_list(lines, index, ordered=False)
            blocks.append({"type": "ul", "items": items})
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items, index = parse_list(lines, index, ordered=True)
            blocks.append({"type": "ol", "items": items})
            continue

        paragraph_lines = [line]
        index += 1
        while index < total:
            next_line = lines[index]
            if not next_line.strip():
                index += 1
                break
            if re.match(r"^(#{1,6})\s+", next_line):
                break
            if maybe_table(lines, index):
                break
            if re.match(r"^\s*[-+*]\s+", next_line) or re.match(r"^\s*\d+\.\s+", next_line):
                break
            if re.match(r"^\s*[-*_]{3,}\s*$", next_line.strip()):
                break
            paragraph_lines.append(next_line)
            index += 1
        paragraph = " ".join(part.strip() for part in paragraph_lines).strip()
        if paragraph:
            blocks.append({"type": "paragraph", "text": paragraph})

    return blocks


def parse_list(lines: Sequence[str], start: int, ordered: bool) -> Tuple[List[ListItem], int]:
    items: List[ListItem] = []
    total = len(lines)
    index = start
    pattern = re.compile(r"^(\s*)(\d+)\.\s+(.*)$") if ordered else re.compile(r"^(\s*)[-+*]\s+(.*)$")
    current: ListItem | None = None

    while index < total:
        raw_line = lines[index]
        match = pattern.match(raw_line)
        stripped = raw_line.strip()

        if match:
            if current:
                items.append(current)
            indent_spaces = len(match.group(1))
            if ordered:
                marker = match.group(2) + "."
                text_group = 3
            else:
                marker = "-"
                text_group = 2
            text = match.group(text_group).strip()
            current = {"indent": indent_spaces, "marker": marker, "text": text}
            index += 1
            continue

        if stripped == "":
            if current:
                current["text"] = f"{current['text']} "
            index += 1
            continue

        continuation_match = re.match(r"^(\s+)(.+)$", raw_line)
        if continuation_match and current:
            continuation = continuation_match.group(2).strip()
            current["text"] = f"{current['text']} {continuation}"
            index += 1
            continue

        break

    if current:
        items.append(current)

    return items, index


def maybe_table(lines: Sequence[str], start: int) -> bool:
    if start + 1 >= len(lines):
        return False
    first = lines[start]
    second = lines[start + 1]
    if "|" not in first or "|" not in second:
        return False
    return is_table_separator(second)


def collect_table(lines: Sequence[str], start: int) -> Tuple[List[str], int]:
    collected: List[str] = []
    index = start
    while index < len(lines) and "|" in lines[index]:
        collected.append(lines[index])
        index += 1
    return collected, index


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    stripped = stripped.replace(":", "").replace(" ", "")
    return bool(stripped) and all(char == "-" for char in stripped)


def split_table_row(line: str) -> List[str]:
    working = line.strip()
    if working.startswith("|"):
        working = working[1:]
    if working.endswith("|"):
        working = working[:-1]
    return [cell.strip() for cell in working.split("|")]


# ---------- Inline parsing ----------


InlineSegment = Tuple[str, str]


def parse_inline(text: str, default_style: str = "normal") -> List[InlineSegment]:
    if not text:
        return []

    pattern = re.compile(r"(\*\*.*?\*\*)")
    parts = pattern.split(text)
    segments: List[InlineSegment] = []

    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            content = part[2:-2]
            if content:
                segments.append(("bold", content))
        else:
            segments.append((default_style, part))
    return segments


# ---------- Layout helpers ----------


def char_width(character: str, font_size: float) -> float:
    if character == " ":
        return font_size * 0.33
    if character in "il.:;,'`!|":
        return font_size * 0.28
    if character in "frtJ":
        return font_size * 0.40
    if character in "mwMW":
        return font_size * 0.85
    if character in "0123456789":
        return font_size * 0.55
    return font_size * 0.6


def text_width(text: str, font_size: float) -> float:
    return sum(char_width(ch, font_size) for ch in text)


def wrap_segments(
    segments: Sequence[InlineSegment], font_size: float, max_width: float
) -> List[List[InlineSegment]]:
    max_width = max(max_width, font_size * 4)
    lines: List[List[InlineSegment]] = []
    current: List[InlineSegment] = []
    current_width = 0.0

    for style, content in segments:
        tokens = _split_tokens(content)
        for token in tokens:
            if not token:
                continue

            token_width = text_width(token, font_size)
            is_space = token.isspace()

            if current and current_width + token_width > max_width:
                lines.append(_merge_segments(current))
                current = []
                current_width = 0.0
                if is_space:
                    continue

            if not current and is_space:
                continue

            if token_width > max_width and not is_space:
                split_lines = split_long_token(token, font_size, max_width)
                for part in split_lines:
                    part_width = text_width(part, font_size)
                    if current and current_width + part_width > max_width:
                        lines.append(_merge_segments(current))
                        current = []
                        current_width = 0.0
                    current.append((style, part))
                    current_width += part_width
                continue

            current.append((style, token))
            current_width += token_width

    if current:
        lines.append(_merge_segments(current))
    return lines


def _split_tokens(text: str) -> List[str]:
    return re.split(r"(\s+)", text)


def _merge_segments(segments: Sequence[InlineSegment]) -> List[InlineSegment]:
    merged: List[InlineSegment] = []
    for style, token in segments:
        if merged and merged[-1][0] == style:
            merged[-1] = (style, merged[-1][1] + token)
        else:
            merged.append((style, token))
    return merged


def split_long_token(token: str, font_size: float, max_width: float) -> List[str]:
    pieces: List[str] = []
    current = ""
    for char in token:
        if text_width(current + char, font_size) > max_width and current:
            pieces.append(current)
            current = char
        else:
            current += char
    if current:
        pieces.append(current)
    return pieces


# ---------- Layout composition ----------


class PDFComposer:
    def __init__(self) -> None:
        self.pages: List[List[Dict[str, object]]] = []
        self.current_page: List[Dict[str, object]] = []
        self.pages.append(self.current_page)
        self.y_position = PAGE_HEIGHT - MARGIN_TOP

    def ensure_space(self, height: float) -> None:
        if self.y_position - height < MARGIN_BOTTOM:
            self.new_page()

    def new_page(self) -> None:
        self.current_page = []
        self.pages.append(self.current_page)
        self.y_position = PAGE_HEIGHT - MARGIN_TOP

    def add_spacing(self, amount: float) -> None:
        self.y_position -= amount
        if self.y_position < MARGIN_BOTTOM:
            self.new_page()

    def add_text_line(self, x: float, segments: Sequence[Tuple[str, float, str]]) -> None:
        if not segments:
            return
        font_size = max(size for _, size, _ in segments)
        line_height = font_size * 1.32
        self.ensure_space(line_height)
        self.current_page.append(
            {
                "type": "text",
                "x": x,
                "y": self.y_position,
                "segments": [segment for segment in segments if segment[2]],
            }
        )
        self.y_position -= line_height

    def add_horizontal_rule(self) -> None:
        thickness = 0.8
        gap = 12
        y = self.y_position - gap
        self.ensure_space(gap + thickness + gap)
        y = self.y_position
        self.current_page.append(
            {
                "type": "line",
                "x1": MARGIN_LEFT,
                "x2": PAGE_WIDTH - MARGIN_RIGHT,
                "y": y,
                "width": thickness,
            }
        )
        self.y_position = y - gap

    def add_heading(self, level: int, text: str) -> None:
        sizes = {1: 22, 2: 18, 3: 16, 4: 14, 5: 13, 6: 12}
        size = sizes.get(level, 12)
        max_width = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        lines = wrap_segments(parse_inline(text, default_style="bold"), size, max_width)
        for line in lines:
            pdf_segments = [
                ("Helvetica-Bold" if style == "bold" else "Helvetica", size, token)
                for style, token in line
            ]
            self.add_text_line(MARGIN_LEFT, pdf_segments)
        self.add_spacing(size * 0.6)

    def add_paragraph(self, text: str) -> None:
        max_width = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        lines = wrap_segments(parse_inline(text), BASE_FONT_SIZE, max_width)
        for line in lines:
            pdf_segments = [
                ("Helvetica-Bold" if style == "bold" else "Helvetica", BASE_FONT_SIZE, token)
                for style, token in line
            ]
            self.add_text_line(MARGIN_LEFT, pdf_segments)
        self.add_spacing(BASE_FONT_SIZE * 0.6)

    def add_unordered_list(self, items: Sequence[ListItem]) -> None:
        bullet_char = "·"
        for item in items:
            indent_level = int(item.get("indent", 0)) // 2
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            max_width = (
                PAGE_WIDTH
                - MARGIN_LEFT
                - MARGIN_RIGHT
                - indent_level * 18
                - 14
            )
            lines = wrap_segments(parse_inline(text), LIST_FONT_SIZE, max_width)
            base_x = MARGIN_LEFT + indent_level * 18
            text_x = base_x + 12
            for line_index, line in enumerate(lines):
                pdf_segments = [
                    ("Helvetica-Bold" if style == "bold" else "Helvetica", LIST_FONT_SIZE, token)
                    for style, token in line
                ]
                line_height = LIST_FONT_SIZE * 1.32
                self.ensure_space(line_height)
                y = self.y_position
                if line_index == 0:
                    self.current_page.append(
                        {
                            "type": "text",
                            "x": base_x,
                            "y": y,
                            "segments": [("Helvetica", LIST_FONT_SIZE, bullet_char)],
                        }
                    )
                self.current_page.append(
                    {
                        "type": "text",
                        "x": text_x,
                        "y": y,
                        "segments": pdf_segments,
                    }
                )
                self.y_position -= line_height
            self.add_spacing(LIST_FONT_SIZE * 0.3)
        self.add_spacing(LIST_FONT_SIZE * 0.6)

    def add_ordered_list(self, items: Sequence[ListItem]) -> None:
        counters: Dict[int, int] = {}
        for item in items:
            indent_spaces = int(item.get("indent", 0))
            level = indent_spaces // 2
            counters[level] = counters.get(level, 0) + 1
            marker = str(item.get("marker")) if item.get("marker") else f"{counters[level]}."
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            marker_text = marker if marker.endswith(".") else f"{marker}."
            max_width = (
                PAGE_WIDTH
                - MARGIN_LEFT
                - MARGIN_RIGHT
                - level * 18
                - 18
            )
            lines = wrap_segments(parse_inline(text), LIST_FONT_SIZE, max_width)
            base_x = MARGIN_LEFT + level * 18
            text_x = base_x + 20
            for line_index, line in enumerate(lines):
                pdf_segments = [
                    ("Helvetica-Bold" if style == "bold" else "Helvetica", LIST_FONT_SIZE, token)
                    for style, token in line
                ]
                line_height = LIST_FONT_SIZE * 1.32
                self.ensure_space(line_height)
                y = self.y_position
                if line_index == 0:
                    self.current_page.append(
                        {
                            "type": "text",
                            "x": base_x,
                            "y": y,
                            "segments": [("Helvetica", LIST_FONT_SIZE, marker_text)],
                        }
                    )
                self.current_page.append(
                    {
                        "type": "text",
                        "x": text_x,
                        "y": y,
                        "segments": pdf_segments,
                    }
                )
                self.y_position -= line_height
            self.add_spacing(LIST_FONT_SIZE * 0.3)
        self.add_spacing(LIST_FONT_SIZE * 0.6)

    def add_table(self, header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        if not header or not rows:
            return
        intro = f"{header[0]}:"
        self.add_paragraph(f"**{intro}**")
        for row in rows:
            if not row:
                continue
            label = row[0].strip()
            details: List[str] = []
            for idx in range(1, min(len(header), len(row))):
                cell_value = row[idx].strip()
                if cell_value:
                    details.append(f"{header[idx]} {cell_value}")
            combined = f"{label} — " + "; ".join(details)
            self.add_unordered_list([{"indent": 2, "marker": "-", "text": combined}])


# ---------- PDF writing ----------


class PDFWriter:
    def __init__(self, pages: Sequence[Sequence[Dict[str, object]]]) -> None:
        self.pages = pages
        self.fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique"]

    def write(self, output_path: str) -> None:
        font_resource_names: Dict[str, str] = {}
        font_object_ids: Dict[str, int] = {}
        objects: List[bytes] = []

        for index, font_name in enumerate(self.fonts, start=1):
            resource_name = f"F{index}"
            font_dict = (
                f"<< /Type /Font /Subtype /Type1 /BaseFont /{font_name} "
                "/Encoding /WinAnsiEncoding >>"
            )
            font_resource_names[font_name] = resource_name
            font_object_ids[font_name] = len(objects) + 1
            objects.append(font_dict.encode("latin-1"))

        page_entries: List[int] = []
        page_count = len(self.pages)
        pages_obj_id = len(objects) + page_count * 2 + 1
        font_entries = " ".join(
            f"/{font_resource_names[name]} {font_object_ids[name]} 0 R"
            for name in self.fonts
        )

        for page in self.pages:
            content_stream = self._build_page_stream(page, font_resource_names)
            content_object = (
                f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
                + content_stream
                + b"\nendstream"
            )
            content_obj_id = len(objects) + 1
            objects.append(content_object)

            page_dict = (
                f"<< /Type /Page /Parent {pages_obj_id} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << {font_entries} >> >> "
                f"/Contents {content_obj_id} 0 R >>"
            )
            page_obj_id = len(objects) + 1
            page_entries.append(page_obj_id)
            objects.append(page_dict.encode("latin-1"))

        kids = " ".join(f"{obj_id} 0 R" for obj_id in page_entries)
        pages_dict = f"<< /Type /Pages /Count {len(page_entries)} /Kids [ {kids} ] >>"
        objects.append(pages_dict.encode("latin-1"))
        catalog_obj_id = len(objects) + 1
        catalog_dict = f"<< /Type /Catalog /Pages {pages_obj_id} 0 R >>"
        objects.append(catalog_dict.encode("latin-1"))

        with open(output_path, "wb") as pdf:
            pdf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            offsets: List[int] = []
            for obj_index, obj in enumerate(objects, start=1):
                offsets.append(pdf.tell())
                pdf.write(f"{obj_index} 0 obj\n".encode("latin-1"))
                pdf.write(obj)
                if not obj.endswith(b"\n"):
                    pdf.write(b"\n")
                pdf.write(b"endobj\n")
            xref_position = pdf.tell()
            pdf.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
            pdf.write(b"0000000000 65535 f \n")
            for offset in offsets:
                pdf.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
            pdf.write(
                (
                    "trailer\n"
                    f"<< /Size {len(objects) + 1} /Root {catalog_obj_id} 0 R >>\n"
                    "startxref\n"
                    f"{xref_position}\n"
                    "%%EOF\n"
                ).encode("latin-1")
            )

    def _build_page_stream(
        self, page: Sequence[Dict[str, object]], font_resource_names: Dict[str, str]
    ) -> bytes:
        parts: List[str] = []
        for entry in page:
            entry_type = entry.get("type")
            if entry_type == "text":
                x = float(entry.get("x", MARGIN_LEFT))
                y = float(entry.get("y", PAGE_HEIGHT - MARGIN_TOP))
                segments = entry.get("segments", [])
                if not isinstance(segments, Iterable):
                    continue
                parts.append("BT")
                parts.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm")
                current_font = None
                for segment in segments:
                    if not isinstance(segment, (list, tuple)) or len(segment) != 3:
                        continue
                    font_name, size, text = segment
                    font_name = str(font_name)
                    size = float(size)
                    text = str(text)
                    resource = font_resource_names.get(font_name, "F1")
                    font_key = (resource, size)
                    if current_font != font_key:
                        parts.append(f"/{resource} {size:.2f} Tf")
                        current_font = font_key
                    escaped = escape_text(text)
                    if escaped:
                        parts.append(f"({escaped}) Tj")
                parts.append("ET")
            elif entry_type == "line":
                width = float(entry.get("width", 1))
                x1 = float(entry.get("x1", MARGIN_LEFT))
                x2 = float(entry.get("x2", PAGE_WIDTH - MARGIN_RIGHT))
                y = float(entry.get("y", self._default_line_y()))
                parts.append(f"{width:.2f} w")
                parts.append(f"{x1:.2f} {y:.2f} m {x2:.2f} {y:.2f} l S")
        return ("\n".join(parts)).encode("latin-1")

    @staticmethod
    def _default_line_y() -> float:
        return PAGE_HEIGHT - MARGIN_TOP - 20


# ---------- Utilities ----------


def escape_text(text: str) -> str:
    safe = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    # Convert to latin-1 friendly range
    return safe.encode("latin-1", "replace").decode("latin-1")


def build_pdf_from_markdown(input_path: str, output_path: str) -> None:
    markdown_text = read_text(input_path)
    blocks = parse_blocks(markdown_text)
    composer = PDFComposer()
    for block in blocks:
        block_type = block.get("type")
        if block_type == "heading":
            composer.add_heading(int(block.get("level", 1)), str(block.get("text", "")))
        elif block_type == "paragraph":
            composer.add_paragraph(str(block.get("text", "")))
        elif block_type == "ul":
            composer.add_unordered_list(block.get("items", []))  # type: ignore[arg-type]
        elif block_type == "ol":
            composer.add_ordered_list(block.get("items", []))  # type: ignore[arg-type]
        elif block_type == "hr":
            composer.add_horizontal_rule()
        elif block_type == "table":
            composer.add_table(
                block.get("header", []),  # type: ignore[arg-type]
                block.get("rows", []),  # type: ignore[arg-type]
            )
    pages = [page for page in composer.pages if page]
    if not pages:
        pages = [[]]
    writer = PDFWriter(pages)
    writer.write(output_path)


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        print("Usage: convert_markdown_to_pdf.py <input> <output>", file=sys.stderr)
        return 1
    input_path, output_path = argv[1], argv[2]
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    build_pdf_from_markdown(input_path, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
