from pathlib import Path
import math
from io import StringIO
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt

TOP_N = 10

def parse_float(value):
    try:
        return float(value)
    except:
        return math.nan


def parse_stdf(stdf_path: Path):
    from pystdf.IO import Parser
    from pystdf.Writers import TextWriter

    parser = Parser(inp=open(stdf_path, "rb"))
    buffer = StringIO()
    parser.addSink(TextWriter(buffer))
    parser.parse()

    lines = buffer.getvalue().splitlines()

    rows = []
    all_dut_count = 0
    failed_duts = set()
    test_failures = {}
    pir_counter = 0

    for line in lines:
        if "|" not in line:
            continue

        parts = line.split("|")
        rec_type = parts[0]

        if rec_type == "PIR":
            all_dut_count += 1
            pir_counter += 1

        elif rec_type == "PTR":
            test_name = parts[7] if len(parts) > 7 else ""
            result = parse_float(parts[6]) if len(parts) > 6 else math.nan
            lo = parse_float(parts[13]) if len(parts) > 13 else math.nan
            hi = parse_float(parts[14]) if len(parts) > 14 else math.nan

            status = "PASS"
            if not math.isnan(lo) and result < lo:
                status = "FAIL"
            if not math.isnan(hi) and result > hi:
                status = "FAIL"

            rows.append({
                "test_name": test_name,
                "result": result,
                "status": status,
                "dut_id": pir_counter
            })

            if status == "FAIL":
                failed_duts.add(pir_counter)
                test_failures[test_name] = test_failures.get(test_name, 0) + 1

    return pd.DataFrame(rows), failed_duts, all_dut_count, test_failures


def compute_metrics(df, failed_duts, total_duts, test_failures):
    failing = len(failed_duts)
    passing = total_duts - failing

    yield_percent = round((1 - failing / max(total_duts, 1)) * 100, 2)

    return {
        "yield_percent": yield_percent,
        "total_parts": total_duts,
        "passing_parts": passing,
        "failing_parts": failing,
        "top_tests": dict(sorted(test_failures.items(), key=lambda x: x[1], reverse=True)[:10])
    }


def generate_plot(values, name):
    Path("plots").mkdir(exist_ok=True)
    path = f"plots/{name}_gaussian.png"

    plt.figure()
    plt.hist(values, bins=30)
    plt.savefig(path)
    plt.close()

    return path


def analyze_test_log(input_file: str, sigma_tests=None):
    df, failed_duts, total_duts, test_failures = parse_stdf(Path(input_file))
    metrics = compute_metrics(df, failed_duts, total_duts, test_failures)

    report = f"""
### Key findings:
- Yield: {metrics['yield_percent']}%
- Total parts: {metrics['total_parts']}
- Failing parts: {metrics['failing_parts']}
"""

    if sigma_tests:
        for test in sigma_tests:
            subset = df[df["test_name"] == test]
            if len(subset) > 1:
                plot = generate_plot(subset["result"], test)
                report += f"\nGaussian plot for {test}: {plot}"

    return report