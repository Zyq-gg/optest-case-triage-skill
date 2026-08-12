---
name: optest-case-triage
description: "Use for either one-case-at-a-time PyTorch optest triage from an Excel row or pytest nodeid, or the separate post-triage task of backfilling CSV 测试目的/解决方案/最终状态/遗留原因 columns from an authoritative Markdown report plus variable auxiliary CSV columns. Reproduce, inspect official/upstream fixes, patch, validate, and document cases; safely preserve unrelated CSV fields; commit or push only when explicitly asked."
---

# Optest Case Triage

## Overview

This skill has two independent modes:

1. Deep triage of a single PyTorch optest failure, starting from one workbook
   row or pytest nodeid and ending with validation and a Markdown record.
2. Post-triage document processing that uses a completed Markdown report as the
   authority for safely backfilling four summary columns in a user CSV.

Do not interleave the CSV backfill mode with case reproduction or patching.

Use this skill when the user asks to:

- analyze one specific case from an optest Excel file;
- reproduce a PyTorch unit-test failure and explain the root cause;
- compare a case with workbook history and historical notes;
- check whether upstream/official PyTorch already fixed the issue;
- try a minimal local source/test patch;
- write a case-analysis Markdown record;
- use an existing Markdown report plus arbitrary auxiliary CSV columns to fill
  `测试目的`, `解决方案`, `最终状态`, and `遗留原因`;
- split verified fixes into reviewable commits and push a development branch to
  the user's fork when explicitly requested.

Do not use this skill for bulk extraction from raw logs, creating a new failure
workbook, or marking newly detected Excel rows; that belongs to
`torch-optest-log-xlsx-skill`.

Expected input:

- An optest Excel workbook plus an op name or `(py name, class, op name)`.
- Or a direct pytest nodeid if no workbook is involved.
- Or a completed Markdown triage report plus the CSV to summarize.

Expected output:

- A concrete diagnosis.
- The exact reproduction command and result.
- Any upstream/official fix evidence found.
- Any local patch attempted.
- Validation result and residual risk.
- A cumulative workbook Markdown report with a reproducible environment/repo
  header and consistent five-part case records when requested or useful.
- Or, in the separate document mode, a structurally validated CSV whose four
  summary columns reflect the Markdown report without changing other fields.

Portable repository and environment rules for one-case triage:

- At the start of every one-case triage run, read
  [references/portable_setup.md](references/portable_setup.md) completely.
- Resolve `<skill-dir>` as the directory containing this `SKILL.md`; all helper
  scripts, dependency declarations, and references are bundled under it.
- Use the PyTorch checkout, Python environment, workbook, and output path named
  by the user. Use the current directory/environment only after validation; do
  not guess host-specific paths or activation scripts.
- Treat `origin`, `upstream`, and `official` as logical remote roles. Map them by
  URL or user instruction, fetch only configured remotes, and keep working when
  an optional reference remote is absent.
- Pair a fork development branch such as `2.9.1-dev-xxx` with the internal base
  `2.9.1-dev` unless the user specifies another target. Map internal versions to
  official releases such as `release/2.9` for version coverage.
- Search official `main` first, then newer official releases, then the target
  release. Use bundled official-skill guidance and live GitHub links if no local
  official remote exists.

The standalone CSV document workflow does not require a PyTorch checkout or
runtime. Resolve `<skill-dir>`, the user-provided CSV, Markdown report, update
plan, and output path directly from
[references/csv_report_backfill.md](references/csv_report_backfill.md).

Do not push or submit to any remote unless the user explicitly asks.

## What This Skill Can Do

- Locate a case row in an optest workbook, including ambiguous substring
  searches.
- Read useful workbook columns such as `错误结果`, `详细分析`, `测试目的`,
  `历史版本分析`, `新增标记`, and local custom analysis columns.
- Reproduce the failure from the working PyTorch repo with the correct environment.
- Compare the reproduced error with the workbook error and classify mismatches
  such as already-fixed, flaky, environment-only, or wrong row/log match.
- Inspect local PyTorch source and tests around the failure.
- Compare against `upstream/*` and `official/*` remote-tracking branches/tags.
- Search official PyTorch issues, PRs, tags, and raw source when network access
  or fetched `official` refs are available and accuracy needs it.
