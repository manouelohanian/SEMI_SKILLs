
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import math
import re
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

TOP_N = 10
DEFAULT_TEMPLATE_NAME = 'output-template.md'


# ======================
# CORE HELPERS
# ======================

def parse_float(value):
    try:
        return float(value)
    except:
        return math.nan


def parse_int(value):
    f = parse_float(value)
    return None if math.isnan(f) else int(round(f))


# ======================
# STDF PARSER
# ======================

def parse_stdf(stdf_path: Path):
    from pystdf.IO import Parser
    from pystdf.Writers import TextWriter

    parser = Parser(inp=open(stdf_path, "rb"))
    buffer = StringIO()
    parser.addSink(TextWriter(buffer))
    parser.parse()

    lines = buffer.getvalue().splitlines()

    rows = []
    all_dut_count = 0  # Count all DUTs from PIR records
    failed_duts = set()  # Track which DUTs have failures
    test_failures = {}  # Track failing tests
    pir_counter = 0  # Counter for DUTs

    for line in lines:
        if "|" not in line:
            continue

        parts = line.split("|")
        rec_type = parts[0]

        if rec_type == "PIR":
            # PIR: track all DUTs
            all_dut_count += 1
            pir_counter += 1
            current_dut_id = pir_counter

        elif rec_type == "PTR":
            # PTR fields: [0]=PTR, [1]=test_id, [2]=site, [3]=?, [4]=?, [5]=?, [6]=result, [7]=test_name, ..., [13]=lo_limit, [14]=hi_limit, [15]=unit
            site = parts[2] if len(parts) > 2 else ""
            test_name = parts[7] if len(parts) > 7 else ""
            result = parse_float(parts[6]) if len(parts) > 6 else math.nan
            lo = parse_float(parts[13]) if len(parts) > 13 else math.nan
            hi = parse_float(parts[14]) if len(parts) > 14 else math.nan
            unit = parts[15] if len(parts) > 15 else ""

            # Skip tests with no limits (NA and 0 limits excluded)
            has_limits = (
                (not math.isnan(lo) and lo != 0.0)
                or (not math.isnan(hi) and hi != 0.0)
                or (unit and unit.strip() and unit.strip() != "")
            )
            if not has_limits:
                continue

            status = "PASS"
            if not math.isnan(lo) and lo != 0.0 and result < lo:
                status = "FAIL"
            if not math.isnan(hi) and hi != 0.0 and result > hi:
                status = "FAIL"

            rows.append({
                "source_record": "PTR",
                "site": site,
                "test_name": test_name,
                "result": result,
                "lo_limit": lo,
                "hi_limit": hi,
                "status": status,
                "dut_id": pir_counter
            })
            
            # Track failures
            if status == "FAIL":
                failed_duts.add(pir_counter)
                if test_name not in test_failures:
                    test_failures[test_name] = 0
                test_failures[test_name] += 1

    return pd.DataFrame(rows), failed_duts, all_dut_count, test_failures


# ======================
# METRICS
# ======================

def compute_metrics(df, failed_duts, all_dut_count, test_failures):
    # Count total DUTs
    total_duts = all_dut_count
    
    # Count DUTs with failures
    failing_duts = len(failed_duts)
    passing_duts = total_duts - failing_duts
    
    # Count total failed test events
    fails = df[df["status"] == "FAIL"]
    failed_test_events = len(fails)
    
    # Top failing tests
    top_tests = sorted(test_failures.items(), key=lambda x: x[1], reverse=True)[:10]
    top_failing_tests = dict(top_tests)

    return {
        "total_parts": total_duts,
        "yield_percent": round((1 - failing_duts / max(total_duts, 1)) * 100, 2),
        "passing_parts": passing_duts,
        "failing_parts": failing_duts,
        "failed_test_events": failed_test_events,
        "top_failing_tests": top_failing_tests,
        "site_failures": {}
    }


