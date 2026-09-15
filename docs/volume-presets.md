# 3D 模板参数与扩展约定

3D 模板由 `volume_presets.py` 汇总，新增 CT 曲线位于 `volume_ct_presets.py`，
类型定义位于 `model/volume_models.py`。运行时使用内置数据，无需安装参考软件或联网。
现有 20 个 CT 可用模板及 3 个 MR 模板；模板只调整强度到颜色、透明度、光照的映射，
不做器官分割，也不会改变原始体素。

## 默认显示与调窗

CT 新建 3D 视图（包括 MPR 内的 3D 视图）默认使用 **AAA（骨骼与血管）**，
采用独立于二维切片的 3D 窗和暖色体渲染。MR 保持自动窗和 MR 通用模板；
其他模态保持通用灰度模板。手动选择通用、MIP、XRay 时仍使用序列默认窗。

上下拖动同时平移颜色与透明度曲线；左右拖动同时拉伸或压缩曲线。
这与 [3D Slicer 的体渲染调窗](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html)
采用的交互含义一致。上移提高 WL，右移增加 WW；使用拖动起始值及总偏移，
不会累加事件误差。CT 窗宽下限为 1，MR 为 0.001，不支持负窗宽反相。

3D 调窗面板保留 WL/WW 数值输入，说明颜色与透明度同时变化，并隐藏二维切片窗预设和
保存二维窗模板入口。3D 模板在专用模板面板选择。

视角 `VolumeViewState` 与显示 `VolumeDisplayState` 分离。
切换模板或再次点击当前模板恢复该模板默认窗，保留相机姿态；调窗重置恢复当前模板；
模板重置和全部重置恢复模态默认模板（CT 为 AAA），全部重置还恢复相机和裁剪状态。
后端收到只有模板 ID 的显示状态时，优先应用该模板默认窗，再回退到序列默认窗。

## 参数约定

颜色点为 `(t, r, g, b)`，透明度点为 `(t, alpha)`，实际强度为：

```text
HU = WL + WW × (t − 0.5)
```

RGB、alpha 必须在 0～1。位置 t 可超出 0～1：它表示相对于有效调窗区间的位置，
这样可保留 −3024 / 3071 等边界控制点，又不必以整个 HU 范围作为拖动灵敏度。
Slicer 来源模板使用其 `effectiveRange` 确定 WL/WW；默认状态精确恢复原 HU 控制点。

模板分别保存颜色、透明度、混合模式、环境光、漫反射、镜面反射和镜面指数。
透明度单位距离为 1 mm；当前引用的 Slicer 模板梯度透明度均为常数 1，无需额外梯度函数。

| ID | 分组 / 名称 | 默认 WL / WW | 混合模式 |
| --- | --- | --- | --- |
| general | General / 通用 | 序列默认窗 | composite |
| mip | General / MIP | 序列默认窗 | mip |
| xray | General / XRay | 序列默认窗 | additive |
| aaa | General / AAA（骨骼与血管） | 281.6460 / 276.1800 | composite |
| cardiac | General / 心脏 | 91.3758 / 338.1265 | composite |
| muscle | General / 肌肉 | 132.1645 / 575.1430 | composite |
| red | General / 红色血管 | 375 / 550 | composite |
| bone | CT / 骨骼 | 300 / 1500 | composite |
| lung | CT / 肺 | -400 / 1500 | composite |
| bones | CT / 骨骼（自然色） | 312.4696 / 657.8308 | composite |
| lung2 | CT / 肺 2（密度分色） | -499.5000 / 201 | composite |
| bone-plate | CT / 骨骼与钢板 | 1160 / 2080 | composite |
| fracture | CT / 骨折 | 500 / 800 | composite |
| lumbar | CT / 腰椎 | 540 / 920 | composite |
| hardware | CT / 金属植入物 | 1850 / 2300 | composite |
| lung3 | CT / 肺 3（低密度） | -625 / 650 | composite |
| renals-stomach | CT / 肾脏与胃 | 160 / 480 | composite |
| vessel | CTA / 血管 | 400 / 700 | composite |
| carotid | CTA / 颈动脉 | 356.7605 / 456.2350 | composite |
| vessel-outline | CTA / 血管轮廓 | 400 / 600 | composite |
| mr-general | MR / MR 灰度体绘制 | 自动 MR 窗 | composite |
| mr-bright | MR / MR 高信号 | 自动 MR 窗 | composite |
| mr-mip | MR / MR MIP | 自动 MR 窗 | mip |