- Route matching failures through the relevant official PyTorch diagnostic
  skill without loading or copying unrelated official skills.
- Port/adapt an official fix when one exists and applies cleanly.
- Propose or apply a minimal local fix when no official fix is found.
- Validate the exact failing case and nearby cases when the patch touches shared
  behavior.
- Write a row-ordered Markdown report with environment/repository/commit state
  and five-part case records containing evidence, focused diffs, validation,
  residual risk, and review boundaries.
- Create logically separated commits with controlled staging and hand them off
  for an MR/PR when the user explicitly asks.
- Backfill the four CSV summary columns from completed Markdown analysis while
  treating auxiliary CSV conclusions as non-authoritative context.

## Boundaries

- Do not submit patches, push branches, or open GitLab/GitHub PRs unless the user
  explicitly asks.
- Do not infer commit or push authorization from a request to analyze, modify,
  or validate a case. Treat commit, push, and MR/PR creation as separate actions.
- Treat official PyTorch skills as diagnostic references, not as permission to
  mutate GitHub issues, labels, comments, branches, commits, or remotes. Keep
  this skill's local-worktree and explicit-authorization boundaries.
- Do not make broad skips, broad tolerance changes, or unrelated refactors just
  to get a case green.
- Do not trust workbook notes as proof; use them as hypotheses to check.
- Do not overwrite user changes. If files are dirty, inspect and work with the
  existing changes.
- Treat official PyTorch evidence as the highest-value signal. Before inventing
  a local workaround or changing test semantics, search official `main`, newer
  release branches, commits, PRs, and issues. A found official fix can save a
  large amount of speculative local analysis and usually gives the safest patch
  direction.
- Prefer a minimal, evidence-backed patch. If a test expectation changed
  upstream, document why porting that expectation is valid.
- In CSV backfill mode, never hard-code an auxiliary column letter such as L.
  Discover relevant columns from headers and contents, and let current Markdown
  evidence override conflicting historical CSV notes.

## Workflow

### 1. Read The Workbook Row

Find the row for the requested case before running tests. Prefer exact test
identity fields when provided. The first three columns are usually the file name,
class name, and op/test name, often named `py name`, `class`, and `op name`, but
workbooks may use different labels. Treat the first three columns as the case
identity when the names differ.

Use the helper script when useful:

```bash
python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --op-name test_name_or_substring
```

Capture the case identity fields:

- file/test module column, usually `py name`
- class column, usually `class`
- test/op column, usually `op name`

For all other workbook columns, do not hard-code names. Read the populated
columns that are useful for this case, such as testing purpose, solution,
statuses/retest status, notes, residual/legacy reason, error text, historical
analysis, or local triage notes. Record only the fields that materially shape the
hypothesis or final Markdown.

Use the workbook context to form an initial hypothesis, but do not treat it as proof.

If multiple rows match, report the candidates and choose only when there is a
clear intended row, such as a sheet name, exact class, or exact op name.

### 2. Reproduce The Case

Run the exact pytest case from the working PyTorch repo.

Preferred command:

```bash
<environment activation command, if provided>
cd <working PyTorch repo>
python -m pytest -vs PY_NAME::CLASS_NAME::OP_NAME
```

Pytest paths may appear with or without the repository `test/` prefix depending
on whether the command is run from the repo root or from `<working PyTorch
repo>/test`. Normalize both forms before concluding a case cannot be collected:

```text
test/dynamo/test_activation_checkpointing.py
dynamo/test_activation_checkpointing.py
```

If collection or parametrization requires `-k`, use:

```bash
pytest -vs PY_NAME -k OP_NAME
```

Record:

- Pass/fail status
- Concise exception line
- Relevant timings, generated-code paths, warnings, or compile/link messages
- Whether the reproduced error matches the workbook row

During reproduction, read the pytest source around the case and relevant helpers
to understand the test purpose. Later diagnosis and patches must preserve that
purpose; do not change the backend, dtype, skip condition, expected text, or
assertion in a way that makes the test pass while testing a different behavior.

If the case depends on a custom environment, use the activation command provided
by the user. Otherwise keep the current environment and record `sys.executable`,
`torch.__version__`, and `torch.__file__` before testing.

