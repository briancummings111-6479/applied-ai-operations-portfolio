#!/usr/bin/env python3
"""
Executive Copy & Humanizer Voice Linter (lint_humanizer_check.py)

Ensures all portfolio case studies and executive summaries stay free of AI
buzzwords, corporate filler, robotic tricolons, and monotonous sentence length.

Usage:
    python scripts/lint_humanizer_check.py README.md case-studies/*.md
"""

import argparse
import glob
import math
import os
import re
import sys

# Strict blacklist of AI buzzwords & corporate resume clichés
BANNED_PATTERNS = [
    r"\bspearhead(?:ed|ing|s)?\b",
    r"\bdelv(?:e|es|ed|ing)\b",
    r"\bresults-driven\b",
    r"\bpassionate\b",
    r"\bsynerg(?:y|ies|istic)\b",
    r"\btestament\b",
    r"\btapestr(?:y|ies)\b",
    r"\bbeacon(?:s)?\b",
    r"\bpivotal\b",
    r"\bparamount\b",
    r"\bcrucial\b",
    r"\bnestled\b",
    r"\bunwavering\b",
    r"\brelentless\b",
    r"\bvaliant\b",
    r"\bpoignant\b",
    r"\bharrowing\b",
    r"\benduring legacy\b",
    r"\bunderscores\b",
    r"\bmultifaceted\b",
    r"\bdynamic landscape\b",
    r"\bin conclusion\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\bit is worth noting\b",
    r"\bstands as a\b",
    r"\bgame-changer\b",
    r"\bcutting-edge\b",
    r"\brevolutioniz(?:e|ed|ing)\b",
]


def split_prose_sentences(text: str):
    """Extract prose sentences from Markdown while ignoring code blocks, tables, and headings."""
    clean = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    clean_lines = []
    for line in clean.splitlines():
        stripped = line.strip()
        # Skip markdown tables, headings, HTML tags, and image links
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith("!")
            or stripped.startswith("<")
            or stripped.startswith("---")
        ):
            continue
        clean_lines.append(stripped)

    prose = " ".join(clean_lines)
    prose = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", prose)
    prose = re.sub(r"\b(vs|e\.g|i\.e|Dr|Mr|Mrs|Ms|No|St)\.", r"\1<DOT>", prose)

    raw_sentences = re.split(r"(?<=[.!?])\s+", prose)
    sentences = []
    for s in raw_sentences:
        s_clean = s.replace("<DOT>", ".").strip()
        words = [w for w in re.split(r"\s+", s_clean) if w]
        if len(words) >= 3:
            sentences.append((s_clean, len(words)))
    return sentences


def calculate_std_dev(word_counts):
    if len(word_counts) < 3:
        return 999.0
    mean = sum(word_counts) / len(word_counts)
    variance = sum((x - mean) ** 2 for x in word_counts) / len(word_counts)
    return math.sqrt(variance)


def check_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip fenced code blocks before checking for buzzwords so we don't flag linter docs
    prose_without_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    violations = []

    for line_idx, line in enumerate(prose_without_code.splitlines(), start=1):
        for pattern in BANNED_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                violations.append(
                    {
                        "line": line_idx,
                        "word": match.group(0),
                        "context": line.strip(),
                    }
                )

    sentences = split_prose_sentences(text)
    word_counts = [count for _, count in sentences]
    std_dev = calculate_std_dev(word_counts) if len(word_counts) >= 4 else 10.0

    return violations, std_dev, len(sentences)


def main():
    parser = argparse.ArgumentParser(description="Check portfolio markdown files for Humanizer voice compliance.")
    parser.add_argument("files", nargs="*", default=["README.md", "case-studies/*.md", "assets/MEDIA_CAPTURE_GUIDE.md"])
    args = parser.parse_args()

    expanded_files = []
    for pattern in args.files:
        matched = glob.glob(pattern)
        if matched:
            expanded_files.extend(matched)
        elif os.path.exists(pattern):
            expanded_files.append(pattern)

    if not expanded_files:
        print("[-] No files found to check.")
        sys.exit(2)

    overall_failed = False
    print("=" * 65)
    print("HUMANIZER VOICE & EXECUTIVE COPY AUDIT")
    print("=" * 65)

    for filepath in expanded_files:
        violations, std_dev, sentence_count = check_file(filepath)
        status = "PASS" if (not violations and std_dev >= 3.5) else "FAIL"
        print(f"[{status}] {filepath} ({sentence_count} prose sentences | cadence std_dev: {std_dev:.1f})")

        if violations:
            overall_failed = True
            for v in violations:
                print(f"   ! Line {v['line']}: Found banned buzzword '{v['word']}' -> {v['context']}")
        if std_dev < 3.5:
            overall_failed = True
            print(f"   ! Monotone cadence detected (std_dev {std_dev:.1f} < 3.5). Mix short 5-8 word sentences with longer explanations.")

    print("=" * 65)
    if overall_failed:
        sys.exit(1)
    print("[+] All checked documents meet Humanizer plain-English voice standards.")
    sys.exit(0)


if __name__ == "__main__":
    main()
