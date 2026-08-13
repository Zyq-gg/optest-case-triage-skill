# 提交工作流

仅当用户明确要求提交已验证的 optest 修复、准备审查分支或推送到 fork 时，才完整阅读并执行本文。

## 目录

- [授权边界](#授权边界)
- [提交前检查](#提交前检查)
- [按逻辑修复拆分提交](#按逻辑修复拆分提交)
- [精确暂存](#精确暂存)
- [提交前验证](#提交前验证)
- [提交元数据](#提交元数据)
- [推送与交付](#推送与交付)

## 授权边界

- 请求分析、修改或验证不代表授权 commit。
- 请求 commit 不代表授权 push。
- 请求 push 不代表授权创建 MR/PR，除非用户同时明确要求。
- feature branch 绝不能推到 `upstream` 或 `official`；只能推到用户 fork 对应的 `origin`。
- 未经用户明确要求相应操作，不得 amend、rebase、force-push、删除分支或重写已发布历史。

## 提交前检查

stage 前检查仓库：

```bash
git status --short --branch
git remote -v
git branch --show-current
git branch -vv
```

阅读同目录 `portable_setup.md`，先区分编译仓、代码记录仓和安装验证仓。代码记录仓是唯一的 diff、commit 和 push 来源；编译仓中的同步 patch/build 产物不提交；安装验证仓中验证有效的 runtime 修改可以保留供用户后续复测，但仍属于 validation-only。随后把用户 fork、内部主线和官方 PyTorch 逻辑角色映射到实际 remote。常见名称是 `origin`、`upstream`、`official`，但不能只按名字假定角色。将 `2.9.1-dev-xxx` 等开发分支映射到目标内部基线，通常是 `2.9.1-dev`。

保留所有既有用户修改。无关变更保持 unstaged；用户要求提交的改动与同一文件或 hunk 中的无关变更重叠时，在不丢弃任何内容的前提下拆分。只有确实无法安全分离时才停止并请求用户决定。

存在未提交工作时，不切换分支，除非当前工作流已经明确这些修改如何保存。创建新开发分支前，刷新映射后的 fork 和内部主线 ref，并从目标内部分支创建：

```bash
git fetch <internal-main remote> --prune
git fetch <user-fork remote> --prune
git rev-parse --short <internal-main remote>/<target-branch>
git branch --list <dev-branch>
git ls-remote --heads <user-fork remote> <dev-branch>
git checkout -b <dev-branch> <internal-main remote>/<target-branch>
```

开发分支已经存在于本地或用户 fork 时，先检查内容；复用、删除或强制更新前必须询问用户。

## 按逻辑修复拆分提交

每个 commit 都应能独立审查和回退：

- 只有多个 case 的根因相同且由同一完整代码修改修复时才合并。
- 即使影响同一测试文件或来自同一工作簿，独立根因也必须分成不同 commit。
- runtime 行为修复与无关的测试预期、环境 guard、timeout、构建/基础设施修复分开。
- 聚焦的 regression test 与它验证的 runtime 修改放在一起。
- 不把当前所有 modified files 打成一个 catch-all commit。
- 不为满足逐 case 形式而把不可分割的 runtime 修复人为拆散。

每次提交前列清其 case 行/nodeid、根因、文件和验证证据。Markdown 应使用相同分组，并说明修改处于待提交、已提交还是有意不提交状态。

## 精确暂存

检查 unstaged diff，只 stage 目标 path 或 hunk。dirty worktree 中避免 `git add -A`、`git add .` 和其他宽泛暂存。

```bash
git diff -- <changed-files>
git status --short
git add <only-files-wholly-owned-by-this-commit>
git diff --cached --check
git diff --cached --stat
git diff --cached -- <changed-files>
```

文件含无关修改时，只 stage 目标 patch，并优先使用可审查的非交互方式。stage 后确认 cached diff 只包含一个逻辑修复，其他 working-tree 修改仍然 unstaged。

绝不 stage 安装验证仓中的验证副本、编译仓 build 产物/临时镜像、生成 cache、测试输出、工作簿或代码记录仓之外的 Markdown。

## 提交前验证

先完成 case 分析流程要求的验证，再对 staged patch 做轻量仓库检查：

```bash
git diff --cached --check
python -m py_compile <changed-python-files>
```

运行精确受影响 pytest；共享逻辑变化时增加合适的相邻 case。不能运行完整测试时，记录准确 blocker，区分已完成静态检查与未执行测试；不得把必要测试未运行的 commit 称为“已验证”。

非简单修改还要阅读同目录 `official_pytorch_skills.md`，执行路由到的官方 `pr-review` 检查。至少检查 regression 覆盖、既有测试工具、skip/xfail 语义、向后兼容性，以及是否引入隐藏行为开关或无关变化。

## 提交元数据

用命令级 identity，不修改全局 Git 配置：

```text
GitHub username: Zyq-gg
GitHub user id: 70554563
Commit identity: Zyq-gg <70554563+Zyq-gg@users.noreply.github.com>
```

subject 格式保持为：

```text
[das-<module>] <short English description>
```

示例：

```text
[das-dynamo] Adjust standalone test timeout
[das-inductor] Fix extension device registration
[das-aten] Model flash attention RNG state views
```

module 按代码归属领域选择，不能只看测试目录。subject 简短并描述行为变化。基于官方修复时，保持其技术方向，在 Markdown 中记录官方 commit/PR；有助于 reviewer 理解时也写入 commit body。

显式设置 author 和 committer：

```bash
git -c user.name=Zyq-gg \
  -c user.email=70554563+Zyq-gg@users.noreply.github.com \
  commit --author="Zyq-gg <70554563+Zyq-gg@users.noreply.github.com>" \
  -m "[das-<module>] <short English description>"
```

每次 commit 后、开始下一提交前检查内容：

```bash
git show --stat --oneline HEAD
git show --check HEAD
git status --short --branch
```

## 推送与交付

仅在用户明确要求时 push：

```bash
git push -u origin <dev-branch>
```

不把开发分支推到 `upstream` 或 `official`。除非用户在获知必要性后明确授权，否则不 force-push。

交付时报告：

- 目标 `upstream` 分支和开发分支；
- 按顺序列出 commit hash 和 subject；
- 每个 commit 覆盖的 case/根因；
- 每个 commit 的验证命令和结果；
- 仍存在的 unstaged/uncommitted 用户修改；
- 是否已经 push，以及适用时 MR/PR 的 source/target branch。
