"""
Code Comment & Docstring Humanizer Engine.
Language-agnostic code parser and humanizer supporting Python, C/C++, Java,
C#, JavaScript/TypeScript, Go, Rust, SQL, Shell, and HTML.
Strictly isolates natural language comments and docstrings while preserving
executable code syntax, variable names, keywords, and strings 100% intact.
"""

import re
from typing import Dict, List, Optional, Tuple


class CodeCommentHumanizer:
    """
    Parses source code files, identifies comments and docstrings,
    and humanizes their tone across Beginner, Intermediate, and Senior/Expert developer personas
    without ever touching executable code logic.
    """

    PERSONAS = {
        "beginner": {
            r"\binstantiates?\b": "sets up",
            r"\binitializes?\b": "starts up",
            r"\bevaluates?\b": "checks",
            r"\bexecutes?\b": "runs",
            r"\bpersists?\b": "saves",
            r"\bretrieves?\b": "gets",
            r"\biterates? through\b": "loops through",
            r"\bterminates?\b": "stops",
            r"\bdetermines?\b": "figures out",
            r"\boptimizes?\b": "speeds up",
            r"\bvalidates?\b": "makes sure it's good",
            r"\bparameters?\b": "inputs",
            r"\butilizes?\b": "uses",
        },
        "intermediate": {
            r"\bsets up\b": "initializes",
            r"\bstops\b": "terminates",
            r"\bgets\b": "retrieves",
            r"\bfigures out\b": "determines",
            r"\buses\b": "applies",
            r"\bmakes sure\b": "verifies",
            r"\blooks at\b": "inspects",
            r"\bcleans up\b": "sanitizes",
        },
        "expert": {
            r"\bchecks\b": "evaluates invariant condition for",
            r"\bloops through\b": "executes deterministic traversal over",
            r"\bsaves\b": "serializes state to persistent storage",
            r"\bruns\b": "dispatches execution pipeline for",
            r"\buses\b": "leverages algorithmic paradigm of",
            r"\bgets\b": "queries and resolves reference to",
            r"\bstarts up\b": "bootstraps runtime context for",
            r"\bcleans\b": "enforces sanitization protocol on",
            r"\bhandles\b": "manages asynchronous edge cases for",
        }
    }

    # Universal phrase cleanups for robotic AI comments ("This function does X")
    ROBOTIC_COMMENT_PATTERNS = [
        (r"^(?:#|//|--)\s*(?:This function|This method|This class|This script)\s+(?:is responsible for|aims to|serves to|delves into)\s+", "# "),
        (r"^(?:#|//|--)\s*(?:Please note that|It is important to note that|It should be noted that)\s+", "# Note: "),
        (r"^(?:#|//|--)\s*In order to\s+", "# To "),
        (r"^(?:#|//|--)\s*Plays a crucial role in\s+", "# Essential for "),
    ]

    def __init__(self):
        pass

    def humanize_comment_text(self, comment_text: str, persona: str = "intermediate") -> str:
        """
        Rewrites a comment's prose according to the selected developer persona.
        """
        processed = comment_text

        # 1. Clean robotic AI phrasing
        for pat, repl in self.ROBOTIC_COMMENT_PATTERNS:
            processed = re.sub(pat, repl, processed, flags=re.IGNORECASE)

        # 2. Apply persona vocabulary
        mapping = self.PERSONAS.get(persona.lower(), self.PERSONAS["intermediate"])
        for pat, repl in mapping.items():
            processed = re.sub(pat, repl, processed, flags=re.IGNORECASE)

        return processed

    def process_code(self, code: str, language: str = "python", persona: str = "intermediate") -> Dict[str, any]:
        """
        Parses source code, humanizes comments in-place, and returns the modified code
        with 100% executable integrity.
        """
        if not code.strip():
            return {"code": code, "comments_modified": 0, "language": language}

        lines = code.split("\n")
        modified_lines = []
        comment_count = 0

        # Language-specific single-line comment prefixes
        single_prefixes = ["#"] if language.lower() in ["python", "sh", "bash", "shell"] else \
                          ["--"] if language.lower() in ["sql", "lua"] else \
                          ["//"]

        in_multiline_python = False
        python_delim = ""
        in_c_multiline = False

        for line in lines:
            stripped = line.strip()

            # Handle Python docstrings (""" or ''')
            if language.lower() == "python":
                if not in_multiline_python:
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        delim = '"""' if stripped.startswith('"""') else "'''"
                        # Check single-line docstring
                        if stripped.count(delim) >= 2 and len(stripped) > 6:
                            content = stripped[3:-3]
                            humanized = self.humanize_comment_text(content, persona)
                            indent = line[:len(line) - len(line.lstrip())]
                            modified_lines.append(f"{indent}{delim}{humanized}{delim}")
                            comment_count += 1
                            continue
                        else:
                            in_multiline_python = True
                            python_delim = delim
                            modified_lines.append(line)
                            continue
                else:
                    if python_delim in stripped:
                        in_multiline_python = False
                        modified_lines.append(line)
                        continue
                    else:
                        # Inside multiline docstring
                        indent = line[:len(line) - len(line.lstrip())]
                        humanized = self.humanize_comment_text(stripped, persona)
                        modified_lines.append(f"{indent}{humanized}")
                        comment_count += 1
                        continue

            # Handle C-style multiline comments (/* ... */)
            if not in_c_multiline:
                if "/*" in line and "*/" in line:
                    start_idx = line.find("/*")
                    end_idx = line.find("*/", start_idx)
                    prefix = line[:start_idx + 2]
                    content = line[start_idx + 2:end_idx]
                    suffix = line[end_idx:]
                    humanized = self.humanize_comment_text(content, persona)
                    modified_lines.append(f"{prefix}{humanized}{suffix}")
                    comment_count += 1
                    continue
                elif "/*" in line:
                    in_c_multiline = True
                    modified_lines.append(line)
                    continue
            else:
                if "*/" in line:
                    in_c_multiline = False
                    modified_lines.append(line)
                    continue
                else:
                    # Inside C multiline comment
                    indent = line[:len(line) - len(line.lstrip())]
                    humanized = self.humanize_comment_text(stripped, persona)
                    modified_lines.append(f"{indent}{humanized}")
                    comment_count += 1
                    continue

            # Handle single-line comments
            matched_prefix = None
            for pfx in single_prefixes:
                # Find comment prefix not inside quotes
                comment_idx = self._find_comment_char_outside_quotes(line, pfx)
                if comment_idx != -1:
                    matched_prefix = pfx
                    break

            if matched_prefix and comment_idx != -1:
                code_part = line[:comment_idx]
                comment_part = line[comment_idx + len(matched_prefix):]
                humanized = self.humanize_comment_text(comment_part, persona)
                modified_lines.append(f"{code_part}{matched_prefix} {humanized.strip()}")
                comment_count += 1
            else:
                modified_lines.append(line)

        return {
            "code": "\n".join(modified_lines),
            "comments_modified": comment_count,
            "language": language,
            "status": "success"
        }

    def _find_comment_char_outside_quotes(self, line: str, comment_char: str) -> int:
        """
        Scans a line of code character-by-character to locate a comment delimiter
        strictly outside of single or double quotation marks.
        """
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        target_len = len(comment_char)

        for i in range(len(line)):
            ch = line[i]

            if escape_next:
                escape_next = False
                continue

            if ch == "\\":
                escape_next = True
                continue

            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                continue

            if ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                continue

            if not in_single_quote and not in_double_quote:
                if line[i:i + target_len] == comment_char:
                    return i

        return -1
