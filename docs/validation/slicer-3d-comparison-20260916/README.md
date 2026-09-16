# P113：Slicer 5.12.4 实际渲染对照与修正

## 结论

同一组 `P113_dicom/MP1/ph0` 在两边读取的全部体素相同。旧实现偏白、条纹重的主要因素是
GPU 体数据坐标表示及射线步长，不是 DICOM 数据丢失或 HU 错误。
修正后 AAA、Bones、Muscle、Lung2、Carotid 五组模板均接近 Slicer 的对应 Maximum 渲染。
AAA 原版配色、透明度和光照参数保持原值；没有通过人为压暗、重新着色来匹配图片。

本次验证当时在 `codex/3d-optimization` worktree 调整，基于前次实现 `06af932`。该成果现已进入 main；后续分支整合与交叉验证见 [main 整合报告](../main-integration-20260916/README.md)。

## 对照条件与数据一致性

- 参考：本机 `/Applications/Slicer.app`，5.12.4 / revision `4e21c19`，VTK 9.6.2。
- 本软件：同机原生 Qt / VTK 9.5.2，实际生产 `VolumeRenderBackend`。
- 数据：`/Users/jun/Documents/test_dicom/P113_dicom/MP1/ph0`，512 × 512 × 99；
  间距 0.9766 × 0.9766 × 3.0 mm；数值 −1000～2976。
- Slicer 使用其 `DICOMScalarVolumePlugin` 的 GDCM reader 读取原 DICOM；本软件使用自身加载器。
  float32 原始体素缓冲 SHA-256 一致：
  `b23c60f54095325b19fbf13e17f28e3aa90ff4358fbd5c6826daea5da252f408`。
- 两边统一为前面观、正交投影、1238 × 928 输出、parallel scale 420.4975801。
  Slicer 的 RAS 与本软件 LPS 经 X/Y 符号转换后相同。每次捕获记录实际相机设置；
  Slicer 同时设置 MRML RenderMode 与 FieldOfView，防止切换质量时恢复默认透视。
- 相同模板曲线、线性插值、白色头灯、背景 RGB (2,7,14)、opacity unit distance 参数 1。
- 参考同时捕获 Normal 和 Maximum。以下数值比较使用 Maximum：明确步长 0.09766 mm、
  自动质量调整关闭、spacing lock 关闭、jitter 关闭。

本地安装最初缺少运行 Intel 版所需的 Rosetta；用户解决后，已实际启动 Slicer 进行捕获。
使用单独创建的 Slicer 实例，未清空用户已有的场景。

## 代码调整

1. **坐标与光照**：将单体 CT/MR GPU 输入设为单位 IJK 网格，actor 矩阵完整承载体素到患者
   LPS 的间距、方向、原点。此前这些信息位于 `vtkImageData`，在各向异性数据上产生不同的
   GPU 梯度光照结果。单变量实验中，相同步长 0.09766 mm，仅改变此表示后 AAA MAE
   从 16.84 降至 0.07。裁剪 mask 使用同一体素网格；回归检查斜轴数据的患者坐标。
2. **采样**：默认采用最小体素间距的 1/4（此组为 0.24415 mm），同时固定交互与静止质量。
   四分之一体素已经接近参考 Maximum，开销低于十分之一体素；不默认加入颗粒状 jitter。
3. **CT 调窗**：按 Slicer 普通调窗公式，上下平移量取源强度范围的一半与视口短边的比值；
   水平伸缩围绕透明度曲线完整范围的中心。AAA 上下移动视口高度的 10%，从原来
   27.618 HU 改为 198.8 HU。颜色与透明度一起变换；MR 的原有调窗保持原有行为。
4. **XRay 回归修正**：提高采样密度暴露了之前重复乘射线步长的问题。VTK 已做采样透明度
   校正，归一化改用 opacity unit distance；原生测试验证不同射线密度下曝光基本一致。
5. PET 单体保留原先物理网格及采样约定；融合后端不经本次单体坐标转换路径。

模板仍为 20 个 CT 和 3 个 MR；本次没有新增重复模板。

## 结果

固定图像区域 `(435,290)-(815,660)`，无对齐变形、亮度或颜色修正。
MAE 为每个 RGB 通道绝对差的平均值，范围 0～255；它仅衡量本组匹配视角的渲染差异。

| 本软件 / Slicer 对应模板 | 修正前 MAE | 修正后 MAE |
| --- | ---: | ---: |
| AAA / CT-AAA | 21.47 | 1.06 |
| Bones / CT-Bone | 13.61 | 0.20 |
| Muscle / CT-Muscle | 10.84 | 0.36 |
| Lung2 / CT-Lung | 11.69 | 1.77 |
| Carotid / CT-Coronary-Arteries-3 | 18.92 | 0.66 |

