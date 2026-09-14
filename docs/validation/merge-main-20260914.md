# main 分支整合验证 · 2026-09-14

本次将 `codex/mr-support` 的经典 MR / Enhanced MR 支持，与 main 中的多视口布局、2D / MPR 对比和实时调窗整合。两个工作目录原有的修改先各自提交保存：`2f0d305`（布局、对比、实时调窗）、`0b876df`（MR）。

## 整合时修复

- 实时调窗的缓存重映射使用当前模态的最小窗宽；MR 保留小数窗值、MONOCHROME1 与用户反白的组合语义，padding 继续显示为黑色。覆盖普通 2D、三个正交方向、MPR、2D / MPR 对比和平铺。
- 切片滑条同时依赖已生效的范围和索引，解决 MR 初始中间层或延迟加载范围时仍停留在零点的问题，保留滑条两端的最大／最小值和当前视口激活行为。
- 统一对比选择器：2D 可选择 2–4 个序列，MPR 始终为两组；保存／恢复保留多视口数量与状态。
- 保留两个分支新增的帮助内容和语言条目，移除已删除条目的空值；四角字段继续固定使用英文。
- 修正外部 Enhanced MR 样本用例的模块导入，使默认隔离测试入口能够正确收集并按环境跳过。

## 测试结果

环境：macOS arm64、Python 3.13、Qt 6.11.1、VTK 9.5.2。使用 `tests/run_isolated.py` 按文件隔离执行。

| 范围 | 最终结果 |
| --- | --- |
| 全量 112 个测试文件（包含失败项修正后的单独复测） | 1516 通过、49 跳过、0 失败 |
| 本机窗口、真实 MR / Enhanced MR 样本与实时调窗截图验证 | 20 通过、0 跳过、0 失败 |

全量入口使用 `QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software PYTHONPATH=src:tests`。初次运行中，新增对比测试的样本构造越界和 Enhanced MR 外部用例的模块路径已修正，并复测对应两个文件；其余 110 个文件全部通过。

本机补验使用 `QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software VOXENRA_NATIVE_QA=1`，设置公开 MR 样本目录后运行 `tests/manual/test_mr_samples.py`、`tests/manual/test_enhanced_mr_samples.py` 和 `tests/test_live_windowing_qml.py`。49 个默认跳过项包含外部样本、桌面渲染、Docker PACS 或平台条件限制，MR 样本和本机界面由上述单独运行覆盖。

本机日志分别保存在 `/private/tmp/voxenra-merge-full`、`/private/tmp/voxenra-merge-recheck` 和 `/private/tmp/voxenra-merge-native`。编译检查、冲突标记检查与 `git diff --check` 均通过。本次未重新发布安装包；Windows 原生行为仍需该平台 CI / 桌面验证。