For slow or flaky tests, rerun only when it materially changes confidence. If a
test passes on rerun, classify it carefully:

- `已修复/当前通过`: current code no longer reproduces the workbook failure.
- `flaky/环境相关`: failure is intermittent or timing/resource-sensitive.
- `日志不匹配`: workbook row likely came from a different build/configuration.

### 3. Check Official, Then Upstream Fixes First

Before inventing a local fix, look for an official solution first. This is a
critical step: if an official PyTorch commit, PR, issue, or release-branch change
explains the failure, prefer porting or minimally adapting that approach. Only
after official evidence is missing or insufficient should you use the internal
`upstream` branch as the primary reference.

Do not skip this step even when a local workaround looks obvious. Finding the
official fix or official direction early avoids unnecessary and misleading
analysis.

First inspect the working repo state and remotes:

```bash
git -C <working PyTorch repo> status --short --branch
git -C <working PyTorch repo> remote -v
git -C <working PyTorch repo> branch -vv
git -C <working PyTorch repo> log --oneline --decorate --all -- PY_NAME
```

Map the fork, internal-main, and official-PyTorch roles using
`portable_setup.md`. Fetch only the remotes that are configured:

```bash
git -C <working PyTorch repo> fetch <configured remote> --prune
git -C <working PyTorch repo> rev-parse --short HEAD
git -C <working PyTorch repo> rev-parse --short <remote>/<branch>
```

For internal branches, pair the fork and internal-main roles by branch family.
For example, a local branch based on `2.9.1-dev-xxx` should usually compare
against the internal-main `2.9.1-dev`. For official PyTorch, map the internal
version to the corresponding release branch, such as `release/2.9` for
2.9/2.9.1 work.

Official search order:

1. Search official `main` for the test name, file, error text, relevant
   function, or changed behavior.
2. Search newer official release branches, especially the latest fetched
   `official/release/2.X` branches. Official fixes may be present in a high
   release branch such as `release/2.13` while missing from the target branch.
3. Check the corresponding official release branch/tag for the target version,
   such as `official/release/2.9`, `v2.9.1`, or relevant rc tags.
4. Search official commits, PRs, and issues. Use commit messages and PR/issue
   numbers from `git log --all`, source comments, workbook notes, or error text.
5. If no official direction is found, inspect internal `upstream` development
   branches from newer to older before falling back to the target base branch.
   For example, when working on `2.9.1-dev-xxx`, check newer internal branches
   such as `upstream/2.13.0-dev`, then `upstream/2.12.0-dev`, and continue
   downward as relevant before checking `upstream/2.9.1-dev`. This catches fixes
   that exist internally but have not been merged back to the target branch.

For every non-trivial case record whether this official search found an exact
fix, a related fix, or no relevant official fix. If a local solution differs
from official direction, explicitly explain why.

Compare source without checking out over dirty local changes:

```bash
git -C <working PyTorch repo> diff upstream/BASE_BRANCH...HEAD -- PY_NAME
git -C <working PyTorch repo> diff official/release/2.X..official/main -- PY_NAME
git -C <working PyTorch repo> diff official/release/2.X..official/release/NEWER_2.X -- PY_NAME
git -C <working PyTorch repo> diff upstream/BASE_BRANCH..official/main -- PY_NAME
git -C <working PyTorch repo> diff upstream/BASE_BRANCH..upstream/NEWER_DEV_BRANCH -- PY_NAME
git -C <working PyTorch repo> show official/main:PY_NAME
git -C <working PyTorch repo> show official/release/2.X:PY_NAME
git -C <working PyTorch repo> show upstream/NEWER_DEV_BRANCH:PY_NAME
git -C <working PyTorch repo> show upstream/BASE_BRANCH:PY_NAME
git -C <working PyTorch repo> show --stat --oneline COMMIT
git -C <working PyTorch repo> show --unified=80 COMMIT -- PY_NAME
```

These examples use the typical remote names. Replace them with the mapped names
from `portable_setup.md` and skip commands whose refs are unavailable. Missing
optional refs reduce comparison coverage but do not prevent local reproduction
and diagnosis.

When a suspected official commit is known, check which branches contain it:

