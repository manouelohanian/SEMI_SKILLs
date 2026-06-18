---
name: test-log-analyzer
description: Analyze STDF semiconductor test logs and optionally compute Gaussian (6-sigma) distribution for a specified test. ALWAYS use the existing script when user asks for yield, failing tests, or sigma distribution.
compatibility: Python 3.10+ with pandas, matplotlib, pystdf
---

# Test Log Analyzer

This skill converts STDF logs into a structured report using a predefined script and template.

---

# Execution mode (STRICT TOOL MODE)

- ONLY use:
  scripts/analyze_test_logs.py

- Treat script as function:
  analyze_test_log(input_file, sigma_tests)

- NEVER:
  - create temp files (tmp_*.py, tmp_*.json, tmp_*.md)
  - generate scripts
  - write reports to disk
  - retry execution
  - debug or troubleshoot
  - run shell commands

- ONLY allowed file output:
  → Gaussian plot in `/plots/`

- All other output must be returned as text

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
- sigma_tests (optional)

If sigma is requested and test name is missing:
→ ask once and stop

---

# Execution (NO THINKING)

1. Call:
   analyze_test_log(input_file, sigma_tests)

2. Get markdown output

3. Append final paragraph (see below)

---

# Final analysis (RULE-BASED ONLY)

Use ONLY result values:

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

1. Template output
2. One paragraph (above)

---

# Constraints (CRITICAL)

- Single execution only
- No retries
- No intermediate steps
- No explanations
- No planning messages
- No logging of actions