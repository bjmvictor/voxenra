# 其他 DICOM：Slicer 实机 3D 对照

## 结论

在 P113 以外选了 7 组本地数据，5 组完成了 36 个同数据、同曲线、同视角的画面对照。
这些画面未见方向翻转、比例错误或整体发黑；颜色、结构和透明度接近 Slicer。
另两组在导入阶段受阻，不能记作渲染通过。

发现并修复一个实际问题：1 mm 薄层脑 MR 在原先四分之一体素射线步长下会触发本机
GPU hang。MR 改为最小体素间距的 1/2 后，两组 MR 的 18 个画面均正常完成。
CT 仍采用 1/4，PET 保持原有设置。本次在 `codex/3d-optimization` worktree 完成。

## 数据与结果

数据位于本机 `Documents/test_dicom`。尺寸按列 × 行 × 层，间距按列、行、层，单位 mm。
CT 采用 AAA / CT-AAA、Bones / CT-Bone；MR 采用 MR General、MR Bright、MR MIP。
每个模板分别检查前面观 A、左侧观 L、斜面观。

| 数据 | 尺寸 | 实际间距 | 配对数 | 前景 RGB 平均绝对差范围 |
| --- | --- | --- | ---: | ---: |
| CatPhan604 | 512 × 512 × 93 | 0.5112 / 0.5112 / 1.9897 | 6 | 0.04–1.35 |
| PET-CT--L 中的小动物 CT | 256 × 512 × 457 | 0.13672 / 0.13672 / 0.18 | 6 | 0.02–3.57 |
| py_test_path/py_test_path2 中的 CT | 512 × 512 × 320 | 0.9766 / 0.9766 / 0.6 | 6 | 0.25–3.26 |
| Thin-3D-T1：薄层脑 MR，斜位矢状采集 | 256 × 256 × 192 | 1 / 1 / 1 | 9 | 0.09–0.32 |
| 01_T1_Brain_HFS：厚层脑 MR | 256 × 256 × 35 | 1.015625 / 1.015625 / 4.8 | 9 | 0.41–3.48 |

差值范围是各组所有配对画面的最小/最大 MAE，每通道取值 0–255，不是百分比。
它衡量这些条件下的渲染相似度，不代表其他数据或所有模板均通过验证。

### 画面检查

- 小动物 CT 的采集方向含反向行轴和反向层轴，两边经物理坐标核对后方向一致。
- 薄层 MR 含斜位方向，正面、侧面、斜面的位置与比例一致。
- 厚层 MR 的重建条纹和模糊在两边均存在。该组 SliceThickness 为 4 mm，实际层间距约
  4.8 mm；不能靠配色把缺少的层间细节补出来。
- 模体和小动物支撑物仍可见；本次不应用去床或裁剪，以免掩盖源数据差异。
- Slicer 原生 MR-Default 呈棕色、较不透明，本软件 MR General 呈灰色、较透明。
  这是模板选择的区别；额外保存原生默认模板对照图，并与同曲线的定量比较分开解释。

## MR GPU 问题与调整

在相同 1238 × 928 输出下，薄层 MR 的第一次 MR General 前面观渲染：

1. 本软件 0.25 mm 步长在批量进程和独立进程均出现
   `MTLCommandBufferErrorDomain Code=2: Caused GPU Hang Error`，进程退出 134。
2. Slicer Maximum 也曾出现 GPU hang；改为 Normal 后全部 MR 对照完成。
3. 本软件仅将步长改为 0.5 mm，9 个薄层 MR 画面完成。正式代码按 MR 元数据选择
   `min(column_spacing, row_spacing, slice_spacing) / 2`，厚层 MR 为 0.5078125 mm。
4. 交互和静止仍使用固定步长，两组 MR 的 18 个画面逐像素检查均一致，源体素未改变。

这是本机上的可重复现象和修正结果，未定位 Apple GPU 驱动内部原因，也不保证所有设备
和更大体数据均不会遇到 GPU 错误。Slicer Normal 开启 spacing lock，本软件使用固定的
最小间距一半；各向异性数据的实际采样密度可能不同，不能声称两边参数完全相同。

## 未完成配对的两组

| 数据 | 观察 | 本次处理 |
| --- | --- | --- |
| C002 Full Dose Images，280 层 CT | 280 张切片有 280 个不同 FrameOfReferenceUID。本软件报“同一序列的 FrameOfReferenceUID 不一致”；Slicer 可以加载并生成 AAA 图像 | 记录导入兼容性差异，未绕过一致性检查，未计入 36 对 |
| 头模，696 层 CT | 本软件可以构建体数据；Slicer 在原 DICOM 解码期间 SIGSEGV，GDCM、DCMTK 尝试均失败 | 无有效 Slicer 参考图，未计入通过。数据含异常 VR 编码，但未证明这就是崩溃原因 |

