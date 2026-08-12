# Markdown Triage Report Contract

Read this reference whenever creating or updating a workbook-backed Markdown
triage report. Apply it across environments and workbooks; do not copy literal
paths, branch names, sheet names, row numbers, devices, versions, or case names
from an earlier report.

## Contents

- [Report Scope And Ordering](#report-scope-and-ordering)
- [Required Report Header](#required-report-header)
- [Required Case Structure](#required-case-structure)
- [Code Diff Requirements](#code-diff-requirements)
- [Commit Information Requirements](#commit-information-requirements)
- [Consistency Checks](#consistency-checks)
- [Portable Template](#portable-template)

## Report Scope And Ordering

- Maintain one cumulative Markdown report beside the workbook by default:
  `<workbook-basename>.xlsx` becomes `<workbook-basename>.md`.
- Order case sections by workbook row number, not by diagnosis time, commit
  order, or test file name. Reorder existing sections when necessary.
- Group multiple rows in one case section only when they share the same root
  cause and coherent solution, or when they are parameterized variants that
  must be explained together. Include a row-to-nodeid table for grouped rows.
- Keep unrelated cases in separate sections even when they modify the same
  source file.
- Update the existing report incrementally. Preserve correct prior evidence and
  revise stale ordering, numbering, paths, statuses, or conclusions when new
  analysis changes them.
- Use exact evidence from the active environment. Never present an example,
  recommendation, proposed patch, installed-tree validation copy, or historical
  fix as an applied source-tree change.

## Required Report Header

Start the document with this global information before any case section.

### 1. Title And Execution Environment

Use `# <workbook filename>.xlsx triage`, then record:

- environment activation command, if any;
- repository and pytest working directory;
- Python executable and version;
- imported PyTorch version and `torch.__file__`;
- accelerator/runtime version such as HIP/ROCm or CUDA;
- relevant GPU/device model;
- test source checkout;
- workbook path and sheet scope when the report covers only selected sheets.

Record unknown values as `未确认` and the command needed to obtain them. Do not
guess. Separate the source checkout from the imported runtime package because
tests may load an installed Torch while reading test files from the repository.

### 2. Current Repository State

Record a concise snapshot containing:

- repository path;
- current branch and full or abbreviated HEAD;
- branch subject when useful;
- mapped user-fork, internal-main, and official-PyTorch remote roles;
- target/base branch or release used for comparison;
- dirty-worktree state and which changes belong to this triage;
- validation-only installed-package modifications, if any, with an explicit
  statement that they are outside Git and must not be committed.

Always record the code-submission state near this snapshot. If no source change
exists, write `代码提交状态：无待提交修改`. If changes are proposed, applied,
committed, or pushed, state that status and the intended/actual target branch.

When code changes exist, add one authoritative logical-change/commit table near
the top. Use it as the single source of truth for numbering throughout the
report:

| Sequence | Workbook rows | Case/root cause | Source files or hunk | State |
| --- | --- | --- | --- | --- |
| 1 | `<rows>` | `<short diagnosis>` | `<paths and focused change>` | `<applied/uncommitted, committed HASH, proposed, or no change>` |

Only number changes that form real logical commits. Mark optional or unapplied
follow-ups as unnumbered unless they are actually adopted. If commits have
already been created or pushed, update the table with commit hashes, branch,
target branch, and push/MR status. Keep those facts synchronized with every
case's `提交建议` section.

### 3. Global Notes When Applicable

Add short global notes only when they materially affect multiple cases, for
example:

- installed-runtime validation policy;
- official diagnostic routing used;
- workbook error-log limitations;
- a shared test runner or environment warning;
- the distinction between applied, proposed, and no-diff solutions.

Do not turn the header into a duplicate of every case analysis.

## Required Case Structure

Every case or coherent case group must use one `##` heading and exactly these
five `###` subsections in this order.

Immediately below the `##` heading, write:

```text
工作簿位置：工作表 `<exact sheet name>`，第 <row or row range/list> 行。
```

Use the workbook's displayed row numbers. For grouped cases, add a compact table
with row, exact pytest nodeid, variant/input when relevant, original result, and
final disposition. Do not say only “sheet4” if the exact sheet name is known;
both ordinal and exact name may be recorded.

### 1. 报错信息

Include:

- original workbook error, status, timing, or raw-log excerpt;
- exact reproduction command and concise result;
- whether reproduction matches the workbook;
- the failing sample index, dtype, device, shape, backend, generated-test
  identity, or call site when these distinguish the failure;
- relevant warnings, clearly separated from the actual failure condition.

If the workbook has no error details or the case currently passes, state that
directly. Do not borrow an adjacent row's error or invent a failure. Distinguish
runner-level STALL/TIMEOUT from a test-level Python/C++ assertion when evidence
does not connect them.

### 2. 测试目的与错误分析

Explain from the test source outward:

- where the test/template and parameterization are defined;
- how the concrete nodeid is generated when relevant;
- input/sample construction and important shape/dtype/device/backend values;
- what behavior or contract the assertions protect;
- the relevant forward/backward, dispatcher, compiler, generated-code, or
  runtime call chain;
- the precise failure layer and root cause;
- why nearby warnings or similar-looking cases are or are not the same issue;
- official PyTorch `main`/release/PR/issue/commit findings, then internal
  upstream findings when official evidence is insufficient;
- the final classification, such as runtime defect, test expectation drift,
  numerical/reference mismatch, environment/data issue, capability gap, or
  flaky observation.

Connect every conclusion to reproduced behavior, source, history, or upstream
evidence. Include exact links or commit hashes when available. State residual
uncertainty rather than converting a hypothesis into fact.

### 3. 解决方法

Start by labeling the code-change state unambiguously:

- `已应用源码修改`;
- `已应用 test-only 修改`;
- `未应用的可选方案`;
- `当前基线已修复，无新增 diff`;
- `仅诊断，未修改`.

Then include:

- exact source-tree files changed;
- a focused unified diff for each applied logical change;
- analysis of how the changed fields, branches, conditions, metadata, or
  assertions address the root cause;
- why the solution preserves the original test purpose;
- affected and unaffected platforms/dtypes/shapes/tests;
- why an official approach was adopted, adapted, or intentionally not used;
- any installed-runtime mirror used only for validation, separately labeled and
  excluded from the commit diff.

For no-change cases, explicitly state that no source diff is pending and why.
For proposed fixes, label the diff `未应用` and do not describe later test
results as post-fix validation.

### 4. 修改后的测试结果

Record:

- exact activation and test commands;
- exact case result and concise pytest summary;
- nearby/parameterized/shared-logic regression coverage;
- static checks such as `py_compile` and `git diff --check`;
- whether the source-tree or a validation-only installed runtime was executed;
- unrun tests and the exact blocker;
- residual risk and what the completed tests do not prove.

For cases with no code change, call this the current-baseline validation rather
than implying a modification was tested. For skips/xfails, state whether the
outcome is `SKIPPED`, `XFAIL`, or a real `PASS` and why that disposition is
correct.

### 5. 提交建议

Record the review boundary even when no commit is requested:

- whether a commit is needed;
- logical commit sequence from the global table;
- case rows/root cause covered by that commit;
- files and exact hunks to stage;
- files/hunks that must remain unstaged;
- suggested title and a Why/What/Impact body when appropriate;
- validation evidence associated with the commit;
- current state: uncommitted, committed hash, pushed branch, or MR source/target.

State `无需提交` for current-pass/no-change cases. Keep runtime fixes with their
focused regression tests, and keep independent test-only fixes separate even if
they touch the same file. Include concrete staging/commit commands only when
useful or requested; commands must follow `commit_workflow.md` and the active
repository's commit convention.

## Code Diff Requirements

- Generate applied diffs from Git (`git diff`, `git diff --cached`, or
  `git show`) instead of reconstructing them from memory.
- Use repository-relative paths and unified `diff --git` blocks. Include enough
  context to identify the function, class, or OpInfo being changed.
- Keep the diff focused on the case's logical change. Exclude unrelated dirty
  hunks, generated files, test logs, the workbook/report, and installed-package
  validation copies.
- If a long runtime fix is abbreviated, label it `精简 diff（省略未改上下文）`
  and retain every semantically important changed field and branch. Do not use
  an ellipsis that hides part of the fix being analyzed.
- Follow each non-trivial diff with prose explaining the before/after state and
  the causal connection to the failure. A diff without analysis is incomplete.
- Never show a historical or official diff as the local applied diff. Label its
  source commit and status explicitly.
- Update the diff/status after commits: use `git show <hash>` when the worktree
  no longer contains the committed patch.

## Commit Information Requirements

- Treat the global logical-change table as authoritative for sequence numbers.
- Renumber all case references after inserting, removing, regrouping, or
  reordering changes. Avoid ordinal prose such as “第三个” when a stable row,
  case name, or commit hash is clearer.
- Before commit, describe the proposed boundary and state `待提交`.
- After commit, replace proposals with actual hashes/subjects and verify that
  the committed files match the documented boundary.
- After push, record only the branch and remote actually pushed. Do not claim an
  MR exists merely because a creation link is available.
- Keep optional future patches outside the numbered applied sequence until they
  are adopted.

## Consistency Checks

Before handing off the report, verify:

1. Case sections are ordered by workbook row.
2. Every case starts with exact workbook sheet and row information.
3. Every case has exactly the five required subsections in the required order.
4. Applied/proposed/no-diff language matches the actual Git state.
5. Every applied code change has a focused diff and causal analysis.
6. Validation results correspond to the code state described in section 3.
7. Global commit sequence, per-case sequence, commit hashes, branches, and
   submission status agree everywhere.
8. Similar cases are grouped only when root cause and solution are coherent;
   otherwise their distinction is explicit.
9. Markdown code fences are paired, tables render, links point to the intended
   source, and paths are portable or clearly environment-specific evidence.
10. No unrelated user changes, installed-runtime copies, workbooks, reports, or
    caches are described as repository changes to submit.

## Portable Template

Use this skeleton and expand it with evidence. Omit optional global notes when
they do not apply, but never omit the five case subsections.

````markdown
# <workbook filename>.xlsx triage

运行环境：

```bash
<activation command, if any>
cd <pytest working directory>
```

- Python: `<executable>` (`<version>`)
- 运行时 PyTorch: `<version>`，`<torch.__file__>`
- 加速栈: `<HIP/ROCm or CUDA version>`
- GPU/设备: `<model>`
- 测试源码: `<repository/test path>`
- 工作簿范围: `<workbook path; selected sheets if applicable>`

当前仓库状态：

```text
repo: <path>
branch: <branch>
HEAD: <hash and subject>
target/base: <remote role and branch>
working tree: <clean or scoped dirty changes>
remotes: <mapped fork/internal/official roles>
代码提交状态: <无待提交修改 / planned changes / applied-uncommitted / committed / pushed; target branch>
```

<installed-runtime validation note, if any>

| Sequence | Workbook rows | Case/root cause | Source files or hunk | State |
| --- | --- | --- | --- | --- |
| 1 | `<rows>` | `<root cause>` | `<files/change>` | `<state/hash>` |

## <case or coherent case-group name>

工作簿位置：工作表 `<exact sheet name>`，第 `<rows>` 行。

<optional row/nodeid mapping table>

### 1. 报错信息

<workbook evidence, reproduction command/result, match status>

### 2. 测试目的与错误分析

<test source, generation/call path, purpose, evidence, root cause, official/internal findings>

### 3. 解决方法

状态：`<已应用源码修改 / 已应用 test-only 修改 / 未应用的可选方案 / 当前基线已修复，无新增 diff / 仅诊断，未修改>`

修改文件：`<repository-relative paths or 无>`

```diff
diff --git a/<path> b/<path>
<focused actual or explicitly labeled proposed diff>
```

<before/after behavior and causal analysis; scope and alternatives>

### 4. 修改后的测试结果

```bash
<exact validation commands>
```

```text
<concise exact result>
```

<neighbor checks, static checks, runtime source, residual risk>

### 5. 提交建议

<commit boundary/order/state, title/body, staged and excluded hunks, hash/branch if completed>
````
