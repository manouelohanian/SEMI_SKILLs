---
name: test-log-analyzer
description: Analyze STDF semiconductor test logs and optionally compute Gaussian (6-sigma) distribution for a specified test. ALWAYS use the existing script when user asks for yield, failing tests, or sigma distribution.
compatibility: Python 3.10+ with pandas, matplotlib, pystdf
---

# Test Log Analyzer

This skill converts semiconductor test logs into a structured engineering summary using a predefined script and output template.

---

# Execution mode (STRICT TOOL MODE)

- ALWAYS use the existing script:
  scripts/analyze_test_logs.py

- Treat script as a function:
  analyze_test_log(input_file, sigma_tests)

- NEVER:
  - create temporary files (tmp_*.py, tmp_*.json, tmp_*.md)
  - generate new scripts
  - write reports to disk
  - create debug or intermediate files

- ONLY allowed file creation:
  → Gaussian plot images inside `/plots/`

- All other outputs MUST be returned as text only

---

# Template enforcement (CRITICAL)

- ALWAYS use:
  assets/output-template.md

- NEVER:
  - create custom output structures
  - reorder template sections
  - rename sections

- Replace placeholders only:
  {{...}}

- The template defines the FULL output structure

---

# When to use this skill

Use when the user asks to:
- summarize STDF / ATDF logs
- compute yield or failure metrics
- identify top failing tests or sites
- run Gaussian / normal / 6σ analysis
- analyze test distributions

---

# Required inputs

| Input | Required | Notes |
|------|--------|------|
| STDF file path | Yes | Main input |
| Sigma test name / number | Optional | Required only for Gaussian analysis |

---

# Workflow

## Step 1 — Get inputs
- STDF file path
- optional sigma test(s)

---

## Step 2 — Call script

Call: analyze_test_log(input_file, sigma_tests)
- Do NOT reimplement logic
- Do NOT generate code
- Do NOT simulate parsing

---

## Step 3 — Generate output

- Use template:
  assets/output-template.md

- Fill placeholders using script output:
  - {{total_parts}}
  - {{yield_percent}}
  - {{passing_parts}}
  - {{failing_parts}}
  - {{failed_test_events}}
  - {{top_failing_tests_bullets}}
  - {{site_failure_bullets}}
  - {{sigma_analysis_section}}

- Return the completed template

---

## Step 4 — Add final analysis paragraph (REQUIRED)

After the template, append **ONE short engineering paragraph**

---

# Analysis logic (FAST RULE-BASED)

Use ONLY simple thresholds (NO deep reasoning):

---

## ✅ GOOD CONDITION

If:
- Yield ≥ 95%
- Fail count low
- No dominant failing test
- Sigma small vs limits

Return:

> The test results indicate a stable process with tight distribution and sufficient margin to specification limits. No immediate testing or product concerns are observed.

---

## ⚠️ WARNING CONDITION

If:
- Yield between 85% – 95%
- Repeated failing tests
- Moderate spread
- Values approaching limits

Return:

> The results suggest moderate variability or localized failures. This may indicate potential issues with measurement setup, test conditions, or DUT variation that should be monitored or further evaluated.

---

## 🚨 PROBLEM CONDITION

If:
- Yield < 85%
- High failure concentration
- Distribution wide or close to limits

Return:

> The results indicate potential testing or product-related issues, with significant variation or failure concentration. Investigation into measurement setup, hardware path, or DUT behavior is recommended.

---

# Output contract

The response MUST be:

1. Template-based markdown report (unchanged structure)
2. ONE additional paragraph at the end

---

# Response style

- Keep output concise and engineering-focused
- Do NOT repeat numeric values
- Do NOT add extra sections
- Do NOT explain methodology unless asked

---

# Validation checklist

Ensure:
- Template structure is preserved
- All placeholders are replaced
- No extra files are created
- Only plot files exist (if sigma used)
- One final paragraph is appended