General 分组中的 AAA、Red、Cardiac、Muscle 也仅供 CT 使用。
MR 界面只显示其 3 个模板；其他非 CT 模态禁用 HU 模板。

## 来源与边界

- 原有骨骼、血管配色仍参考本机小赛看看 DICOM Viewer 2.6.2 的可读
  `VRBones.clut`、`VRRedVessels.clut`；骨骼、肺窗参考 `WLWW.xml`。
  颜色以索引 0、32、64、96、128、160、192、224、255 取样后线性插值。
- AAA、Cardiac、Muscle、Bones、Lung2 分别取自 3D Slicer 的 CT-AAA、CT-Cardiac、
  CT-Muscle、CT-Bone、CT-Lung；Carotid 使用其 CT-Coronary-Arteries-3 强度映射，
  用作血管显示配置，不代表颈动脉识别或分割。
  [固定版本参数来源](https://github.com/Slicer/Slicer/blob/74c135801f704ade9660d894a928d8b4b93d7a28/Modules/Loadable/VolumeRendering/Resources/presets.xml)，
  完整许可证保存在 `licenses/Slicer.txt`，现有打包流程会携带 licenses 目录。
- Red、Bone Plus Plate、Fracture、Lumbar、Hardware、Lung3、Renals–Stomach、
  Vessel Outline 是本项目编写的独立 HU 曲线；参考截图用于功能分类和视觉比较。
  原有透明度、血管默认窗等也是本项目配置。
- 没有取得小赛看看二进制 `vrConifg.xml` 的完整模板参数，故不声称逐像素复制参考软件。
  未复制其图标、缩略图或二进制资源。模板名字表示显示用途，实际可见组织取决于序列强度，
  例如无金属或高密度结构的序列可能在 Hardware 下接近全空。

## 投影与采样

Composite 使用逐采样点的颜色、透明度及模板光照。
MIP 使用真实最大强度混合，关闭光照；XRay 使用 Additive，并将线性透明度乘以
`min(1, 3 × step / diagonal)`，其中 step 是最小体素间距，diagonal 是体数据物理对角线。
XRay 是灰度射线累加显示，不是包含能谱和散射的 X 光物理模拟。

所有模板保持固定射线采样步长和图像采样距离，关闭交互采样自适应；
旋转、平移、缩放及调窗期间与松手后保持相同质量。
视口以 16 ms 定时器合并事件。调窗只更新传递函数和属性，相机变化复用它们；
不会重新读取 DICOM、重建体数据或替换原始像素数组。

## 验证

自动回归覆盖 HU 锚点、曲线同步变换（含窗外点）、透明空气、模态限制、CT 默认显示、
序列窗独立性、后台默认窗回退、模板/相机重置和全部模板的可滚动选择。
`tests/manual/smoke_3d.py` 使用含肺、软组织、骨骼、金属和床板的合成数据，
验证全部 20 个 CT 模板的实际 GPU 输出，以及交互质量、调窗、旋转、裁剪和 Tab 生命周期。

单个真实 CT 序列可本地检查：

```sh
PYTHONPATH=src python tests/manual/render_ct_presets.py DICOM_DIR build/validation/ct-presets
```

该脚本导出每个模板的体绘制 PNG 和不含患者标识的渲染统计；输出图包含影像内容，
保持在本地忽略的 build 目录。详见 [P113 验证记录](validation/volume-3d-20260915/README.md)。
