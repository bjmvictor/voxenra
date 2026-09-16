# 压缩像素支持验证 · 2026-09-16

基于 main `8baa018`，工作分支 `codex/compressed-dicom`。本记录针对 DICOM Pixel Data 压缩，与 ZIP/RAR 等归档验证不同。

## 实现

- 固定 pydicom 3.0.2、python-gdcm 3.2.1、pylibjpeg 2.1.0、pylibjpeg-openjpeg 2.5.0、pyjpegls 1.5.1；独立 `uv sync --locked` 环境验证。
- RLE / JPEG Baseline、Extended、Lossless / JPEG-LS / JPEG 2000 采用指定插件；读取、重建、缩略图、PNG 导出共用策略。
- 缺少插件、未支持语法、像素解码失败分别提供中英文错误；PNG 失败清理临时文件；原 DICOM 复制不依赖解码。
- 增加原生依赖／插件元数据打包钩子、冻结程序校验入口及 macOS / Windows 产物上传前的检查。

## 结果

- CT/MR/Enhanced MR、导出、PET、MPR、4D、打包参数、QML、语言与手册定向回归：**237 passed、2 skipped**。原生窗口用例在离屏环境跳过。
- 随后新增有损误差、冻结校验失败检测和真实 QML 压缩 MR 播放测试，压缩专项最终 **19 passed**。与上述批次存在重复，不相加作为全量测试数。
- 无损合成数据逐像素比对，包含 signed 16-bit 负值、rescale、完整体数据；Enhanced MR 指定帧与逐帧缩放一致。
- JPEG Lossless RGB 使用 pydicom 3.0.2 自带公开测试文件验证色块；JPEG-LS 近无损和 JPEG 2000 有损分别验证形状与误差上限。未据此扩大彩色主阅片支持范围。
- 三种无损压缩 MR 通过真实离屏 QML 完成导入、2D 播放、切换 MPR，未出现 QML 警告。
- macOS arm64 使用项目正式解码钩子构建独立 PyInstaller 冻结验证程序，清除 PYTHONPATH/PYTHONHOME 后，RLE、JPEG-LS、JPEG 2000、JPEG Baseline 四种合成输入的形状与已知像素摘要全部一致；九种配置的压缩语法均检测到指定插件。

冻结验证程序复用正式解码模块与钩子，不等同于已经生成、验收完整 DMG。Windows 未在本机执行，已加入便携版和安装版的构建验证门槛，须以对应工作流通过为准。JPEG Extended 与 Process 14 非 SV1 此轮验证了插件可用，尚未增加独立的逐像素金标准样本。

本机产物：`build/codec-check/result.json`、`build/codec-probe/`；日志：`/tmp/codec-regression.log`、`/tmp/codec-extra.log`、`/tmp/codec-freeze.log`。生成数据均为合成影像，不包含用户影像，不提交到 Git。
