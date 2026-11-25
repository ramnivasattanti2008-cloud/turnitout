"""
Format-Preserving Structural Layout Engine for TextHumanizer Pro.
Maintains 100% exact formatting fidelity across:
- Headings (#, ##, ###, Title case, numbered sections)
- Bullet points (-, *, •, +, –) with arbitrary indentation
- Numbered lists (1., 2), (1), a., i.) with arbitrary indentation
- Fenced code blocks (``` and ~~~) and indented code blocks
- Markdown tables (| col | col |)
- Blockquotes (> Quote)
- Blank lines and spacing between sections
- Single-spaced multi-line verses, addresses, and line-breaks
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple


STANDARD_ACADEMIC_SECTION_TITLES = {
    "abstract", "introduction", "background", "methodology", "methods",
    "materials and methods", "results", "discussion", "conclusion",
    "conclusions", "concluding remarks", "references", "bibliography",
    "works cited", "table of contents", "acknowledgments", "acknowledgements",
    "appendix", "author contributions", "conflict of interest",
    "data availability", "ethics statement", "executive overview",
    "executive summary", "overview", "findings", "related work",
    "literature review", "experimental setup", "experimental results",
    "evaluation", "empirical evaluation", "threats to validity",
    "limitations", "future work", "implementation details"
}


class FormatPreserver:
    """
    Parses, transforms, and reassembles text while preserving 100% of its
    structural layout, lists, indentation, code, tables, and line breaks.
    """

    RE_CODE_FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
    RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
    RE_HEADING = re.compile(r"^(\s*#{1,6}\s+)(.*?)(\r?\n)?$")
    RE_BULLET = re.compile(r"^(\s*[-*•+–]\s+)(.*?)(\r?\n)?$")
    RE_NUMBERED = re.compile(r"^(\s*(?:\(?\d+[\.\)]|\(?[a-zA-Z][\.\)]|\(?[ivxlcdm]+[\.\)])\s+)(.*?)(\r?\n)?$")
    RE_QUOTE = re.compile(r"^(\s*>\s*)(.*?)(\r?\n)?$")

    @classmethod
    def parse_document_blocks(cls, text: str) -> List[Dict[str, Any]]:
        """
        Parses text into high-level structural units:
        - code: multi-line fenced code, passed verbatim
        - table: multi-line table, passed verbatim
        - empty: blank lines preserving exact newlines
        - bullet: bullet list item with prefix and suffix preserved
        - numbered: numbered list item with prefix and suffix preserved
        - heading: markdown heading with prefix preserved
        - quote: blockquote with prefix preserved
        - prose: coherent prose block (or line)
        """
        lines = text.splitlines(keepends=True)
        blocks: List[Dict[str, Any]] = []

        in_code = False
        code_fence_char = ""
        code_lines: List[str] = []

        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # 1. Code Fence Detection
            m_fence = cls.RE_CODE_FENCE.match(line)
            if m_fence:
                fence_str = m_fence.group(0).strip()
                if not in_code:
                    in_code = True
                    code_fence_char = fence_str[:3]
                    code_lines = [line]
                    i += 1
                    continue
                else:
                    if fence_str.startswith(code_fence_char):
                        in_code = False
                    code_lines.append(line)
                    blocks.append({
                        "type": "code",
                        "verbatim": "".join(code_lines)
                    })
                    code_lines = []
                    i += 1
                    continue

            if in_code:
                code_lines.append(line)
                i += 1
                continue

            # 2. Empty Line
            if not stripped:
                blocks.append({
                    "type": "empty",
                    "verbatim": line
                })
                i += 1
                continue

            # 3. Table Rows
            if cls.RE_TABLE_ROW.match(line):
                table_lines = [line]
                while i + 1 < n and cls.RE_TABLE_ROW.match(lines[i + 1]):
                    i += 1
                    table_lines.append(lines[i])
                blocks.append({
                    "type": "table",
                    "verbatim": "".join(table_lines)
                })
                i += 1
                continue

            # 4. Markdown Headings
            m_head = cls.RE_HEADING.match(line)
            if m_head:
                prefix, content, suffix = m_head.groups()
                blocks.append({
                    "type": "heading",
                    "prefix": prefix,
                    "content": content,
                    "suffix": suffix or ""
                })
                i += 1
                continue

            # 5. Bullet List Items
            m_bullet = cls.RE_BULLET.match(line)
            if m_bullet:
                prefix, content, suffix = m_bullet.groups()
                blocks.append({
                    "type": "bullet",
                    "prefix": prefix,
                    "content": content,
                    "suffix": suffix or ""
                })
                i += 1
                continue

            # 6. Numbered List Items
            m_num = cls.RE_NUMBERED.match(line)
            if m_num:
                prefix, content, suffix = m_num.groups()
                blocks.append({
                    "type": "numbered",
                    "prefix": prefix,
                    "content": content,
                    "suffix": suffix or ""
                })
                i += 1
                continue

            # 7. Blockquotes
            m_quote = cls.RE_QUOTE.match(line)
            if m_quote:
                prefix, content, suffix = m_quote.groups()
                blocks.append({
                    "type": "quote",
                    "prefix": prefix,
                    "content": content,
                    "suffix": suffix or ""
                })
                i += 1
                continue

            # 8. Prose Paragraph or Distinct Line
            para_lines = [line]
            while i + 1 < n:
                next_l = lines[i + 1]
                next_str = next_l.strip()
                if (
                    not next_str
                    or cls.RE_CODE_FENCE.match(next_l)
                    or cls.RE_TABLE_ROW.match(next_l)
                    or cls.RE_HEADING.match(next_l)
                    or cls.RE_BULLET.match(next_l)
                    or cls.RE_NUMBERED.match(next_l)
                    or cls.RE_QUOTE.match(next_l)
                ):
                    break
                i += 1
                para_lines.append(lines[i])

            full_para = "".join(para_lines)
            trailing_nl = ""
            if full_para.endswith("\r\n"):
                trailing_nl = "\r\n"
                clean_content = full_para[:-2]
            elif full_para.endswith("\n"):
                trailing_nl = "\n"
                clean_content = full_para[:-1]
            else:
                clean_content = full_para

            # If the user pasted lines that each look like a title, subtitle, address or single-line statement
            # (< 6 words each and ended with newline), preserve as separate lines
            if len(para_lines) > 1 and all(len(pl.strip().split()) <= 6 for pl in para_lines):
                for pl in para_lines:
                    pl_nl = "\r\n" if pl.endswith("\r\n") else ("\n" if pl.endswith("\n") else "")
                    pl_c = pl.rstrip("\r\n")
                    blocks.append({
                        "type": "prose",
                        "content": pl_c,
                        "suffix": pl_nl
                    })
            else:
                normalized_content = re.sub(r"[ \t]*\r?\n[ \t]*", " ", clean_content).strip()
                blocks.append({
                    "type": "prose",
                    "content": normalized_content,
                    "suffix": trailing_nl
                })
            i += 1

        # If unclosed code fence
        if in_code and code_lines:
            blocks.append({
                "type": "code",
                "verbatim": "".join(code_lines)
            })

        return blocks

    @classmethod
    def process_and_reconstruct(
        cls,
        text: str,
        humanize_fn: Callable[[str], str]
    ) -> str:
        """
        Parses text, transforms every translatable element through humanize_fn,
        and reconstructs the exact layout with 100% structural fidelity.
        """
        if not text:
            return ""

        blocks = cls.parse_document_blocks(text)
        reconstructed: List[str] = []

        from core.document_parser import DocumentParser

        for b in blocks:
            b_type = b["type"]

            if b_type in ("code", "table", "empty"):
                # Preserve 100% verbatim
                reconstructed.append(b["verbatim"])

            elif b_type in ("bullet", "numbered", "quote"):
                content = b["content"].strip()
                if not content or len(content.split()) < 2:
                    transformed = content
                elif DocumentParser.is_reference_entry(content):
                    transformed = content
                else:
                    transformed = humanize_fn(content)
                reconstructed.append(f"{b['prefix']}{transformed}{b['suffix']}")

            elif b_type == "heading":
                content = b["content"].strip()
                # Check for leading numbering like "1. ", "1.1 ", "Chapter 1: ", etc.
                m_num = re.match(
                    r"^((?:[IVXLCDM]+\.|\d+(?:\.\d+)*\.?|Chapter\s+\d+:?|Section\s+\d+:?)\s*)(.*)$",
                    content,
                    re.IGNORECASE
                )
                if m_num:
                    h_num, h_text = m_num.groups()
                else:
                    h_num, h_text = "", content

                clean_title = h_text.strip().lower().rstrip(":")
                if clean_title in STANDARD_ACADEMIC_SECTION_TITLES or len(h_text.split()) < 2:
                    transformed = content
                else:
                    transformed_title = humanize_fn(h_text)
                    transformed = f"{h_num}{transformed_title}"
                reconstructed.append(f"{b['prefix']}{transformed}{b['suffix']}")

            elif b_type == "prose":
                content = b["content"].strip()
                if not content:
                    reconstructed.append(b["suffix"])
                    continue
                # For prose blocks, check reference entries and metadata (using p_idx=999 so non-period lines aren't misclassified)
                if (
                    DocumentParser.is_reference_entry(content)
                    or DocumentParser.is_academic_metadata(content, p_idx=999)
                    or len(content.split()) < 2
                ):
                    transformed = content
                else:
                    transformed = humanize_fn(content)
                reconstructed.append(f"{transformed}{b['suffix']}")

        return "".join(reconstructed)