```bash
git -C <working PyTorch repo> branch -r --contains COMMIT
git -C <working PyTorch repo> merge-base --is-ancestor COMMIT official/main
git -C <working PyTorch repo> merge-base --is-ancestor COMMIT official/release/NEWER_2.X
git -C <working PyTorch repo> merge-base --is-ancestor COMMIT official/release/2.X
git -C <working PyTorch repo> merge-base --is-ancestor COMMIT upstream/NEWER_DEV_BRANCH
git -C <working PyTorch repo> merge-base --is-ancestor COMMIT upstream/BASE_BRANCH
```

Search official GitHub when network is available. Use official PyTorch sources
before internal downstream sources:

- `https://github.com/pytorch/pytorch/issues`
- `https://github.com/pytorch/pytorch/pulls`
- Raw source from `main`, relevant release tags, or patch tags such as `v2.12.1`

Search terms should include:

- `op name`
- class name
- exact error text
- relevant file/function name
- issue or PR number from local git log if discovered

Classify the result:

- **Official fix found**: port or adapt it if it applies cleanly; record the
  exact commit, PR/MR, issue, and branch/tag coverage.
- **Related official fix found**: explain the overlap and why it does or does not solve this case.
- **No official fix, internal upstream fix found**: use the `upstream` fix if it
  is minimal and relevant; record that it is downstream/internal rather than
  official PyTorch.
- **No official fix found**: proceed with a minimal local fix based on evidence.

When browsing upstream, prefer official PyTorch sources. Record exact PR/issue
numbers, commit hashes, tags, or file URLs in the Markdown record.

### 4. Diagnose The Root Cause

Use evidence from reproduction, workbook history, source, and official search.
Before deep diagnosis, read
[references/official_pytorch_skills.md](references/official_pytorch_skills.md)
and use its bundled diagnostic route. If an official remote or network access
is available, optionally refresh only the matching official skill. Use pinned
links when reproducibility matters and live `main` links when checking for
updated guidance. Missing optional official refs must not block diagnosis.

The official skill supplies domain-specific diagnostic methods; this skill
still controls environment selection, dirty-worktree handling, patch scope,
validation, Markdown output, commits, and remote mutations. In particular, do
not inherit GitHub issue labeling/commenting/closing actions from official issue
triage skills unless the user explicitly requests those actions.

Common diagnosis categories:

- Backend capability gap: HIP/ROCm/CUDA path lacks an implementation or guard.
- Numerical mismatch: output differs from eager/reference because of dtype,
  accumulation, algorithm choice, or tolerance.
- Compiler/codegen bug: Inductor/Triton lowering, scheduler, template, or
  generated kernel is wrong.
- Test expectation drift: upstream changed behavior or golden text/counts.
- Environment/data issue: missing dependency, failed download, corrupt cache,
  network, device capability, or timing threshold.
- Flaky/timing: threshold is too absolute for the environment or workload.
- Distributed/runtime setup: rank count, process group, device availability, or
  unsupported distributed operator path.

For each category, state why the evidence points there and what evidence would
disprove it.

### 5. Try A Minimal Patch

Patch only the code needed for this case. Preserve user and existing local changes.
The patch should be guided by the evidence already found: exact official fix
first, then related official direction, then newer internal `upstream` branch
fixes, then target-branch local reasoning. Avoid inventing a patch that ignores
an applicable official or internal reference.

Test files under `<working PyTorch repo>/test/...` only need to be edited in the
working source tree. Do not force tests to import runtime code from the source
tree just for validation.

When patching non-test PyTorch runtime source under `<working PyTorch repo>/torch/...`,
first check which `torch` package the selected test environment imports. In this
environment, derive the active package root instead of assuming a Python or
installation layout:

```bash
python -c "from pathlib import Path; import sys, torch; print(sys.executable); print(Path(torch.__file__).resolve().parent)"
```

Prefer the repository's supported source/build workflow. Only when the user
explicitly requests installed-tree validation, apply the same minimal runtime
patch to the dynamically resolved package root. The Markdown record should
still list source-tree changes as the changes to commit and separately mention
any installed-package patch used only for verification. Never stage that copy.

Good patch patterns:

- Prefer semantic assertions over arbitrary buffers.
- Prefer backend guards or fallbacks over skipping broad tests.
- Prefer targeted dtype/device/shape handling over global behavior changes.
- For test-only timing failures, compare against a measured baseline when possible.

