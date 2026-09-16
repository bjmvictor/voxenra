# Slicer 与 Voxenra 的 SEG 往返及 SR 实际加载验证

日期：2026-09-16。基于 `codex/segmentation-export-report` 的 `fea046a`，本轮补充可复现脚本和验证记录，未修改产品实现或本机 Slicer 插件。

## 结论

**SEG 完整往返通过；SR 仅单区域体积报告通过 Slicer 实际加载。** 多个独立 SEG 的关联 SR、自由形状 ROI 与分割混合 SR 均存在当前 Slicer 插件兼容问题，不能宣称全部互通。

环境：macOS 原生 Qt，Slicer **5.12.4**，其内置 dcmqi **1.5.4 / a102298**；使用 `DICOMSegmentationPlugin`、`DICOMTID1500Plugin`。每个阶段使用独立 Slicer 进程及临时 DICOM 数据库。

| 验证项目 | P113 CT（MP1/ph0） | 脑 MR（Thin-3D-T1） |
| --- | --- | --- |
| Slicer Segment Editor 实际编辑 | Margin 5 mm，Apply 可用 | Margin 3 mm，Apply 可用 |
| 原区域体素数 | 111577 | 851022 |
| 扩张后区域体素数 | 528999 | 1276283 |
| 两区域重叠体素数 | 111577 | 851022 |
| Slicer 导出 → 本软件右侧导入 | 两区域逐体素一致 | 两区域逐体素一致 |
| 本软件导出 → Slicer 读回 | 两区域逐体素一致 | 两区域逐体素一致 |
| 单区域 SR 实际加载及表格数值 | 通过 | 通过 |
| 多个独立 SEG 的 SR 实际加载 | 插件抛出 IndexError | 插件抛出 IndexError |
| 自由形状 ROI 与分割混合 SR | 插件抛出 AttributeError | 插件抛出 AttributeError |
| dcmqi 独立解析上述三类 SR | 数值、SEG 引用通过 | 数值、SEG 引用通过 |

P113 单区域 SR 显示体积 **1513.59448957657 cm³**；MR 为 **1276.28300000007 cm³**。同时比对均值、标准差、最小值、最大值和体素数，数值相对误差容限 `1e-12`，单位及追踪标识一致。此项检查报告的数值保真，不代表使用 Slicer 重新计算了全部统计量。

## 实际执行流程

1. 通过 Slicer 的 DICOM 插件加载原始影像和本软件前轮导出的单区域 SEG。
2. 在 Segment Editor 复制基线区域，设置 OverwriteNone，点击已启用的 Margin Apply 按钮，保留相互重叠的两个区域并通过 SEG 插件导出。
3. 在本软件原生窗口，通过实际右侧「导入」→「导入 SEG」按钮加载；进入分割管理并截图。文件选择对话框由脚本提供路径，加载和导出任务仍走实际控制器。
4. 根据 Slicer 的参考体积仿射矩阵，将完整掩膜映射到本软件原始网格，比较全部占用体素的位置，同时核对名称、数量。不是只比较体积或截图。
5. 点击本软件「导出 SR 报告」按钮，生成两个独立 SEG 及对应 SR。再在临时场景删除基线区域，生成单区域报告作为对照。
6. 新 Slicer 进程通过实际插件读回 SEG，在原始影像参考网格逐体素比较；再分别实际加载多区域、单区域及前轮含自由形状 ROI 的 SR，保存表格、加载返回值和异常。
7. 独立运行 dcmqi `tid1500reader`，检查三类报告的数值和分割引用，并核对 Slicer 表格中的数值、单位及 Tracking Identifier。

截图复核发现 P113 的原始层间距约 3 mm，最初尝试的 3 mm Margin 在界面不可用，因此最终使用可点击的 **5 mm** 重做整个流程。Slicer 会按网格离散化扩张范围；这里记录的是其界面设置值，并非每个方向都恰好移动 5 mm。

