# 20 个公开 DICOM 逐文件界面核验

日期：2026-09-16。代码：`codex/compressed-dicom`，以 `9453995` 为基础加入本轮提示修正。环境：macOS、Python 3.13、工作树自带 `.venv`、Qt Cocoa 原生窗口、Qt Quick software 渲染。

**结论：12 个可以正常阅片（7 个压缩、5 个未压缩对照），8 个按当前能力边界受限。20 项验证通过，不能解释为 20 个都能显示。**

每个文件使用独立应用实例：点击导入 → 文件选择器选中单个原始文件 → 导入 → 点击序列和 2D → 检查实际 QML 画面 → 打开 Tag。没有用扫描结果直接注入代替本地导入。正常影像核对分辨率、切片数量、默认画面、调窗后实际图像字节变化；单张或失败视图不能启动播放。19 个已入库文件均成功打开 Tag；缺少元数据的文件不能入库。正常导入进度窗口自动关闭，导入失败窗口保留并可点击“确定”关闭。

截图检查确认头部、肩部、低分辨率 MR 和全身灰度图正常；64×64 MR 放大后模糊属于源图分辨率。此次无 UI 卡死或 QML 警告，测试日志中有底层库弃用警告，以及旧 JPEG 混合 VR 文件的预期读取警告。

## 逐文件结果

| # | 文件 | 类型 | 界面结果 | 截图 |
| --- | --- | --- | --- | --- |
| 1 | `MR_small_RLE.dcm` | RLE Lossless | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_RLE.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_RLE-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_RLE-default.png) |
| 2 | `emri_small_RLE.dcm` | RLE Lossless | 缺少 Enhanced MR 功能组；2D 禁用，Tag 可查看 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_RLE-blocked.png) / [不可用原因](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_RLE-reason.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_RLE-tag.png) |
| 3 | `MR_small_jpeg_ls_lossless.dcm` | JPEG-LS Lossless Image Compression | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jpeg_ls_lossless.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jpeg_ls_lossless-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jpeg_ls_lossless-default.png) |
| 4 | `emri_small_jpeg_ls_lossless.dcm` | JPEG-LS Lossless Image Compression | 缺少 Enhanced MR 功能组；2D 禁用，Tag 可查看 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_ls_lossless-blocked.png) / [不可用原因](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_ls_lossless-reason.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_ls_lossless-tag.png) |
| 5 | `MR_small_jp2klossless.dcm` | JPEG 2000 Image Compression (Lossless Only) | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jp2klossless.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jp2klossless-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small_jp2klossless-default.png) |
| 6 | `emri_small_jpeg_2k_lossless.dcm` | JPEG 2000 Image Compression (Lossless Only) | 缺少 Enhanced MR 功能组；2D 禁用，Tag 可查看 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_2k_lossless-blocked.png) / [不可用原因](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_2k_lossless-reason.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small_jpeg_2k_lossless-tag.png) |
| 7 | `MR2_J2KR.dcm` | JPEG 2000 Image Compression (Lossless Only) | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KR.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KR-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KR-default.png) |
| 8 | `693_J2KR.dcm` | JPEG 2000 Image Compression (Lossless Only) | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_J2KR.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_J2KR-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_J2KR-default.png) |
| 9 | `MR2_J2KI.dcm` | JPEG 2000 Image Compression | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KI.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KI-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_J2KI-default.png) |
| 10 | `JPEG-LL.dcm` | JPEG Lossless, Non-Hierarchical, First-Order Prediction (Process 14 [Selection Value 1]) | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG-LL.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG-LL-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG-LL-default.png) |
| 11 | `JPEG-lossy.dcm` | JPEG Extended (Process 2 and 4) | 明确显示 JPEG Extended 12 位精度不支持；Tag 正常 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG-lossy.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG-lossy-tag.png) |
| 12 | `SC_rgb_jpeg.dcm` | JPEG Baseline (Process 1) | 解码可用，但彩色主阅片暂不支持；中文提示、Tag 正常 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/SC_rgb_jpeg.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/SC_rgb_jpeg-tag.png) |
| 13 | `SC_rgb_jpeg_gdcm.dcm` | JPEG Lossless, Non-Hierarchical, First-Order Prediction (Process 14 [Selection Value 1]) | 解码可用，但彩色主阅片暂不支持；中文提示、Tag 正常 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/SC_rgb_jpeg_gdcm.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/SC_rgb_jpeg_gdcm-tag.png) |
| 14 | `JPEGLSNearLossless_16.dcm` | JPEG-LS Lossy (Near-Lossless) Image Compression | 缺少导入必需元数据；导入未完成提示，确认可关闭 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEGLSNearLossless_16.png) |
| 15 | `MR_small.dcm` | 未压缩对照 | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR_small-default.png) |
| 16 | `emri_small.dcm` | 未压缩对照 | 缺少 Enhanced MR 功能组；2D 禁用，Tag 可查看 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small-blocked.png) / [不可用原因](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small-reason.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/emri_small-tag.png) |
| 17 | `MR2_UNCR.dcm` | 未压缩对照 | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCR.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCR-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCR-default.png) |
| 18 | `MR2_UNCI.dcm` | 未压缩对照 | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCI.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCI-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/MR2_UNCI-default.png) |
| 19 | `693_UNCR.dcm` | 未压缩对照 | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_UNCR.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_UNCR-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/693_UNCR-default.png) |
| 20 | `JPEG2000_UNC.dcm` | 未压缩对照 | 正常显示，1 张，调窗改变实际显示像素 | [视图](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG2000_UNC.png) / [Tag](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG2000_UNC-tag.png) / [默认窗](/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916/_validation/ui-each/JPEG2000_UNC-default.png) |

## 本轮修正

两张彩色 JPEG 的解码和缩略图正常，但主阅片之前显示英文内部错误 `Stack rendering ... shape=(..., 3)`。现在区分彩色阅片能力限制与压缩解码错误，显示中文/英文可切换的提示，并保留缩略图、Tag 和 PNG 导出用途。本轮未把彩色主阅片实现为支持。

## 验证记录和边界

- 完整离屏 QML：20 项通过。
- macOS 原生窗口完整流程：20 项通过。
- Enhanced MR 独立提示窗口补充检查：4 项通过。
- 压缩解码、导入界面、语言设置相关回归：58 项通过。
- 20 份源 DICOM 的 SHA-256 均与下载 manifest 一致；没有改写源文件。
- 灰度正常样本都是单张，无法验证真实多层序列的连续翻页、MPR、3D 或性能。四份 Enhanced MR 均缺少必要帧功能组，不能替代合法 Enhanced MR 重建验收。
- 样本仍保留原始重复 UID，应逐个导入；不能把整个根目录作为一组无重复影像导入。
- 本轮是源码环境验证，不代表 Windows 或已安装旧版本已经包含修改。

机器可读结果：`ui-each-results.json`。源码测试：`tests/manual/test_public_compressed_samples.py`。原有像素解码与无损配对结果保留在 `validation.json` 中。