Bad patch patterns:

- Changing expected values without explaining behavior.
- Broad skips for unrelated platforms.
- Reverting unrelated local changes.
- Fixed thresholds without justification when a relative condition expresses the test purpose better.

Use `apply_patch` for manual edits.

Patch decision rules:

- If an official fix exists, port the smallest relevant part first.
- If a newer `upstream` branch has a relevant fix and no official fix was found,
  adapt the smallest relevant part and record the branch/commit used.
- If the issue is unsupported backend behavior, prefer a targeted guard,
  fallback, or explicit error over silent wrong behavior.
- If the issue is test-only and upstream changed the test, preserve the test's
  purpose rather than copying an arbitrary number or text.
- If a local patch would be risky or broad, stop at diagnosis and explain the
  safer follow-up.

### 6. Validate

Run the exact failing case again using the same environment. If the fix is in shared logic, run at least one nearby case or a narrower `-k` group.

For a non-trivial runtime or test-framework patch, apply the relevant testing,
backward-compatibility, and design checks routed from
[references/official_pytorch_skills.md](references/official_pytorch_skills.md).
An existing failing workbook case can serve as the regression test; add a new
test only when the existing case does not isolate or permanently cover the bug.

Record the exact command and summary result, for example:

```text
PASSED [108.4338s]
1 passed in 113.57s
```

If tests cannot be run, say why and record the residual risk.

Validation levels:

- Exact case only: acceptable for narrow test-only fixes.
- Exact case plus neighboring variant: use for parametrized tests, dtype/device
  guards, or shared helper changes.
- Small focused file/class subset: use when touching common compiler/backend
  logic.
- Not run: acceptable only with a clear blocker and risk note.

### 7. Write The Markdown Record

Create or update a Markdown record. When the case comes from a workbook, prefer
one Markdown file beside the workbook, named from the workbook basename with
`.md` replacing `.xlsx`; for example `report.xlsx` should record into
`report.md`. Append new case sections to that same file instead of creating
case-named files, unless the user explicitly asks for a separate file.

If there is no workbook, or the user asks for a new standalone file, create one
at the user-provided path or in the current task directory.

Before writing or revising a workbook-backed report, read
[references/markdown_report.md](references/markdown_report.md) completely and
follow its report contract and portable template. It is the authoritative
output schema for this workflow.

Required invariants include:

- Start the document with the execution environment, imported runtime, current
  repository/remote/base state, dirty changes, validation-only installed-tree
  copies, and code-submission/target-branch status. Add a single authoritative
  logical-change/commit table when code changes exist; state explicitly when
  there is no pending source change.
- Order case sections by workbook row. Start every case/group with the exact
  sheet name and row/range/list, and add a row-to-nodeid table for grouped
  parameterized cases.
- Give every case exactly five subsections in this order: `报错信息`,
  `测试目的与错误分析`, `解决方法`, `修改后的测试结果`, and `提交建议`.
- In `解决方法`, explicitly distinguish applied source changes, applied
  test-only changes, unapplied proposals, current-baseline/no-diff cases, and
  diagnosis-only cases. Include a focused Git-derived unified diff for every
  applied change and explain the before/after behavior and causal link.
- Keep source-tree diffs separate from installed-package mirrors used only for
  validation. Never present an official/historical/proposed diff as a locally
  applied patch.
- In `修改后的测试结果`, record exact commands, results, adjacent coverage,
  static checks, runtime source, blockers, and residual risk. Do not describe a
  baseline pass as a post-fix pass.
- In `提交建议`, preserve the same logical grouping and sequence as the global
  table; state files/hunks to stage and exclude, commit status/hash/branch when
  known, and `无需提交` for no-change cases.
- Before handoff, audit row ordering, five-section completeness, code-fence
  pairing, diff/status accuracy, validation state, and global/per-case commit
  numbering consistency.

When an official PR/issue/source was checked, include the result in section 2.
If no official fix exists, explicitly say so. Record the official diagnostic
skill used, its source ref/commit, and any guidance intentionally not adopted
because it conflicts with this workflow.

### 8. Commit And Hand Off Only When Requested

