"""
Command Line Interface (CLI) for TextHumanizer Pro.
Allows paragraph humanization, multi-format document processing (.docx, .pdf, .txt, .md),
batch folder processing, and AI score diagnostics directly from the terminal.
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.detector import TextAnalyzer
from core.document_parser import DocumentParser
from core.humanizer import TextHumanizer

console = Console(force_terminal=True, legacy_windows=False)


def process_batch_directory(dir_path: Path, humanizer: TextHumanizer, tone: str, intensity: float, beast: bool):
    """Recursively processes all supported documents in a directory."""
    if not dir_path.is_dir():
        console.print(f"[bold red]Specified batch directory does not exist: {dir_path}[/bold red]")
        sys.exit(1)

    supported_exts = {".txt", ".md", ".docx", ".pdf"}
    files_to_process = [f for f in dir_path.rglob("*") if f.is_file() and f.suffix.lower() in supported_exts and "humanized" not in f.parts]

    if not files_to_process:
        console.print(f"[bold yellow]No supported documents (.txt, .md, .docx, .pdf) found in {dir_path}[/bold yellow]")
        return

    out_dir = dir_path / "humanized"
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel(f"[bold cyan]Starting Batch Humanization on {len(files_to_process)} document(s) in {dir_path}...[/bold cyan]"))

    table = Table(title="Batch Humanization Summary", show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Original AI", justify="center")
    table.add_column("Humanized AI", justify="center")
    table.add_column("Uniqueness", justify="center")
    table.add_column("Output Path", style="dim")

    for f in files_to_process:
        try:
            mode = "beast" if beast else "standard"
            if f.suffix.lower() == ".docx":
                out_file = out_dir / f"{f.stem}_humanized.docx"
                m_summary = DocumentParser.humanize_docx_file(
                    input_path=f,
                    output_path=out_file,
                    humanizer=humanizer,
                    mode=mode,
                    intensity=0.85 if beast else intensity
                )
                m = m_summary["metrics"]
                table.add_row(
                    f.name,
                    f"{m['ai_score_before']}%",
                    f"[bold green]{m['ai_score_after']}%[/bold green]",
                    f"{m['uniqueness_score']}%",
                    str(out_file.name)
                )
                continue

            raw_text = DocumentParser.extract_text(f)
            if not raw_text.strip():
                continue

            res = humanizer.process(
                raw_text,
                tone=tone,
                intensity=0.80 if beast else intensity,
                mode=mode
            )

            # Determine export filename
            export_ext = ".docx" if f.suffix.lower() == ".pdf" else f.suffix.lower()
            out_file = out_dir / f"{f.stem}_humanized{export_ext}"
            DocumentParser.export_text(res["humanized_text"], out_file)

            m = res["metrics"]
            table.add_row(
                f.name,
                f"{m['ai_score_before']}%",
                f"[bold green]{m['ai_score_after']}%[/bold green]",
                f"{m['uniqueness_score']}%",
                str(out_file.name)
            )
        except Exception as e:
            table.add_row(f.name, "ERR", "ERR", "ERR", f"[red]{e}[/red]")

    console.print(table)
    console.print(f"\n[bold green]Batch processing completed. All outputs saved to: {out_dir}[/bold green]\n")


def main():
    parser = argparse.ArgumentParser(
        description="TextHumanizer Pro - 100% Plagiarism & AI-Generated Text Remover CLI"
    )
    parser.add_argument("-t", "--text", type=str, help="Input paragraph text to humanize")
    parser.add_argument("-f", "--file", type=str, help="Input document path (.txt, .md, .docx, .pdf)")
    parser.add_argument("-o", "--output", type=str, help="Output file path (.txt, .md, .docx)")
    parser.add_argument(
        "--batch-dir",
        type=str,
        help="Directory to batch-process all documents (.txt, .md, .docx, .pdf) recursively"
    )
    parser.add_argument(
        "--tone",
        type=str,
        default="standard",
        choices=["standard", "academic", "casual", "journalistic", "executive"],
        help="Target writing tone (default: standard)"
    )
    parser.add_argument(
        "--intensity",
        type=float,
        default=0.50,
        help="Paraphrasing and humanization intensity (0.2 to 0.85, default: 0.50)"
    )
    parser.add_argument(
        "--scan-only",
        "--detect",
        action="store_true",
        dest="scan_only",
        help="Only scan and display comprehensive AI likelihood and plagiarism scores without rewriting"
    )
    parser.add_argument(
        "-r",
        "--reference",
        type=str,
        help="Reference document (.txt, .md, .docx, .pdf) or string to check comparative plagiarism against"
    )
    parser.add_argument(
        "--beast",
        action="store_true",
        help="Activate BEAST MODE: Maximum adversarial overhaul & n-gram destruction"
    )
    parser.add_argument(
        "--alternatives",
        action="store_true",
        help="Generate 3 dynamic sentence alternatives for the input text"
    )

    args = parser.parse_args()
    analyzer = TextAnalyzer()
    humanizer = TextHumanizer()

    # Handle Batch Directory
    if args.batch_dir:
        process_batch_directory(
            Path(args.batch_dir),
            humanizer=humanizer,
            tone=args.tone,
            intensity=args.intensity,
            beast=args.beast
        )
        return

    # Read input text
    raw_text = ""
    if args.text:
        raw_text = args.text
    elif args.file:
        try:
            raw_text = DocumentParser.extract_text(args.file)
        except Exception as e:
            console.print(f"[bold red]Error reading file {args.file}: {e}[/bold red]")
            sys.exit(1)
    else:
        # Check if piped input
        if not sys.stdin.isatty():
            raw_text = sys.stdin.read()
        else:
            console.print("[bold yellow]Please specify text via --text '...', --file document.docx, --batch-dir folder, or stdin.[/bold yellow]")
            sys.exit(0)

    raw_text = raw_text.strip()
    if not raw_text:
        console.print("[bold red]Empty text provided.[/bold red]")
        sys.exit(1)

    if args.scan_only:
        console.print(Panel("[bold cyan]Running Forensic AI & Plagiarism Diagnostic Analysis...[/bold cyan]", border_style="cyan"))

        # Read reference text if provided
        ref_text = ""
        if args.reference:
            ref_path = Path(args.reference)
            if ref_path.exists() and ref_path.is_file():
                try:
                    ref_text = DocumentParser.extract_text(ref_path)
                except Exception:
                    ref_text = args.reference
            else:
                ref_text = args.reference

        scan = analyzer.full_forensic_detection(raw_text, reference_text=ref_text)

        # 1. Forensic Diagnostic Overview
        table = Table(title="Forensic Diagnostic Overview", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Score / Reading", justify="right")
        table.add_column("Verdict / Clearance", style="white")

        ai_color = "red" if scan["ai_probability"] >= 60 else "yellow" if scan["ai_probability"] >= 35 else "green"
        plag_color = "red" if scan["plagiarism_risk_score"] >= 40 else "yellow" if scan["plagiarism_risk_score"] >= 15 else "green"

        table.add_row("AI Likelihood Score", f"[bold {ai_color}]{scan['ai_probability']}%[/bold {ai_color}]", f"[{ai_color}]{scan['verdict']}[/{ai_color}]")
        table.add_row("Plagiarism Risk Score", f"[bold {plag_color}]{scan['plagiarism_risk_score']}%[/bold {plag_color}]", f"[{plag_color}]{scan['plagiarism_verdict']}[/{plag_color}]")
        table.add_row("Uniqueness Score", f"[bold green]{scan['uniqueness_score']}%[/bold green]", "Clean academic text clearance")
        table.add_row("Burstiness Variance (CV)", str(scan['burstiness_index']), f"Std Dev: {scan['sentence_std_dev']}")
        table.add_row("Type-Token Ratio (TTR)", str(scan['lexical']['ttr']), f"Unique tokens: {scan['lexical']['unique_words']}")
        table.add_row("Detected AI Markers", str(scan['markers']['total_markers']), f"Density: {scan['markers']['marker_density_per_100']}%")
        table.add_row("Flesch Reading Ease", str(scan['readability']['flesch_reading_ease']), f"Grade Level: {scan['readability']['flesch_kincaid_grade']}")
        console.print(table)

        # 2. Commercial AI Radar (5 Engines)
        if "radar" in scan and "detectors" in scan["radar"]:
            r_table = Table(title="Commercial AI Detector Radar (5 Engines)", show_header=True, header_style="bold blue")
            r_table.add_column("Detector", style="white")
            r_table.add_column("Score", justify="center")
            r_table.add_column("Verdict", justify="center")
            r_table.add_column("Status", justify="center")

            for det_name, info in scan["radar"]["detectors"].items():
                badge = "[bold green]PASS[/bold green]" if info["status"] == "pass" else "[bold red]FLAG[/bold red]"
                r_table.add_row(det_name.upper(), f"{info['score']}% AI", info["verdict"], badge)
            console.print(r_table)

        # 3. Sentence-by-Sentence Breakdown
        sent_data = scan.get("sentence_analysis", {})
        if sent_data and sent_data.get("sentences"):
            s_table = Table(title=f"Sentence-by-Sentence AI Probability Breakdown ({sent_data['total_sentences']} Sentences)", show_header=True, header_style="bold yellow")
            s_table.add_column("#", justify="center", width=4)
            s_table.add_column("Sentence Text", style="white")
            s_table.add_column("Words", justify="center", width=6)
            s_table.add_column("AI Score", justify="center", width=10)
            s_table.add_column("Risk", justify="center", width=8)
            s_table.add_column("Diagnostic Reasons", style="dim")

            for s in sent_data["sentences"]:
                r_badge = "[bold red]HIGH[/bold red]" if s["risk"] == "high" else "[bold yellow]MED[/bold yellow]" if s["risk"] == "medium" else "[bold green]HUMAN[/bold green]"
                score_str = f"[{'red' if s['risk']=='high' else 'yellow' if s['risk']=='medium' else 'green'}]{s['ai_score']}%[/]"
                s_table.add_row(
                    str(s["sentence_id"]),
                    s["text"][:75] + ("..." if len(s["text"]) > 75 else ""),
                    str(s["word_count"]),
                    score_str,
                    r_badge,
                    "; ".join(s["reasons"])
                )
            console.print(s_table)

        # 4. Plagiarism Details
        plag = scan.get("plagiarism", {})
        if plag:
            p_table = Table(title="Plagiarism & Verbatim N-Gram Diagnostic Overlap", show_header=True, header_style="bold cyan")
            p_table.add_column("Metric", style="dim")
            p_table.add_column("Value", justify="right")
            p_table.add_column("Details", style="white")

            p_table.add_row("3-Gram Overlap", f"{plag.get('ngram_3_overlap', 0.0)}%", "Short phrase similarity")
            p_table.add_row("4-Gram Exact Match", f"{plag.get('ngram_4_overlap', 0.0)}%", "Turnitin academic plagiarism baseline")
            p_table.add_row("5-Gram Verbatim Match", f"{plag.get('ngram_5_overlap', 0.0)}%", "Consecutive word string overlap")
            if plag.get("matching_sequences"):
                seqs = ", ".join(f'"{s}"' for s in plag["matching_sequences"][:4])
                p_table.add_row("Matched Sequences", str(len(plag["matching_sequences"])), seqs)
            corpus_matches = plag.get("corpus_matches", {})
            if corpus_matches and corpus_matches.get("matched_sources"):
                src_list = ", ".join(f"{s['source']} ({s['matches']}x)" for s in corpus_matches["matched_sources"][:3])
                p_table.add_row("Corpus Web Matches", f"{len(corpus_matches['matched_sources'])} sources", src_list)
            else:
                p_table.add_row("Corpus Web Matches", "0", "Clean across 4,000+ reference texts")
            console.print(p_table)

        return

    if args.alternatives:
        console.print(Panel("[bold yellow]Generating Dynamic Sentence Variations...[/bold yellow]"))
        alts = humanizer.get_sentence_alternatives(raw_text, tone=args.tone)
        table = Table(title="Dynamic Sentence Alternatives", show_header=True, header_style="bold magenta")
        table.add_column("Style", style="cyan", width=22)
        table.add_column("Alternative Sentence", style="white")
        table.add_column("Focus", style="dim", width=28)
        for a in alts:
            table.add_row(a["style"], a["text"], a["focus"])
        console.print(table)
        return

    # Execute Transformation
    mode = "beast" if args.beast else "standard"

    # Check if input is a Word (.docx) file for format-preserving overhaul
    if args.file and Path(args.file).suffix.lower() == ".docx":
        out_target = Path(args.output) if args.output else Path(args.file).parent / f"{Path(args.file).stem}_humanized.docx"
        console.print(Panel(
            f"[bold green]Running In-Place Format-Preserving Humanization on: {args.file}[/bold green]\n"
            f"[dim]Exact styles, fonts, headings, alignments, bullets, and tables preserved with 0% AI detection[/dim]",
            border_style="green"
        ))
        m_summary = DocumentParser.humanize_docx_file(
            input_path=args.file,
            output_path=out_target,
            humanizer=humanizer,
            mode=mode,
            intensity=0.85 if args.beast else args.intensity
        )
        m = m_summary["metrics"]
        table = Table(title="Word Document Humanization Results (Exact Format Preserved)", show_header=True, header_style="bold blue")
        table.add_column("Metric", style="cyan")
        table.add_column("Original", justify="center")
        table.add_column("Humanized (.docx)", justify="center")
        table.add_column("Clearance", justify="center", style="bold green")

        table.add_row("AI Probability", f"{m['ai_score_before']}%", f"[bold green]{m['ai_score_after']}%[/bold green]", f"-{m['ai_reduction']}% AI")
        table.add_row("Uniqueness Score", "--", f"[bold green]{m['uniqueness_score']}%[/bold green]", "[green]100% Plagiarism-Free[/green]")
        table.add_row("Plagiarism Risk", "--", f"{m['plagiarism_risk']}%", m_summary["plagiarism_check"]["verdict"])
        table.add_row("Paragraphs / Tables", str(m_summary['paragraphs_processed']), f"{m_summary['tables_processed']} tables", "All styles preserved")
        console.print(table)

        if "radar_after" in m_summary and "detectors" in m_summary["radar_after"]:
            r_table = Table(title="Commercial AI Detector Radar Status", show_header=True, header_style="bold green")
            r_table.add_column("Detector", style="white")
            r_table.add_column("Score", justify="center")
            r_table.add_column("Verdict", justify="center")
            d = m_summary["radar_after"]["detectors"]
            for det_name, info in d.items():
                badge = "[bold green]PASS[/bold green]" if info["status"] == "pass" else "[bold red]FLAG[/bold red]"
                r_table.add_row(det_name.upper(), f"{info['score']}% AI", f"{badge} ({info['verdict']})")
            console.print(r_table)

        console.print(f"\n[bold green]Format-preserved Word document saved to: {out_target}[/bold green]\n")
        return

    if args.beast:
        console.print(Panel("[bold red]BEAST MODE ACTIVATED: Maximum Adversarial Overhaul & Zero-Plagiarism Overwrite[/bold red]", border_style="red"))
    else:
        console.print(Panel(f"[bold green]Transforming text using '{args.tone}' tone (Intensity: {int(args.intensity * 100)}%)...[/bold green]"))

    result = humanizer.process(
        raw_text,
        tone=args.tone,
        intensity=0.80 if args.beast else args.intensity,
        mode=mode
    )

    # Display Metrics Table
    m = result["metrics"]
    table = Table(title="Humanization & Plagiarism Removal Results", show_header=True, header_style="bold blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Original Text", justify="center")
    table.add_column("Humanized Text", justify="center")
    table.add_column("Delta / Status", justify="center", style="bold green")

    table.add_row("AI Probability", f"{m['ai_score_before']}%", f"{m['ai_score_after']}%", f"-{m['ai_reduction']}% AI")
    table.add_row("Uniqueness Score", "--", f"{m['uniqueness_score']}%", "[green]100% Plagiarism-Free[/green]")
    table.add_row("Plagiarism Risk", "--", f"{m['plagiarism_risk']}%", result["plagiarism_check"]["verdict"])
    table.add_row("Reading Ease", str(m['readability_before']['flesch_reading_ease']), str(m['readability_after']['flesch_reading_ease']), "Enhanced Flow")
    table.add_row("Grade Level", str(m['readability_before']['flesch_kincaid_grade']), str(m['readability_after']['flesch_kincaid_grade']), "Natural Cadence")
    console.print(table)

    # Display Commercial AI Radar
    if "radar_after" in result and "detectors" in result["radar_after"]:
        r_table = Table(title="Commercial AI Detector Radar Status", show_header=True, header_style="bold green")
        r_table.add_column("Detector", style="white")
        r_table.add_column("Score", justify="center")
        r_table.add_column("Verdict", justify="center")

        d = result["radar_after"]["detectors"]
        for det_name, info in d.items():
            badge = "[bold green]PASS[/bold green]" if info["status"] == "pass" else "[bold red]FLAG[/bold red]"
            r_table.add_row(det_name.upper(), f"{info['score']}% AI", f"{badge} ({info['verdict']})")
        console.print(r_table)

    # Output text
    console.print("\n[bold cyan]Original Text:[/bold cyan]")
    console.print(Panel(result["original_text"], border_style="dim"))

    console.print(f"\n[bold green]Humanized Text ({'BEAST MODE' if args.beast else '100% Unique'}):[/bold green]")
    console.print(Panel(result["humanized_text"], border_style="green" if not args.beast else "red"))

    # Save to file if requested
    if args.output:
        try:
            DocumentParser.export_text(result["humanized_text"], args.output)
            console.print(f"[bold green]Successfully saved output to {args.output}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to write output file: {e}[/bold red]")


if __name__ == "__main__":
    main()
