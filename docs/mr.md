# MR 支持

MR 使用现有 2D、平铺、Compare 2D、MPR 和 3D 页签。

## 输入与分组

支持经典单帧 MR Image Storage（.4）、Enhanced MR Image Storage（.4.1）、Legacy Converted Enhanced MR（.4.4），均要求单采样 MONOCHROME1／MONOCHROME2 和可用解码器。Enhanced MR 按共享／逐帧功能组读取位置、方向、像素间距、TR/TE/TI、分量、时相、窗值与像素缩放。主链路引用原文件与零基帧号，不生成伪造的单帧 DICOM。

同一源序列按回波、b 值、扩散方向、时相、分量、StackID 和非空间 DimensionIndexValues 自动分组。未知维度保留独立分组，不猜测缺失信息。列表显示参数，按源序列、数值时相、回波及分量等维度排序，可独立打开或选择 2–4 组对照。内部浏览组使用确定性 ID，源 SeriesInstanceUID 与 SOPInstanceUID 不改写；重复导入、缩略图、工作区和缓存区分帧号。

小型 Enhanced 对象缓存编码数据（每文件最多 64 MiB、合计 128 MiB），只解码所需帧；大型对象使用按帧文件解码。几何或维度不完整时保留 Tag 入口并说明错误。

## 显示与测量

MR 2D 默认打开中间层，优先使用该层有效 DICOM 窗值，缺失时取有限非 padding 像素的 1%～99% 分位范围。翻页保留当前窗；自动窗按当前图像计算。平铺用首次加载切片统一窗值。MPR 初始窗按完整体计算，避免首层窄窗导致过曝；三个切面同步调窗和反白。最小窗宽 0.001，输入三位小数，拖动灵敏度随当前范围变化。

MONOCHROME1 与用户反白叠加；像素经过逐帧 Modality LUT / Rescale，padding 以 NaN 排除统计。长度、角度、ROI、标注与导出沿用现有工具。来源未明确单位时显示 a.u.，不推导 HU、SUV 或 ADC；尚未实现 Real World Value Mapping、厂家私有定量缩放及 ADC 计算。窗值、伪彩、反白、裁剪不改写源像素。

## 空间对照

2–4 序列共用已有对照页签。MR 默认不同步窗值和反白，并使用患者坐标模式。只在相同检查、相同非空 Frame of Reference 且患者 ID 一致时允许空间联动：平行层面按患者坐标匹配覆盖范围内最近切片，不按切片编号硬配对。不同方向显示活动切面的定位线，Alt＋单击图像在其他视口定位对应点；超出视野不强制跳到首尾层。不同空间不自动配准，可分别浏览或显式选择相对进度。

## MPR 与 3D

组内矩阵、方向、间距、参数一致，切片规则、无重复且至少两层时支持 MPR／3D。七种 MPR 布局均可用，四宫格共享已加载体数据。3D 提供 MR 灰度、高信号和 MR MIP，灰度与高信号预设按体数据分位范围映射颜色与透明度，MIP 自动窗使用完整有限强度范围，避免最大值投影大面积截白；支持浮点窗值、自动窗、旋转、缩放、标准方向、裁剪和 PNG 导出。MONOCHROME1 保持源显示极性。MR padding 在 VTK 中始终通过有效像素掩膜排除，裁剪重置也不会恢复无效背景；源数组保持不变。CT 组织预设、CT 去床板、QA、MTF、阈值分割和 VOI 不用于 MR。

薄层、接近各向同性的数据更适合三维展示；厚层或有层间隙的数据即便满足规则采样，插值也不会增加原始信息。体绘制不是分割模型。

## 导出与限制

- PNG 序列导出只包含当前组，并采用各帧的源窗值和缩放；当前视口导出采用当前显示设置。
- DICOM 序列导出保留完整源对象，可能同时包含其他组；可匿名化，像素及逐帧几何保持原样。Tag 按源文件查看完整标签。
- Mosaic、MR Color、波谱、MR 4D 播放、融合、DTI、灌注和 fMRI 分析尚不支持。单帧对象中缺乏标准维度标签的重复切片不会被猜测为时间／扩散维度；MPR／3D 会拒绝。
- 未压缩、RLE 有回归覆盖；JPEG、JPEG-LS、JPEG 2000 依赖实际安装的解码器。NIfTI／NRRD 和原始 MR 不作为应用输入。

## 验证

合成回归覆盖显式／隐式 VR、RLE、逐帧缩放及窗值、padding、源极性、缺损功能组、分组与帧去重、空间匹配、逐组 PNG、完整匿名 DICOM、四窗工作区与 MR 3D。

公开样本包括 Siemens 经典厚层／薄层 T1、Siemens XA10 时相、Philips 幅度／相位与多回波时相、Canon 扩散。逐帧直接核对原始 DICOM，并按患者坐标与上游 NIfTI 参考结果比较存储像素。Philips 参考采用私有 precise scaling，因此参考验证比较未缩放存储值；软件显示值另按标准 Rescale 独立验证，不冒充定量一致。详见 [MR 测试数据](mr-test-data.md)。

格式依据：[DICOM Enhanced MR 功能组](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_A.36.2.4.html)。
