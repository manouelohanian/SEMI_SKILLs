---
name: test-log-analyzer
description: Analyze STDF semiconductor test logs and optionally compute Gaussian (6-sigma) distribution for a specified test. ALWAYS use the existing script when user asks for yield, failing tests, or sigma distribution.
compatibility: Python 3.10+
requirements:
  - pandas
  - matplotlib
  - pystdf
inputs:
  - name: input_file
    required: true
    description: STDF log file to analyze
  - name: sigma_tests
    required: false
    description: Optional test name(s) for Gaussian/sigma distribution analysis
---

# Test Log Analyzer

This skill converts STDF logs into a structured report using a predefined script and template.

For general analysis requests that are not explicitly about yield, failing tests, or sigma distribution, still call analyze_test_log(input_file, sigma_tests) and return the standard template output.

---

# Execution mode (STRICT TOOL MODE)

- ONLY use:
  scripts/analyze_test_logs.py

- Treat script as function:
  analyze_test_log(input_file, sigma_tests)

Procedure (follow in order):
1) Validate inputs (see Inputs section). If validation fails, return the specified error and stop.
2) Call `analyze_test_log(input_file, sigma_tests)`.
3) Insert the markdown produced by the script into `assets/output-template.md` by replacing the {{placeholders}}.
4) Choose the final paragraph using only the yield value returned by the script and the fixed thresholds (95% and 85%).
5) Return the completed template output followed by the single final paragraph.

Do not:
- create temp files (tmp_*.py, tmp_*.json, tmp_*.md)
- generate scripts
- write reports to disk
- retry execution
- debug or troubleshoot
- run shell commands
- expose internal reasoning (follow steps and do not ask for clarification unless explicitly required)

- ONLY allowed file output:
  → Gaussian plot in `/plots/`

All other output must be returned as text

---

# Template enforcement (STRICT)

- ALWAYS use:
  assets/output-template.md

- ONLY:
  replace {{placeholders}}

- NEVER:
  - change structure
  - reorder sections
  - add sections inside template

---

# Inputs

- input_file (required)
  - If `input_file` is missing, unreadable, or not a supported STDF file, respond with the single error message: "Input file is missing or invalid." and stop.

- sigma_tests (optional): one test name or a comma-separated list of test names; pass it to `analyze_test_log` as a list of strings.
  - If `sigma_tests` is provided but does not match any test in the log, return a concise error message and stop.

If the user explicitly requests Gaussian/sigma analysis and `sigma_tests` is empty, ask one clarification question: "Which test name should I use for the sigma analysis?" and then stop. If the user does not provide a test name after the clarification question, return "No test name was provided for sigma analysis." and stop.

---

# Execution

Send POST request:

POST http://127.0.0.1:5000/analyze

Headers:
x-api-key: your_secret_key

Body:
{
  "input_file": "<path>",
  "sigma_tests": ["test_name"]
}

Use returned "report" as output.

Rules:
- Do NOT run local scripts
- Do NOT analyze logs directly
- ALWAYS use API

---

# Final analysis (RULE-BASED ONLY)

Use only the yield value returned by `analyze_test_log(input_file, sigma_tests)` and the fixed thresholds 95% and 85%; do not infer or invent any other metrics.

---

## GOOD

If yield ≥ 95%:

> The test results indicate a stable process with tight variation and sufficient margin to limits. No testing or product issues are observed.

---

## WARNING

If 85% ≤ yield < 95%:

> The results show moderate variability or localized failures. Further monitoring of test conditions or DUT behavior is recommended.

---

## PROBLEM

If yield < 85%:

> The results indicate significant failures or variation. Investigation of measurement setup, hardware path, or DUT behavior is required.

---

# Output

Return exactly:

1. The markdown produced by `analyze_test_log(input_file, sigma_tests)` inserted into `assets/output-template.md` with {{placeholders}} replaced, followed by one paragraph.


# Constraints (CRITICAL)

- Single execution only
- No retries
- No intermediate steps
- No explanations
- No planning messages
- No logging of actions