这两组没有修改源 DICOM。本次对照未实现 C002 的兼容导入，也未修复 Slicer 自身的读取异常。

## 对照方法

- Slicer 5.12.4 / VTK 9.6.2；本软件生产 `VolumeRenderBackend` / VTK 9.5.2，同一台 Mac。
- 使用独立启动的 Slicer 实例执行官方 DICOMScalarVolumePlugin reader，未清空用户已有场景。
  本软件通过生产 DICOM 加载器和原生 Qt/OpenGL 后端捕获。这是可重复的渲染对照，
  不是完整 GUI 导入操作自动化。
- 按 ImagePositionPatient 在切片法向量上的投影排序，不能按文件名排序。
- 两边独立解码。根据 IJK→LPS 矩阵核对有符号轴置换，调整内存轴顺序后，5 组完整
  float32 体素 SHA-256 均完全相同；无图像重采样。这 5 组没有 NaN/padding mask。
- 统一患者空间相机、正交投影、输出尺寸和 RGB (2,7,14) 背景。Slicer 同时设置
  MRML RenderMode、FieldOfView 与相机；RAS→LPS 转换 X/Y 符号。
- CT 使用 Slicer 原生同名预设和 Maximum 质量。MR 使用 Normal，并将本软件模板的
  颜色、透明度、光照参数导入 Slicer，确保比较渲染本身。另拍原生 MR-Default 供风格参考。
- 差值在两张图的可见前景并集计算：任一通道偏离背景超过 12，排除右上角方向标记。
  不做对齐变形、调色或亮度补偿。并排预览只做相同区域裁切与等比缩放，原始 PNG 保留。

## 验证与性能

- 相关回归：`test_volume_display.py`、`test_enhanced_mr.py`、
  `test_standalone_pet_volume.py`，**75 passed**。
- 5 组共 36 对捕获均非空，体素校验通过；逐图检查全部并排预览。
- 新修正后重新捕获的两组 MR 和 320 层 CT，共 24 个画面交互与静止像素一致。
- 渲染调用耗时：CT 约 27–184 ms，MR 约 2–53 ms（预热后 3 次中位数）。
  小动物 CT 的斜面最慢；这些是本机调用计时，不是 GPU 同步计时或跨机器 FPS 保证。

## 本地证据

输出根目录：`build/validation/slicer-multicase/`，全部影像和含本地源路径的清单均被 Git 忽略。

- `comparison/overview.png`：5 组代表画面，左 Slicer、右本软件。
- `comparison/all-pairs.png`：36 对总览；同目录有每一对的独立大图。
- `comparison/mr-thin-default-presets.png`、`mr-thick-default-presets.png`：原生默认模板区别。
- `manifest.json`、`reference.json`、`viewer.json`、`differences.json`：几何、体素摘要、参数和差值。
- `mr-thin-quarter-isolated.log`、`mr-thin-half-step.log`、`mr-thin-final.log`：MR 修正前后。
- `head-sorted.log`、`head-dcmtk.log`：头模读取失败；`pytest.log`：回归结果。

## 复现

同目录提供 `prepare_cases.py`、`capture_slicer.py`、`capture_viewer.py`、`compare_images.py`。
准备脚本输入 JSON 数组，每项为 `id`、DICOM `files` 路径列表和 `presets` 映射，例如
`[["aaa", "CT-AAA"], ["bones", "CT-Bone"]]`；MR 映射的 Slicer 名称填 `null`，使用相同曲线。
执行 `PYTHONPATH=src python prepare_cases.py selection.json OUTPUT` 生成清单。

在 worktree 中使用有桌面 OpenGL 的环境，每个病例启动独立进程，顺序运行以隔离崩溃：

```sh
COMPARISON_ROOT=/absolute/local/output COMPARISON_CASE=mr-thin \
  /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --ignore-slicerrc \
  --python-script /absolute/path/to/capture_slicer.py

COMPARISON_CASE=mr-thin PYTHONPATH=src python \
  docs/validation/slicer-multicase-20260916/capture_viewer.py /absolute/local/output

python docs/validation/slicer-multicase-20260916/compare_images.py /absolute/local/output
```

最后一步要求所有计划配对图像完整。`DIAGNOSTIC_SAMPLE_DIVISOR=4` 可仅在捕获脚本中复现
原 MR 步长；本次正式结果未设置该覆盖变量。头模的原生进程崩溃需由外部记录退出码，
不能当作 Python 异常恢复后继续比较。
