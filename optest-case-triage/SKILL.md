---
name: optest-case-triage
description: "Use when doing one-case-at-a-time PyTorch optest triage from an Excel row or pytest nodeid: read workbook context, reproduce the failure, compare history, inspect the working PyTorch repo plus its origin/upstream/official remotes for fixes, try a minimal local patch, validate, write a Markdown analysis record, and optionally split verified fixes into scoped commits for the user's fork. Complements batch log/XLSX skills; commit or push only when explicitly asked."
---

# Optest Case Triage

## Overview

Use this skill for deep triage of a single PyTorch optest failure. It complements
`torch-optest-log-xlsx-skill`, which is for batch log/XLSX processing. This skill
starts from one workbook row or pytest nodeid and carries the case through
reproduction, source investigation, optional local patching, validation, and a
Markdown record.

Use this skill when the user asks to:

- analyze one specific case from an optest Excel file;
- reproduce a PyTorch unit-test failure and explain the root cause;
- compare a case with workbook history and historical notes;
- check whether upstream/official PyTorch already fixed the issue;
- try a minimal local source/test patch;
- write a case-analysis Markdown record.
- split verified fixes into reviewable commits and push a development branch to
  the user's fork when explicitly requested.

Do not use this skill for bulk extraction from logs or marking new Excel rows;
that belongs to `torch-optest-log-xlsx-skill`.

Expected input:

- An optest Excel workbook plus an op name or `(py name, class, op name)`.
- Or a direct pytest nodeid if no workbook is involved.

Expected output:

- A concrete diagnosis.
- The exact reproduction command and result.
- Any upstream/official fix evidence found.
- Any local patch attempted.
- Validation result and residual risk.
- A Markdown case record when requested or useful.

Default repository and environment rules:

- Working repo for analysis, local edits, validation, and commits: use the
  PyTorch checkout named by the user. If none is named, use the current working
  directory when it is a PyTorch repo; otherwise prefer `/workspace/pytorch-new`
  if present, then `/workspace/pytorch`.
- Do not rely on separate local comparison repos. Compare against the working
  repo's remotes instead.
- Expected remotes in the working repo:
  - `origin`: the user's fork. Use this for branches intended for local
    changes, validation, commits, and pushes when explicitly requested.
  - `upstream`: the internal/main repository. Use this for synchronization,
    comparing branch state, and creating fresh local branches from the main
    development line.
  - `official`: the official PyTorch GitHub repository. Use this mainly to
    inspect official fixes, release branches/tags, PR-linked commits, and the
    correct upstream direction for a patch. Do not push to `official`.
- Branch mapping rules:
  - `origin` and `upstream` are paired by internal branch family. If the working
    branch is `origin/2.9.1-dev` or `origin/2.9.1-dev-xxx`, compare and sync
    against `upstream/2.9.1-dev`. Apply the same pattern for other internal
    development branches unless the user specifies a different upstream base.
  - `official` uses official PyTorch release branches/tags for version
    comparison, such as `official/release/2.9` for a 2.9/2.9.1 internal branch.
  - Because official fixes usually land first in `official/main` and may then be
    cherry-picked only to newer release branches, always search official `main`
    first, then newer official release branches, then the corresponding official
    release branch. Record where the fix is present and where it is missing.
- Typical optest workbook: `/workspace/pytorch2.12.0-optest_2_marked_newcases.xlsx`
- Typical environment, unless the user specifies another one:

```bash
source /home/tmp/python_and_sh/env-old.sh
cd <working PyTorch repo>
```

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
- Port/adapt an official fix when one exists and applies cleanly.
- Propose or apply a minimal local fix when no official fix is found.
- Validate the exact failing case and nearby cases when the patch touches shared
  behavior.
- Write a Markdown record with problem, analysis, fix, validation, and evidence.
- Create logically separated commits with controlled staging and hand them off
  for an MR/PR when the user explicitly asks.

## Boundaries

- Do not submit patches, push branches, or open GitLab/GitHub PRs unless the user
  explicitly asks.
- Do not infer commit or push authorization from a request to analyze, modify,
  or validate a case. Treat commit, push, and MR/PR creation as separate actions.
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

## Workflow

### 1. Read The Workbook Row

Find the row for the requested case before running tests. Prefer exact test
identity fields when provided. The first three columns are usually the file name,
class name, and op/test name, often named `py name`, `class`, and `op name`, but
workbooks may use different labels. Treat the first three columns as the case
identity when the names differ.

Use the helper script when useful:

