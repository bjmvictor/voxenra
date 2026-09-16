<p align="center">
  <img src="src/qt_dicom_viewer/qml/assets/brand/voxenra-mark.svg" width="80" alt="Voxenra logo">
</p>

# Voxenra

面向 CT、MR 与 PET 的跨平台 DICOM 工作台：多窗口阅片、灵活布局、序列对比、斜面重建、3D / 4D、融合与测量。

[macOS · Apple Silicon](https://github.com/l5769389/voxenra/releases/download/v1.2.0/Voxenra-1.2.0-macos-arm64.dmg) · [Windows · 安装包](https://github.com/l5769389/voxenra/releases/download/v1.2.0/Voxenra-1.2.0-windows-x64-setup.exe) · [Windows · 便携版](https://github.com/l5769389/voxenra/releases/download/v1.2.0/Voxenra-1.2.0-windows-x64-portable.exe) · [更新记录](https://github.com/l5769389/voxenra/releases/tag/v1.2.0)

> v1.2.0 优化 2D 视图切换、侧边栏与加载响应，新增测量精度设置及统一鼠标操作；下方展示当前版本的主要功能。

## 影像与导入

| 类型 | 支持范围 |
| --- | --- |
| CT | 常规单帧灰度序列；2D、MPR、3D、平铺与对比；有效多时相组支持 4D。 |
| MR | 经典单帧、Enhanced MR 与 Legacy Converted Enhanced MR；灰度多帧按回波、扩散、时相和分量分组，支持阅片、对比及规则组重建。 |
| PET / PT | 经典单帧静态／全身 PET；2D、MPR、3D、PET/CT 融合，按元数据提供源单位或 SUVbw。 |
| 本地与 PACS | 文件、文件夹、ZIP / RAR / 7z / TAR 等压缩包混选或拖入；DICOMweb 查询与下载。 |

MPR / 3D 需要规则空间采样。暂不支持 NIfTI / NRRD、动态／门控 PET、MR 4D 播放及 fMRI / DTI 分析；归档解压与 DICOM 像素压缩解码是两回事；内置 RLE、JPEG、JPEG-LS 和 JPEG 2000 的固定解码组件，详见 [压缩 DICOM](docs/compressed-dicom.md)。完整格式与解码限制见 [影像支持](docs/image-support.md)。

视口默认左键拖动调窗、右键拖动缩放、滚轮翻页；当前工具及十字线等专用交互优先。融合配准保留右键旋转，3D 滚轮保持缩放。

体数据读取与 3D 数组准备在后台执行，加载中可切换页签或关闭视图。关闭会停止未完成的读取，首次 GPU 绘制仍可能短暂等待。

CT 3D 默认使用 **AAA**，提供 **20 个模板**；MR 保留专用模板。3D 调窗同时调整颜色和透明度，独立于二维切片窗。详见 [3D 模板与调窗](docs/volume-presets.md)。

## MPR 四宫格

三平面与 3D 同屏，显示切面边框和交点；支持位置联动及可选的旋转联动。选中 3D 后右侧切换为独立的 3D 工具，收起侧栏也可选择影像类型对应的模板、六方向和参考显示设置。双击 3D 宫格可最大化至视图区，再次双击恢复四宫格。3D 相机与显示设置独立保存，切换视图或 4D 时相不会重置。 布局面板可勾选「记住布局」，MPR 与 4D 分别记忆并自动更新；工作区恢复优先使用各标签页已保存的布局。

[![MPR 四宫格与原生 3D 切面参考](docs/screenshots/11-mpr-3d-layout.png)](docs/screenshots/11-mpr-3d-layout.png)

## 窗口、布局与对比

<table>
<tr>
<td width="50%" valign="top"><b>分离页签</b><br>拖出成为独立窗口，也可拖回合并。<br>
<a href="docs/screenshots/13-detached-tabs.png"><img src="docs/screenshots/13-detached-tabs.png" alt="分离页签：拖出成为独立窗口，也可拖回合并。" width="100%"></a></td>
<td width="50%" valign="top"><b>Oblique 斜面重建</b><br>旋转十字线和切面，观察任意斜面。<br>
<a href="docs/screenshots/14-oblique-mpr.png"><img src="docs/screenshots/14-oblique-mpr.png" alt="Oblique 斜面重建：旋转十字线和切面，观察任意斜面。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>2D 多视口</b><br>预设／自定义网格，拖入序列；各视口左上角切换 Stack 原始切片或 Axial／Coronal／Sagittal 标准切面。<br>
<a href="docs/screenshots/10-2d-layout.png"><img src="docs/screenshots/10-2d-layout.png" alt="2D 多视口：预设／自定义网格，拖入序列；各视口左上角切换 Stack 原始切片或 Axial／Coronal／Sagittal 标准切面。" width="100%"></a></td>
<td width="50%" valign="top"><b>双序列 MPR 对比</b><br>六宫格、对应切面放大与可控联动，测量各自独立。<br>
<a href="docs/screenshots/09-mpr-compare.png"><img src="docs/screenshots/09-mpr-compare.png" alt="双序列 MPR 对比：六宫格、对应切面放大与可控联动，测量各自独立。" width="100%"></a></td>
</tr>
</table>

## 4D 多时相 · 动画

2D／MPR 的 **播放** 循环浏览当前视图的切片。4D 提供两个入口：**当前时相播放** 仅循环当前时相的切片，**4D 播放** 保持同一定位循环切换 CT 时相；两种播放互斥，运行时另一种播放按钮禁用，停止后才能切换；手动切换时相会停止切片播放。展开和收起的操作栏都可播放／停止，支持 1–15 FPS，停止保留当前位置。切换视图或标签页会停止播放。支持通过空间几何校验的 `Gated, 0.0%A` 等呼吸时相描述，需导入全部时相序列。 四宫格的 3D 随时相变化，播放等待当前 3D 帧完成再推进；选中 3D 后也保留播放／停止入口。4D 支持阈值分割与 VOI，范围和统计按时相独立保存，切换回来可继续编辑；清除仅影响当前时相，不自动跨时相传播或追踪。以下展示 10 个呼吸时相；[查看高清静态图](docs/screenshots/03-4d-mpr.png)。

![4D CT 十时相循环：三个切面的影像与相位同步变化](docs/screenshots/03-4d-playback.gif)

## 阅片与测量

测量结果默认显示 2 位小数；可在“设置 → 测量与标注 → 测量精度”选择整数或 1–3 位小数，应用于测量、ROI/VOI、分析结果及 CSV/PDF 测量报告。底层计算及工作区中的测量值保留原精度，详见 [显示设置](docs/display-settings.md)。

<table>
<tr>
<td width="50%" valign="top"><b>MR 阅片</b><br>自动窗、反白与 MR 采集参数；按原始强度测量。<br>
<a href="docs/screenshots/07-mr-reading.png"><img src="docs/screenshots/07-mr-reading.png" alt="MR 阅片：自动窗、反白与 MR 采集参数；按原始强度测量。" width="100%"></a></td>
<td width="50%" valign="top"><b>2–4 序列 2D 对比</b><br>对应位置或相对进度同步；图示 Enhanced MR 分组。<br>
<a href="docs/screenshots/08-enhanced-mr-compare.png"><img src="docs/screenshots/08-enhanced-mr-compare.png" alt="2–4 序列 2D 对比：对应位置或相对进度同步；图示 Enhanced MR 分组。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>测量与标注</b><br>长度、角度、ROI 统计，支持复制粘贴和撤销重做。<br>
<a href="docs/screenshots/01-2d-measurement.png"><img src="docs/screenshots/01-2d-measurement.png" alt="测量与标注：长度、角度、ROI 统计，支持复制粘贴和撤销重做。" width="100%"></a></td>
<td width="50%" valign="top"><b>序列平铺与伪彩</b><br>快速浏览整组切片，双击进入对应层的 2D 视图。<br>
<a href="docs/screenshots/12-mr-montage.png"><img src="docs/screenshots/12-mr-montage.png" alt="序列平铺与伪彩：快速浏览整组切片，双击进入对应层的 2D 视图。" width="100%"></a></td>
</tr>
</table>

## 三维、融合与分割

<table>
<tr>
<td width="50%" valign="top"><b>3D 体绘制</b><br>CT / MR / PET 专用显示控制，支持旋转与裁剪。<br>
<a href="docs/screenshots/04-volume-rendering.png"><img src="docs/screenshots/04-volume-rendering.png" alt="3D 体绘制：CT / MR / PET 专用显示控制，支持旋转与裁剪。" width="100%"></a></td>
<td width="50%" valign="top"><b>3D 圈选裁剪</b><br>保留或移除选区，裁剪后仍可旋转观察与重置。<br>
<a href="docs/screenshots/29-volume-crop.png"><img src="docs/screenshots/29-volume-crop.png" alt="3D 圈选裁剪：保留或移除选区，裁剪后仍可旋转观察与重置。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>PET/CT 融合</b><br>CT、PET、融合和 MIP 联动，支持手动刚性配准。<br>
<a href="docs/screenshots/05-pet-ct-fusion.png"><img src="docs/screenshots/05-pet-ct-fusion.png" alt="PET/CT 融合：CT、PET、融合和 MIP 联动，支持手动刚性配准。" width="100%"></a></td>
<td width="50%" valign="top"><b>融合 3D</b><br>叠加 CT 与 PET，可独立调整色表和不透明度。<br>
<a href="docs/screenshots/06-fusion-3d.png"><img src="docs/screenshots/06-fusion-3d.png" alt="融合 3D：叠加 CT 与 PET，可独立调整色表和不透明度。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>MPR 厚层投影</b><br>MIP、MinIP、Mean、Sum，可分别设置三向厚度。<br>
<a href="docs/screenshots/27-thick-slab.png"><img src="docs/screenshots/27-thick-slab.png" alt="MPR 厚层投影：MIP、MinIP、Mean、Sum，可分别设置三向厚度。" width="100%"></a></td>
<td width="50%" valign="top"><b>MPR 阈值分割</b><br>在限定范围内分割，查看体积及强度统计。<br>
<a href="docs/screenshots/02-mpr-segmentation.png"><img src="docs/screenshots/02-mpr-segmentation.png" alt="MPR 阈值分割：在限定范围内分割，查看体积及强度统计。" width="100%"></a></td>
</tr>
</table>

## 分析与标签

<table>
<tr>
<td width="50%" valign="top"><b>VOI 分析</b><br>球体／椭球范围与阈值分析，显示三向截面。<br>
<a href="docs/screenshots/20-voi.png"><img src="docs/screenshots/20-voi.png" alt="VOI 分析：球体／椭球范围与阈值分析，显示三向截面。" width="100%"></a></td>
<td width="50%" valign="top"><b>CT 水模 QA</b><br>中心与周边 ROI，查看 CT 值、噪声和均匀性。<br>
<a href="docs/screenshots/19-water-qa.png"><img src="docs/screenshots/19-water-qa.png" alt="CT 水模 QA：中心与周边 ROI，查看 CT 值、噪声和均匀性。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>点源 MTF / FWHM</b><br>框选微珠或细丝截面，查看 X / Y 曲线及分辨率指标。<br>
<a href="docs/screenshots/28-mtf-analysis.png"><img src="docs/screenshots/28-mtf-analysis.png" alt="点源 MTF / FWHM：框选微珠或细丝截面，查看 X / Y 曲线及分辨率指标。" width="100%"></a></td>
<td width="50%" valign="top"><b>DICOM 标签</b><br>逐实例浏览、搜索与查看完整标签值。<br>
<a href="docs/screenshots/21-dicom-tags.png"><img src="docs/screenshots/21-dicom-tags.png" alt="DICOM 标签：逐实例浏览、搜索与查看完整标签值。" width="100%"></a></td>
</tr>
</table>

## 导入、保存与导出

<table>
<tr>
<td width="50%" valign="top"><b>统一导入</b><br>同一个窗口混选文件夹、DICOM 文件与压缩包。<br>
<a href="docs/screenshots/15-mixed-import.png"><img src="docs/screenshots/15-mixed-import.png" alt="统一导入：同一个窗口混选文件夹、DICOM 文件与压缩包。" width="100%"></a></td>
<td width="50%" valign="top"><b>PACS 浏览器</b><br>查询检查、选择序列并下载到本地阅片。<br>
<a href="docs/screenshots/16-pacs-browser.png"><img src="docs/screenshots/16-pacs-browser.png" alt="PACS 浏览器：查询检查、选择序列并下载到本地阅片。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>PACS 导入完成</b><br>下载的序列自动加入左侧列表，并打开 2D 阅片。<br>
<a href="docs/screenshots/23-pacs-import.png"><img src="docs/screenshots/23-pacs-import.png" alt="PACS 导入完成：下载的序列自动加入左侧列表，并打开 2D 阅片。" width="100%"></a></td>
<td width="50%" valign="top"><b>工作区保存与恢复</b><br>保存影像引用与操作状态，支持自动恢复副本。<br>
<a href="docs/screenshots/17-workspace.png"><img src="docs/screenshots/17-workspace.png" alt="工作区保存与恢复：保存影像引用与操作状态，支持自动恢复副本。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>影像与测量导出</b><br>PNG、源 DICOM、测量 CSV / PDF；匿名默认开启。<br>
<a href="docs/screenshots/18-export.png"><img src="docs/screenshots/18-export.png" alt="影像与测量导出：PNG、源 DICOM、测量 CSV / PDF；匿名默认开启。" width="100%"></a></td>
<td width="50%" valign="top"><b>中英文离线手册</b><br>工具直达说明，支持章节搜索、操作示例与快捷键。<br>
<a href="docs/screenshots/30-offline-manual.png"><img src="docs/screenshots/30-offline-manual.png" alt="中英文离线手册：工具直达说明，支持章节搜索、操作示例与快捷键。" width="100%"></a></td>
</tr>
</table>

## 主题与紧凑界面

<table>
<tr>
<td width="50%" valign="top"><b>深色主题</b><br>深色工作台，保持影像区域与工具清晰分离。<br>
<a href="docs/screenshots/25-theme-dark.png"><img src="docs/screenshots/25-theme-dark.png" alt="深色主题：深色工作台，保持影像区域与工具清晰分离。" width="100%"></a></td>
<td width="50%" valign="top"><b>浅色主题</b><br>即时切换浅色界面，影像内容保持黑色背景。<br>
<a href="docs/screenshots/26-theme-light.png"><img src="docs/screenshots/26-theme-light.png" alt="浅色主题：即时切换浅色界面，影像内容保持黑色背景。" width="100%"></a></td>
</tr>
<tr>
<td width="50%" valign="top"><b>紧凑侧边栏</b><br>左右栏可独立收起；左侧保留导出、清除等入口，右侧支持测量、旋转、标注和伪彩的二级图标。<br>
<a href="docs/screenshots/24-compact-sidebars.png"><img src="docs/screenshots/24-compact-sidebars.png" alt="紧凑侧边栏：左右栏可独立收起；左侧保留导出、清除等入口，右侧支持测量、旋转、标注和伪彩的二级图标。" width="100%"></a></td>
<td width="50%" valign="top"><b>显示设置</b><br>自选四角字段与样式，另支持深浅主题和中英文。<br>
<a href="docs/screenshots/22-display-settings.png"><img src="docs/screenshots/22-display-settings.png" alt="显示设置：自选四角字段与样式，另支持深浅主题和中英文。" width="100%"></a></td>
</tr>
</table>

所有截图来自实际应用，点击可查看原图；[数据来源与截图复现](docs/screenshots/README.md)。更详细的操作说明在应用内离线手册中。

## 文档与运行

[影像支持](docs/image-support.md) · [本地导入](docs/local-import.md) · [PACS](docs/pacs.md) · [MR](docs/mr.md) · [PET 与融合](docs/pet-mpr-fusion.md) · [分割与 VOI](docs/mpr-segmentation-voi.md) · [工作区](docs/workspaces.md) · [导出](docs/export.md) · [操作手册](docs/manual.md)

```bash
uv run voxenra
```

[开发与打包](docs/packaging.md) · 测试：`uv run --group dev pytest -q`