Do not enter this stage unless the user explicitly asks for commits, a pushed
branch, or MR/PR preparation. Before committing, read
[references/commit_workflow.md](references/commit_workflow.md) completely and
follow it for branch selection, logical commit splitting, controlled staging,
author and message format, validation, fork-only push rules, and final reporting.

Keep these invariants:

- Commit only source-tree changes under the working repository. Never stage the
  installed-torch copy used only for validation or analysis Markdown outside the
  repository.
- Put cases in one commit only when they share one root cause and one coherent
  fix. Separate unrelated runtime, backend, test-expectation, and infrastructure
  fixes even when they were triaged together.
- Push only to `origin`, and only when the user explicitly requests a push.

## Separate Document Workflow: Backfill CSV From Markdown

This is a post-triage document task, not step 9 of the case workflow. Use it
only when the Markdown analysis already exists and the user asks to update CSV
summary fields.

Read
[references/csv_report_backfill.md](references/csv_report_backfill.md)
completely. It defines:

- Markdown-over-CSV evidence precedence;
- dynamic discovery of auxiliary columns regardless of letter or position;
- exact case matching and ambiguous-row handling;
- concise semantics and status vocabulary for `测试目的`, `解决方案`, `最终状态`,
  and `遗留原因`;
- a reviewable JSON update-plan format;
- structural validation that preserves BOM, case identity, non-target columns,
  row order, and logical row count.

Use `scripts/backfill_triage_csv.py` only after producing the semantic update
plan. The helper deliberately does not interpret Markdown; it prevents a valid
analysis from being applied to the wrong row or from rewriting unrelated CSV
data.

## Helper Script

`scripts/find_case_in_xlsx.py` locates workbook rows and prints all populated
columns for the match.

Common commands:

```bash
python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --op-name test_max_min_bool_cpu

python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --py-name test/test_ops.py \
  --class-name TestCommonCPU \
  --op-name test_max_min_bool_cpu \
  --exact \
  --json
```

Use `--json` when another script or tool should consume the result.

For the separate CSV document workflow:

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --dry-run
```

## Relationship To torch-optest-log-xlsx

Use `torch-optest-log-xlsx-skill` first when the user asks for bulk processing:

- parse many logs;
- create three-column or six-column Excel files;
- mark new cases.

Use this skill after that, when the user chooses one row for deep investigation:

- reproduce exactly;
- inspect source and upstream/official fixes;
- patch locally;
- validate;
- write the Markdown record.

Separately, use this skill's CSV report-backfill workflow after triage when the
user wants completed Markdown conclusions summarized into the four report
columns. That operation consumes existing analysis; it does not perform batch
failure extraction or replace per-case validation.

## Example: Timing Test

For `test_forkserver_perf`, a fixed `+5` threshold passes but is weaker than comparing parallel time to the measured serial baseline. Prefer:

```python
serial_elapsed = time.perf_counter() - start
self.assertGreaterEqual(serial_elapsed, Expensive.SLEEP_SECS * nprocs)

parallel_elapsed = time.perf_counter() - start
self.assertLess(parallel_elapsed, serial_elapsed / 2)
```

This keeps the test purpose: parallel forkserver startup should be noticeably faster than non-parallel startup, while avoiding failures from environment-specific import overhead.

## Example: Official Fix Exists

For cases such as `test_max_min_bool_cpu` and `test_max_min_bool_cuda`, first search `official/*` and `upstream/*` history for matching changes. If a later official commit changes bool max/min behavior or test expectations, port that minimal patch rather than inventing a new one. Then validate both CPU and CUDA variants and document the upstream/official source in the Markdown record.

## Example: Environment/Data Issue

For `test_module_backcompat`, the test may download and load a legacy
`linear.pt` file. If reproduction fails with `EOFError: Ran out of input`,
check whether the downloaded/cache file is empty or corrupt before patching
PyTorch serialization. Document it as an environment/data issue if the source
logic is sound.

## Example: Backend Capability Gap

For FP8 or scaled matmul cases, inspect both Python test expectations and
backend support code such as `ScaledBlas`, CUDA/HIP BLAS wrappers, dtype/device
guards, and Inductor lowering. If ROCm lacks a mode supported by CUDA, prefer a
targeted capability guard or fallback with a clear error over broad test skips.
