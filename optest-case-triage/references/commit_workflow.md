# Commit Workflow

Read this reference only when the user explicitly asks to commit validated
optest fixes, prepare a branch for review, or push to the fork.

## Contents

- [Authorization Boundaries](#authorization-boundaries)
- [Preflight](#preflight)
- [Split Commits By Logical Fix](#split-commits-by-logical-fix)
- [Stage Deliberately](#stage-deliberately)
- [Validate Before Committing](#validate-before-committing)
- [Commit Metadata](#commit-metadata)
- [Push And Handoff](#push-and-handoff)

## Authorization Boundaries

- A request to analyze, modify, or validate does not authorize a commit.
- A request to commit does not authorize a push.
- A request to push does not authorize creating an MR/PR unless the user also
  asks for it.
- Never push feature branches to `upstream` or `official`. Push only to
  `origin`, the user's fork.
- Do not amend, rebase, force-push, delete branches, or rewrite published
  history unless the user explicitly requests that exact operation.

## Preflight

Inspect the repository before staging anything:

```bash
git status --short --branch
git remote -v
git branch --show-current
git branch -vv
```

Read `portable_setup.md` from this directory and map the user-fork,
internal-main, and official-PyTorch logical roles to the configured remote
names. The typical names are `origin`, `upstream`, and `official`, but do not
assume them from spelling alone. Map a development branch such as
`2.9.1-dev-xxx` to its target internal base, normally `2.9.1-dev`.

Preserve all pre-existing user changes. If unrelated changes are present, leave
them unstaged. If requested and unrelated changes overlap the same file or hunk,
separate them without discarding either change; stop for direction only when a
clean separation is not possible.

Do not switch branches with uncommitted work unless the requested workflow has
already established how that work will be preserved. When creating a new
development branch, refresh the mapped fork and internal-main refs and create
it from the target internal branch:

```bash
git fetch <internal-main remote> --prune
git fetch <user-fork remote> --prune
git rev-parse --short <internal-main remote>/<target-branch>
git branch --list <dev-branch>
git ls-remote --heads <user-fork remote> <dev-branch>
git checkout -b <dev-branch> <internal-main remote>/<target-branch>
```

If the development branch already exists locally or on the user-fork remote,
inspect it and ask before reusing, deleting, or force-updating it.

## Split Commits By Logical Fix

Make each commit independently reviewable and reversible:

- Combine multiple cases only when they fail for the same root cause and are
  fixed by the same coherent code change.
- Keep independent root causes in separate commits even when they affect the
  same test file or were analyzed in the same workbook.
- Keep runtime behavior fixes separate from unrelated test-expectation updates,
  environment guards, timeout changes, and build/infrastructure fixes.
- Include focused regression tests with the runtime change they validate.
- Do not create one catch-all commit for every currently modified file.
- Do not split one inseparable runtime fix into artificial per-case commits.

Before each commit, identify its case rows/nodeids, root cause, changed files,
and validation evidence. The Markdown record should use the same grouping and
state whether the change is pending, committed, or intentionally not submitted.

## Stage Deliberately

Review the unstaged diff and stage only the intended paths or hunks. Avoid
`git add -A`, `git add .`, and broad staging from a dirty worktree.

```bash
git diff -- <changed-files>
git status --short
git add <only-files-wholly-owned-by-this-commit>
git diff --cached --check
git diff --cached --stat
git diff --cached -- <changed-files>
```

When a file contains unrelated changes, stage only the intended patch. Prefer a
non-interactive, reviewable method when possible. After staging, verify that the
cached diff contains one logical fix and that unrelated working-tree changes
remain unstaged.

Never stage validation-only modifications under an installed Torch package
outside the working repository, generated caches, test outputs, workbooks, or
Markdown files outside the repository.

## Validate Before Committing

Use the validation already required by the triage workflow, then run lightweight
repository checks on the staged patch:

```bash
git diff --cached --check
python -m py_compile <changed-python-files>
```

Run the exact affected pytest cases and an appropriate neighboring case when
shared logic changed. If the full test cannot run, record the exact blocker and
distinguish completed static checks from unrun tests. Do not claim a commit is
verified when its required test did not run.

For non-trivial changes, read `official_pytorch_skills.md` from this directory
and apply the routed official `pr-review` checks that match the patch. At
minimum, check regression-test coverage, use of established test utilities,
skip-versus-xfail semantics, backward compatibility, and whether the patch
introduces hidden behavioral flags or unrelated changes.

## Commit Metadata

Use command-level identity instead of changing global Git configuration:

```text
GitHub username: Zyq-gg
GitHub user id: 70554563
Commit identity: Zyq-gg <70554563+Zyq-gg@users.noreply.github.com>
```

Use this subject format:

```text
[das-<module>] <short English description>
```

Examples:

```text
[das-dynamo] Adjust standalone test timeout
[das-inductor] Fix extension device registration
[das-aten] Model flash attention RNG state views
```

Choose the module from the owning area, not merely the test directory. Keep the
subject concise and describe the behavior changed. When an official fix is the
basis, preserve its technical direction and record the official commit/PR in the
Markdown analysis; include it in the commit body when useful for reviewers.

Commit with explicit author and committer identity:

```bash
git -c user.name=Zyq-gg \
  -c user.email=70554563+Zyq-gg@users.noreply.github.com \
  commit --author="Zyq-gg <70554563+Zyq-gg@users.noreply.github.com>" \
  -m "[das-<module>] <short English description>"
```

After each commit, verify its contents before starting the next one:

```bash
git show --stat --oneline HEAD
git show --check HEAD
git status --short --branch
```

## Push And Handoff

Push only when explicitly requested:

```bash
git push -u origin <dev-branch>
```

Do not push the development branch to `upstream` or `official`. Do not
force-push unless explicitly authorized after showing why it is required.

At handoff, report:

- target `upstream` branch and development branch;
- commit hashes and subjects in order;
- cases/root causes covered by each commit;
- validation commands and results per commit;
- remaining unstaged or uncommitted user changes;
- whether the branch was pushed, and the MR/PR source and target branches when
  applicable.
