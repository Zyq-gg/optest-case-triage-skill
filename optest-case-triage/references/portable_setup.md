# 可移植环境准备

每次开始 case 分析都要完整阅读本文。路径和工具必须从当前环境解析，不得假设最初开发 skill 的容器仍然存在。

## 目录

- [定位 skill 目录](#定位-skill-目录)
- [定位工作仓库](#定位工作仓库)
- [区分三类仓库](#区分三类仓库)
- [确认 Python 与 PyTorch](#确认-python-与-pytorch)
- [定位工作簿与输出](#定位工作簿与输出)
- [映射 Git remote](#映射-git-remote)
- [处理 runtime 源码验证](#处理-runtime-源码验证)

## 定位 skill 目录

将 `<skill-dir>` 解析为当前所加载 `SKILL.md` 的所在目录。以下配套文件均相对于该目录：

```text
<skill-dir>/requirements.txt
<skill-dir>/scripts/find_case_in_xlsx.py
<skill-dir>/scripts/backfill_triage_csv.py
<skill-dir>/references/portable_setup.md
<skill-dir>/references/official_pytorch_skills.md
<skill-dir>/references/commit_workflow.md
<skill-dir>/references/csv_report_backfill.md
<skill-dir>/references/markdown_report.md
```

不要通过硬编码 clone 路径反推 skill 位置。skill 可能通过符号链接安装、复制到 skills 目录，或直接从 clone 加载。

读取工作簿前检查依赖：

```bash
python3 -c "import openpyxl"
```

缺少依赖时报告下列安装命令，但未经用户允许不要安装：

```bash
python3 -m pip install -r <skill-dir>/requirements.txt
```

## 定位工作仓库

优先使用用户明确指定的编译仓和代码记录仓 PyTorch checkout。用户只指定一个 checkout 时，先确认它是否同时承担两个角色；未指定时，只有下列检查全部成功才可把某个当前目录作为候选，并仍需明确它承担的角色：

```bash
git rev-parse --show-toplevel
test -d torch
test -d test
test -f torch/version.py
```

否则应向用户取得对应 checkout 路径，不能猜测主机专用位置。

以 Git 顶层目录为基准解析仓库内测试路径。接受 `test/dynamo/test_x.py` 和 `dynamo/test_x.py`；后者通常表示命令从 `<repo>/test` 运行。

## 区分三类仓库

实际任务可能把构建、代码记录和安装验证分开。必须在开始测试前明确三类仓库；它们可以是同一个路径，但不能因为路径相同就省略角色记录。

| 角色 | 定义 | 允许的修改和用途 | 提交边界 |
| --- | --- | --- | --- |
| 编译仓 | 用于源码构建、生成 build 产物并运行依赖该产物的测试的 PyTorch checkout，例如 `/workspace/pytorch-compile`。 | 通常保持不改；需要重新编译才生效时，可在此应用与代码记录仓相同的临时源码 patch，然后构建和运行测试。 | build 目录、生成文件和仅为编译而存在的修改默认不提交；若该路径同时被指定为代码记录仓，才按代码记录仓规则处理。 |
| 代码记录仓 | 用于人工查看源码 diff、保存 case 修改、创建 commit 和 push 的 PyTorch checkout，例如 `/workspace/pytorch` 或 `/workspace/pytorch-code`。 | 所有 case 的源码/测试修改都必须在此记录；这里是提交建议、Git 状态、commit hash 和 MR/PR 边界的唯一权威来源。 | 只有该仓库中的目标源码 patch 才能进入 stage、commit 和 push；不得把编译仓或安装验证仓的镜像改动直接当作提交内容。 |
| 安装验证仓 | 由实际运行的 `torch.__file__` 动态解析出的已安装 torch 包目录，可能位于 `/usr`、virtualenv 或其他 site-packages。 | 用于验证当前 pytest 实际加载的 runtime；用户明确要求或源码构建流程无法直接提供 runtime 时，可同步最小 runtime patch。 | 永远只作 validation-only；不得 stage、commit、push，也不得把其路径误写成代码记录仓源码路径。 |

默认角色映射：

```text
编译仓：<compile checkout>
代码记录仓：<code-record checkout>
安装验证仓：<Path(torch.__file__).resolve().parent>
```

如果用户只提供一个 PyTorch 路径，先询问或验证它是否同时承担编译仓和代码记录仓；如果用户明确说明它们相同，可以记录“编译仓 = 代码记录仓”。不能猜测另一个 checkout，也不能把安装验证仓通过固定 `/usr` 路径猜出来。

开始运行前记录每个角色的绝对路径、当前 branch/HEAD、dirty 状态，以及三者是否为同一份 checkout。编译仓存在未提交改动时，先区分它是用户已有改动、为当前 case 临时应用的 patch，还是 build 生成物；不得覆盖或清理用户改动。

三类仓库之间的同步规则：

1. 代码记录仓中的 patch 是逻辑和提交的源头；每个 applied diff 都从该仓库的 Git 生成。
2. 测试必须依赖编译产物时，将同一逻辑 patch 临时同步到编译仓，再重新构建；同步 patch 必须记录文件、commit/工作树基线和构建命令。
3. 实际 pytest 导入安装包时，将需要验证的 runtime patch 同步到安装验证仓；记录同步文件和导入路径，但不把它纳入代码 diff。
4. 编译仓或安装验证仓中的 patch 与代码记录仓不一致时，不能宣称“修复后通过”；应标为“验证副本不一致”，先同步或说明差异。

确认编译仓和代码记录仓：

```bash
git -C <compile-repo> rev-parse --show-toplevel
git -C <compile-repo> status --short --branch
git -C <compile-repo> rev-parse HEAD
git -C <code-record-repo> rev-parse --show-toplevel
git -C <code-record-repo> status --short --branch
git -C <code-record-repo> rev-parse HEAD
```

## 确认 Python 与 PyTorch

使用用户提供的环境激活命令。若未提供，保留并记录当前 shell 环境，不 source 猜测的脚本。

pytest 前执行：

```bash
command -v python
python -c "import sys, torch; print(sys.executable); print(torch.__version__); print(torch.__file__)"
python -m pytest --version
```

`torch.__file__` 决定 pytest 实际导入的 runtime 代码，也就是安装验证仓。不得假设 Python 版本、virtualenv 布局或 site-packages 前缀。若 pytest 使用编译仓的 editable package，必须记录该事实，并说明安装验证仓与编译仓实际重合。

## 定位工作簿与输出

使用用户提供的工作簿路径。若只给 basename 或行号，在当前任务目录查找唯一匹配的 `.xlsx`；存在多个候选时询问用户。

默认在工作簿旁创建同 basename 的 `.md`。例如 `/data/run.xlsx` 对应 `/data/run.md`。没有工作簿时，使用用户指定的输出路径，或在当前任务目录创建含义清晰的文件。

不得把输出默认到某台机器专用目录。

## 映射 Git remote

`origin`、`upstream`、`official` 是逻辑角色，不保证就是实际 remote 名。fetch 前先检查：

```bash
git -C <repo> remote -v
git -C <repo> branch -vv
```

推荐角色映射：

| 逻辑角色 | 常见名称 | 用途 |
| --- | --- | --- |
| 用户 fork | `origin` | 工作分支，以及用户明确要求的 push |
| 内部主线 | `upstream` | 目标分支同步和内部版本对比 |
| PyTorch GitHub | `official` | 官方 main、release、commit、PR、issue 和 skill |

名称不同时按 URL 或用户说明映射。只 fetch 已存在的 remote。未经用户明确要求，不新增、重命名或重写 remote。

若缺少 official remote，使用 `official_pytorch_skills.md` 的内置指导和 GitHub 链接检索官方修复。文档要注明无法进行本地官方分支包含关系检查，但不能因此阻止整个分析流程。

## 处理编译与 runtime 源码验证

测试源码和 runtime 的来源必须分别记录：测试可能从代码记录仓或编译仓读取，而 Python 运行时由 `torch.__file__` 决定。优先采用编译仓支持的 editable/build 工作流；若编译仓和代码记录仓不同，修改后需在编译仓重新构建，不能只修改代码记录仓就把安装包测试结果称为修复后结果。

只有用户明确要求“修改安装目录仅用于验证”，或当前测试明确导入安装包而无法直接使用新构建产物时，才动态解析安装验证仓：

```bash
python -c "from pathlib import Path; import torch; print(Path(torch.__file__).resolve().parent)"
```

只同步同一份最小 runtime diff：代码记录仓 → 编译仓（如需构建）→ 安装验证仓（如需安装包验证）。分别记录每个副本的文件、基线和命令。安装验证仓中经验证有效的修改默认不回退，保留给用户后续复测；如果用户要求清理或切换版本，必须先记录当前副本状态再操作。绝不 stage 或 commit 编译产物、安装验证仓或工作仓库之外的文件。不得硬编码安装前缀、Python 版本或包管理器布局。