# ======================
# SIGMA
# ======================

def compute_sigma(rows):
    values = rows["result"].dropna()

    if len(values) == 0:
        return None

    mean = values.mean()
    sigma = values.std()

    return {
        "mean": mean,
        "sigma": sigma,
        "min": values.min(),
        "max": values.max(),
        "lower": mean - 3 * sigma,
        "upper": mean + 3 * sigma,
        "width": 6 * sigma
    }


# ======================
# PLOT (ONLY FILE ALLOWED)
# ======================

def generate_plot(values, name, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    file = out_dir / f"{name}_gaussian.png"

    plt.figure()
    plt.hist(values, bins=30, density=True)
    plt.savefig(file)
    plt.close()

    return str(file)


# ======================
# TEMPLATE
# ======================

def load_template():
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "assets" / DEFAULT_TEMPLATE_NAME
    # Read with utf-8 and replace errors to avoid encoding failures on Windows
    if template_path.exists():
        text = template_path.read_text(encoding='utf-8', errors='replace')
    else:
        text = Path(DEFAULT_TEMPLATE_NAME).read_text(encoding='utf-8', errors='replace')

    # Remove the guidance section from the template so the generated report
    # contains only the filled report (guidance is for authors, not users).
    guidance_marker = "\n### Placeholder guidance"
    if guidance_marker in text:
        text = text.split(guidance_marker, 1)[0]

    return text


def generate_report(df, metrics, sigma_tests, plots_dir, input_file=""):
    template = load_template()

    # Format top failing tests as bullets
    top_tests_bullets = "\n".join(
        [f"- `{name}` — {count} failures" for name, count in metrics["top_failing_tests"].items()]
    ) if metrics["top_failing_tests"] else "- None"

    # Format site failures as bullets
    site_fail_bullets = "\n".join(
        [f"- `{site}` — {count} failures" for site, count in metrics["site_failures"].items()]
    ) if metrics["site_failures"] else "- None"

    if sigma_tests:
        sigma_section = ""
        for test in sigma_tests:
            subset = df[df["test_name"] == test]

            stats = compute_sigma(subset)
            if not stats:
                continue

            plot = generate_plot(subset["result"], test, plots_dir)

            sigma_section += f"""
#### {test}
- Samples: {len(subset)}
- Mean: {stats['mean']:.4f}
- Std dev: {stats['sigma']:.4f}
- Min/Max: {stats['min']:.4f} / {stats['max']:.4f}
- 6σ width: {stats['width']:.4f}
- Plot: {plot}
"""
    else:
        sigma_section = "Not requested."

    return template \
        .replace("{{input_file}}", str(input_file)) \
        .replace("{{total_parts}}", str(metrics["total_parts"])) \
        .replace("{{yield_percent}}", str(metrics["yield_percent"])) \
        .replace("{{passing_parts}}", str(metrics["passing_parts"])) \
        .replace("{{failing_parts}}", str(metrics["failing_parts"])) \
        .replace("{{failed_test_events}}", str(metrics["failed_test_events"])) \
        .replace("{{top_failing_tests_bullets}}", top_tests_bullets) \
        .replace("{{site_failure_bullets}}", site_fail_bullets) \
        .replace("{{sigma_analysis_section}}", sigma_section)


# ======================
# MAIN FUNCTION (IMPORTANT)
# ======================

def analyze_test_log(input_file: str, sigma_tests=None, plots_dir="plots"):
    df, failed_duts, all_dut_count, test_failures = parse_stdf(Path(input_file))
    metrics = compute_metrics(df, failed_duts, all_dut_count, test_failures)

    return generate_report(df, metrics, sigma_tests or [], plots_dir, input_file=input_file)


# ======================
# CLI (optional)
# ======================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--sigma-test", action="append")
    args = parser.parse_args()

    report = analyze_test_log(args.input_file, args.sigma_test)
    print(report)


if __name__ == "__main__":
    main()