两组本软件原生界面运行均无 QML 警告。已查看 Slicer 编辑、返回 SEG、单区域 SR 表格及本软件分割叠加截图。验证数据、截图、源 UID 和患者关联信息仅保存在 Git 忽略的 `build/validation/slicer-roundtrip/`，不进入版本库。

## 未通过项及原因

### 多个独立 SEG 的关联 SR

`DICOMTID1500Plugin.py` 在 `load` 中取最后一个分割节点，再调用 `assignTrackingUniqueIdentifier`。该函数按 SR 测量组索引访问该节点的 segment 列表。当前导出为两个单区域 SEG：SR 有两组，而最后一个节点只有一个 segment，因此第二次访问在本机插件第 1204 行抛出 `IndexError: list index out of range`。

异常前已建立两行表格，数值和单位都正确，但**表格出现不等于加载成功**。单区域对照成功加载，支持此定位。后续可优先评估同一源影像的多区域合并为一个 SEG 的导出方式，并重新验证重叠区域、分组引用与 Slicer 实际加载；本轮没有实现该兼容改动。

### 自由形状 ROI 与分割的混合 SR

插件进入平面测量路径，在本机第 763 行无条件访问 `group.finding_type.CodeValue`。本软件导出的中性几何测量没有 Finding 类型，因此抛出 `AttributeError: 'NoneType' object has no attribute 'CodeValue'`，没有生成可用表格。

[DICOM TID 1410](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_A.html#sect_TID_1410) 将 Finding 标为 U（可选）。因此，不能仅凭缺少该字段判定报告无效；也不能为绕开插件异常添加推测的诊断或解剖信息。即使解决该异常，仍需继续验证自由轮廓与混合测量的显示语义。本轮未宣称全量 DICOM 合规认证。

## 复现

从 worktree 根目录运行，需本机 Slicer 已包含两个 DICOM 插件、项目 Python 环境已安装依赖，并有桌面会话。**GUI 阶段串行运行**，避免多个原生窗口争抢焦点。

```sh
# 每次只选一个源序列；生成原始单区域 SEG、自由形状 ROI 混合 SR 及 manifest。
.venv/bin/python tests/manual/validate_dicom_results.py \
  /path/to/one/series "$PWD/build/validation/source-case"

export SOURCE_MANIFEST="$PWD/build/validation/source-case/manifest.json"
export ROUNDTRIP_ROOT="$PWD/build/validation/slicer-roundtrip/case"
SLICER_APP=/Applications/Slicer.app/Contents/MacOS/Slicer
DCMQI_BIN=/Applications/Slicer.app/Contents/lib/Python/lib/python3.12/site-packages/dcmqi/bin

ROUNDTRIP_STAGE=edit "$SLICER_APP" --no-splash --ignore-slicerrc \
  --python-script "$PWD/tests/manual/slicer_seg_roundtrip.py"

QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software .venv/bin/python \
  tests/manual/voxenra_slicer_roundtrip.py "$SOURCE_MANIFEST" "$ROUNDTRIP_ROOT"

ROUNDTRIP_STAGE=verify "$SLICER_APP" --no-splash --ignore-slicerrc \
  --python-script "$PWD/tests/manual/slicer_seg_roundtrip.py"

.venv/bin/python tests/manual/check_slicer_roundtrip.py \
  "$ROUNDTRIP_ROOT" "$SOURCE_MANIFEST" "$DCMQI_BIN"
```

关键产物：`slicer-edit.json`、`slicer-edited-masks.npz`、`voxenra.json`、`slicer-return.json`、`summary.json`、各阶段 PNG、`decoded-reports/`。最终两组 `summary.json` 均记录 SEG 一致、单区域 SR 加载成功，同时明确 `all_sr_gui_loaded: false`。

脚本成功退出表示证据采集及其数值断言通过；**不表示每一种 SR 都加载成功**，必须查看 `sr_gui_loaded`。本轮未改变产品代码，没有重复运行前轮的 1788 项全量回归；新增脚本完成 Ruff、语法检查及上述真实两组影像验证。
