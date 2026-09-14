# README 功能截图

共 30 张 PNG 与 1 段 GIF。README 内嵌 29 张静态图和 4D 动画，并提供 4D 高清静态图链接。图片来自真实 Qt / VTK 应用界面，保留原始分辨率；动画按实际相位画面缩小编码。

## 场景与来源

| 文件 | 场景 | 数据与生成方式 |
| --- | --- | --- |
| `01-2d-measurement.png`、`02-mpr-segmentation.png` | CT 阅片、ROI、MPR 分割 | 沿用原有 CT 示例截图，2026-09-08 |
| `04-volume-rendering.png`、`05-pet-ct-fusion.png`、`06-fusion-3d.png` | 原生 3D、PET/CT 融合、融合 3D | 沿用原有 CT / PET 示例截图，2026-09-08 |
| `03-4d-mpr.png`、`03-4d-playback.gif` | 三平面 CT 十时相 | 本地 `test_dicom/P113_dicom/MP1`，10 相位 × 99 层，2026-09-14 重拍 |
| `07-mr-reading.png` | MR 原始 Stack、自动窗 | 公开 Thin-3D-T1，192 层、1 mm |
| `08-enhanced-mr-compare.png` | 四组 2D 对比 | 公开 Philips `IM_0035_fMRI.dcm`，两回波 × 两时相 |
| `09-mpr-compare.png` | 双序列 MPR 六宫格 | 公开 `01_T1_Brain_HFS` / `02_T1_Brain_HFDR` |
| `10-2d-layout.png` | Stack / Axial / Coronal / Sagittal 四视口 | 公开 Thin-3D-T1 |
| `11-mpr-3d-layout.png` | MPR 四宫格与带切面参考的原生 3D | 公开 Thin-3D-T1；原生窗口抓取包含 VTK 子窗口 |
| `12-mr-montage.png` | 三列平铺、BlackBody 伪彩 | 公开 Thin-3D-T1 |
| `13-detached-tabs.png` | 主窗口与独立页签同时阅片 | 公开 Thin-3D-T1；只抓取应用自己的纯色背景及两个真实窗口 |
| `14-oblique-mpr.png` | 十字线与三维旋转后的斜切面 | 公开 Thin-3D-T1 |
| `15-mixed-import.png` | 文件夹、DICOM、ZIP 混合选择 | 临时生成的合成 DICOM 文件与 ZIP |
| `16-pacs-browser.png` | DICOMweb 查询结果与序列选择 | `tests/test_pacs.py` 的本机回环 HTTP 服务器与合成检查 |
| `17-workspace.png`、`18-export.png` | 工作区恢复、影像与测量导出 | 合成水模 CT |
| `19-water-qa.png`、`20-voi.png` | 水模 QA、VOI 截面与统计 | 测试辅助脚本生成的合成水模 / CT |
| `21-dicom-tags.png` | 搜索像素与几何标签 | 公开 Thin-3D-T1；搜索 `0028` 标签组 |
| `22-display-settings.png` | 四角信息与显示偏好 | 隔离设置的实际应用界面 |
| `23-pacs-import.png` | PACS 下载完成、加入序列列表与自动打开阅片 | 本机 DICOMweb 测试服务器；实际下载 3 个合成 DICOM，并检查落盘文件 |
| `24-compact-sidebars.png` | 左侧缩略图栏与右侧直接操作栏同时收起 | 公开 Thin-3D-T1 |
| `25-theme-dark.png`、`26-theme-light.png` | 深色与浅色主题 | 相同公开 Thin-3D-T1、MPR 主视图布局 |
| `27-thick-slab.png` | 三方向 20 mm MIP 厚层投影 | 公开 Thin-3D-T1；实际重建厚层画面 |
| `28-mtf-analysis.png` | 点源 MTF / FWHM 曲线与指标 | 脚本生成的高斯点源 CT；实际框选 ROI 并等待分析完成 |
| `29-volume-crop.png` | 原生 3D 圈选裁剪后旋转观察 | 公开 Thin-3D-T1；检查裁剪已生效后抓取 VTK 画面 |
| `30-offline-manual.png` | 英文离线手册、编辑与撤销重做说明 | 实际英文界面与随软件分发的手册 |

`07`–`30` 均于 2026-09-14 补拍。MR 样本的上游来源、许可与校验信息见 [MR 测试数据](../mr-test-data.md)。新增真实影像场景在内存中使用 `MR Demo` / `CT Demo` / `Anonymous` 显示标签并隐藏身份字段；原始 DICOM、几何与像素不改动，也不将源 DICOM 加入仓库。

MR 分组浏览不等于 fMRI 分析，对比截图不表示已配准，伪彩和体绘制不代表组织分割结果。水模和 MTF 截图使用合成数据展示工具，不是设备质控报告；保留软件实际计算结果及质量提示。

## 补拍与复现

在具有原生桌面的 macOS 上，从仓库根目录执行。样本目录结构见上方 MR 测试数据文档。

```bash
QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software PYTHONPATH=src:tests:tests/manual \
  uv run --group dev --with pillow python tests/manual/capture_readme.py \
  --samples "$HOME/Documents/Voxenra-MR-TestData" \
  --ct-samples "$HOME/Documents/test_dicom/P113_dicom/MP1" \
  --output /tmp/voxenra-readme
```

可加 `--scene 11-mpr-3d-layout` 只拍一个场景；不传 `--ct-samples` 时跳过 4D。脚本逐场景使用独立进程、临时设置并关闭自动恢复，不覆盖个人工作区。PACS 示例仅查询与下载测试脚本启动的本机服务器数据；下载文件位于临时目录，并校验导入数量、落盘文件和阅片页签。

通用界面使用以下脚本复现：

```bash
QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software PYTHONPATH=src:tests:tests/manual \
  uv run --group dev python tests/manual/capture_manual.py /tmp/voxenra-manual
```

将 `import`、`workspace`、`export`、`water-qa`、`voi-ct`、`corners` 的输出依次对应到 `15`、`17`、`18`、`19`、`20`、`22`。这组脚本使用临时合成数据，不需要真实影像。

## 动画与检查

- 4D GIF 包含 10 个不同相位，等待实际切面重建完成后逐帧抓取，脚本断言模态像素发生变化。
- GIF 宽度 1100 px，每帧 240 ms，循环播放，约 1.4 MiB；采用统一色表。固定帧间隔用于展示，不代表应用实际播放帧率。
- 每张图片检查加载完整性、文字、布局、身份显示及 3D 内容；分离窗口图检查无其他应用内容。
- 文档校验涵盖本地链接、HTML 图片引用、图片可解码性、GIF 帧数与截图脚本语法；截图不加入应用资源包，不增加安装包体积。
