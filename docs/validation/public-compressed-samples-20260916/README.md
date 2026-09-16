# 网上公开压缩 DICOM 验证 · 2026-09-16

样本：`/Users/jun/Documents/test_dicom/Compressed_DICOM_Public_20260916`。从 pydicom v3.0.2 和 pydicom-data 固定提交 `39a2eb31815eec435dc26c322c27aec5cfcbddb6` 下载 20 个 DICOM，共 6,446,876 字节；其中 14 个压缩样本，6 个未压缩对照。源 URL、上游哈希和 SHA-256 清单、许可证、中文导入说明保留在该文件夹。文件未转换、未改写 UID 或标签。

## 结果

- 13 个压缩样本像素解码通过；JPEG Extended 12 位当前明确不支持。
- 8 个无损配对与原始参考逐像素一致；10 个适用样本缩略图及 PNG 导出通过。
- 7 个正常单帧灰度样本通过完整离屏 QML 导入、显示和调窗，无 QML 警告；CT 头部、MR 肩部截图人工检查正常。
- 当前数据以单帧为主，不用来声明 MPR/3D 已验证。三个 emri 10 帧样本缺少共享/逐帧功能组，解码通过但必须拒绝伪造几何重建，已移到限制样例目录。
- JPEG 2000 有损 MR 与上游对应解码参考最大差 1；这不是对压缩前损失的度量。JPEG-LL 与 JPEG2000_UNC 不是已确认的无损配对，不用于无损一致性断言。
- 本轮代码回归 **85 passed**；额外公开样本界面回归 **7 passed**。

## 由样本发现并修正

1. `SC_rgb_jpeg.dcm` 的旧式混合 VR 导致按路径读取 Pixel Data 时误解析偏移表，而完整 `dcmread` 能恢复。现在对不超过 64 MiB 的文件，在流式解析 ValueError 时回退到完整解析，仍使用相同指定解码器并保持原文件不变。缩略图元数据同时保留；逐帧导出已经输出帧时不回退，避免重复帧。
2. pydicom/GDCM 明确拒绝 12 位 JPEG Extended。新增明确能力提示、更新支持文档和中英文手册，避免把它含糊归为损坏文件。

数据根目录不可一次性全部导入作为正常阅片测试：不同压缩版本保留相同 UID，正常去重可能生效。应按 README 一次导入一个具体样本目录，限制／仅解码样本分别放置。

## 复跑

```sh
VOXENRA_COMPRESSED_SAMPLE_DIR="$HOME/Documents/test_dicom/Compressed_DICOM_Public_20260916" \
  PYTHONPATH=src:tests QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  uv run --group dev python -m pytest tests/manual/test_public_compressed_samples.py -q
```

仅在线获取了公开影像，没有上传用户文件。本轮不包含 Windows 或完整安装包验收。