AAA 的图像差异降低约 95%。残余细纹与采样步长有关；源数据 3 mm 层距的结构不能通过
显示调整恢复为薄层扫描。不能将上述结果外推为全部数据、全部视角和全部模板逐像素一致。

### 调窗

对照脚本依据 Slicer 5.12.4 源码，直接在 Slicer 原生传递函数上施加相当于视口
10% 位移的变换，再由 Slicer 实际渲染；本软件使用生产 `drag_volume_window`。
这是可重复的参数对照，不是对 Slicer 鼠标事件派发的自动化测试。

四方向调窗的 MAE 为：上 1.13、下 1.29、右 1.00、左 1.08。
本软件自己的鼠标拖动、数值状态及重置由原生 QML/Qt 测试另外覆盖。
Ctrl 单独调透明度不在本次实现范围。

### 耗时

本机 1238 × 928 像素输出、预热后 3 次中位数：AAA 约 5.4 → 13.5 ms，五组模板
修正后约 13～17 ms。增加了采样开销；这些是渲染调用计时，不是跨设备 FPS 保证。
更大的窗口和更大的数据仍可能更慢。

## 验证

- Headless 回归：159 passed、3 skipped；覆盖体素/患者坐标、传递函数、调窗、mask、
  MR、PET、QML 模板、MPR 和加载响应。需要原生窗口的检查由以下 smoke 单独验证。
- 原生 `tests/manual/smoke_3d.py`：20 个 CT 模板非空且不同、XRay 曝光稳定、六方向、
  鼠标调窗/重置、自由手绘裁剪、去床、Tab 切换/关闭/重开全部通过。
- 原生交互中与松手后像素差为 0，源像素不变。
- 所有影像截图仅在被忽略的 `build/validation/slicer-comparison/`，未加入 Git。

## 本地输出与复现

- `build/validation/slicer-comparison/aaa-comparison.png`：Slicer / 修正前 / 修正后。
- `presets-comparison.png`：五组模板；`windowing-comparison.png`：四方向调窗。
- `reference/settings.json`：Slicer 版本、体素校验、相机、灯光、采样与变换参数。
- `viewer/settings.json`：本软件窗值与计时；`differences.json`：区域及差值。

在本 worktree 中，使用有桌面 OpenGL 的 Python 环境：

```sh
SLICER_DICOM_DIR=/path/to/one/CT/series SLICER_CAPTURE_ROOT=/absolute/local/output/reference \
  /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --ignore-slicerrc \
  --python-script /absolute/path/to/capture_slicer.py
PYTHONPATH=src python docs/validation/slicer-3d-comparison-20260916/capture_viewer.py \
  /path/to/one/CT/series /absolute/local/output/reference /absolute/local/output/viewer
python docs/validation/slicer-3d-comparison-20260916/compare_images.py /absolute/local/output
```

图片比较脚本的区域针对本次 1238 × 928 相机协议；不同窗口需重新定义区域。

## 参考实现

- [Slicer 5.12.4 GPU 映射器与 actor 变换](https://github.com/Slicer/Slicer/blob/v5.12.4/Modules/Loadable/VolumeRendering/MRMLDM/vtkMRMLVolumeRenderingDisplayableManager.cxx)
- [Slicer 5.12.4 三维调窗公式](https://github.com/Slicer/Slicer/blob/v5.12.4/Modules/Loadable/VolumeRendering/MRMLDM/vtkMRMLVolumeRenderingWindowLevelWidget.cxx)
- [Slicer 5.12.4 采样步长](https://github.com/Slicer/Slicer/blob/v5.12.4/Modules/Loadable/VolumeRendering/MRML/vtkMRMLVolumeRenderingDisplayNode.cxx)
- [Slicer 5.12.4 模板原始参数](https://github.com/Slicer/Slicer/blob/v5.12.4/Modules/Loadable/VolumeRendering/Resources/presets.xml)
- [VTK 9.5.2 Additive 透明度步长校正](https://github.com/Kitware/VTK/blob/v9.5.2/Rendering/VolumeOpenGL2/vtkOpenGLVolumeOpacityTable.cxx)

Slicer 许可证见仓库 `licenses/Slicer.txt`。本次记录补充并更新前一次
[小赛看看对照](../xiaosai-3d-comparison-20260915/README.md) 中关于偏白、采样和调窗的发现。