```bash
python3 /workspace/optest-case-triage-skill/optest-case-triage/scripts/find_case_in_xlsx.py \
  --xlsx /workspace/pytorch2.12.0-optest_2_marked_newcases.xlsx \
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
source /home/tmp/python_and_sh/env-old.sh
cd <working PyTorch repo>
pytest -vs PY_NAME::CLASS_NAME::OP_NAME
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

If the case depends on a custom environment, source the environment first. For
this workspace the default is:

```bash
source /home/tmp/python_and_sh/env-old.sh
cd <working PyTorch repo>
```

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
git -C <working PyTorch repo> fetch origin --prune
git -C <working PyTorch repo> fetch upstream --prune
git -C <working PyTorch repo> fetch official --prune
git -C <working PyTorch repo> log --oneline --decorate --all -- PY_NAME
```

Use `origin` as the fork/working remote, `upstream` as the internal main remote,
and `official` as the official PyTorch reference remote. Determine branch bases
before comparing:

```bash
git -C <working PyTorch repo> branch --show-current
git -C <working PyTorch repo> branch -vv
git -C <working PyTorch repo> rev-parse --short HEAD origin/INTERNAL_BRANCH upstream/BASE_BRANCH official/release/2.X
```

For internal branches, pair `origin` and `upstream` by branch family. For
example, a local branch based on `origin/2.9.1-dev` or
`origin/2.9.1-dev-xxx` should usually compare against `upstream/2.9.1-dev`.
For official PyTorch, map the internal version to the corresponding release
branch for version coverage checks, such as `official/release/2.9` for
2.9/2.9.1 work.

Official search order:

1. Search `official/main` for the test name, file, error text, relevant
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
workspace, `env-old.sh` tests may import installed files from
`/usr/local/lib/python3.10/site-packages/torch` rather than the working tree. If
so, apply the same minimal runtime patch to the installed torch file for local
validation. The Markdown record should still list the source-tree changes under
the working repo as the changes to commit or carry to a clean environment, and
separately mention any installed-torch patch used only for verification.

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
one Markdown file per workbook under `/workspace`, named from the workbook
basename with `.md` replacing `.xlsx`; for example
`/workspace/torch291_ind_pytest_bw_analyzed.xlsx` should record into
`/workspace/torch291_ind_pytest_bw_analyzed.md`. Append new case sections to
that same file instead of creating case-named files, unless the user explicitly
asks for a separate file.

If there is no workbook, or the user asks for a new standalone file, create one
under `/workspace`.

Use this section format:

````markdown
# <workbook basename>.xlsx triage

运行环境默认使用：

```bash
source /home/tmp/python_and_sh/env-old.sh
cd <working PyTorch repo>
```

当前仓库同步状态：

```text
<branch/commit/remote summary>
```

## <op name>

1. 报错信息

   <workbook error and reproduction error>

2. 测试目的与错误分析

   <what the test verifies, why it failed, history/GCC relevance, upstream/official search result>

3. 解决方法

   <files changed; what changed from old behavior/code to new behavior/code;
   before/after snippets or a focused diff when useful; key code analysis;
   why this fix is preferred and how it preserves the test purpose>

4. 修改后的测试结果

   <commands and results, or not-run reason>
```
````

When an official PR/issue/source was checked, include the result in section 2. If no official fix exists, explicitly say so.

Also include:

- workbook sheet/row when available;
- exact reproduction command;
- exact changed files if a patch was attempted;
- detailed solution notes: changed files, before/after behavior, focused diff
  or code snippets, and the key reasoning that connects the code change to the
  root cause;
- validation command and concise result;
- not-run reason and residual risk when validation is incomplete.

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

## Helper Script

`scripts/find_case_in_xlsx.py` locates workbook rows and prints all populated
columns for the match.

Common commands:

```bash
python3 /workspace/optest-case-triage-skill/optest-case-triage/scripts/find_case_in_xlsx.py \
  --xlsx /workspace/pytorch2.12.0-optest_2_marked_newcases.xlsx \
  --op-name test_max_min_bool_cpu

python3 /workspace/optest-case-triage-skill/optest-case-triage/scripts/find_case_in_xlsx.py \
  --xlsx /workspace/pytorch2.12.0-optest_2_marked_newcases.xlsx \
  --py-name test/test_ops.py \
  --class-name TestCommonCPU \
  --op-name test_max_min_bool_cpu \
  --exact \
  --json
```

Use `--json` when another script or tool should consume the result.

## Relationship To torch-optest-log-xlsx

Use `torch-optest-log-xlsx-skill` first when the user asks for bulk processing:

- parse many logs;
- create three-column or six-column Excel files;
- mark new cases;
- fill columns E/F/G/H across many rows.

Use this skill after that, when the user chooses one row for deep investigation:

- reproduce exactly;
- inspect source and upstream/official fixes;
- patch locally;
- validate;
- write the Markdown record.

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
