<p align="center">
  <img src="src/qt_dicom_viewer/qml/assets/brand/voxenra-mark.svg" width="80" alt="Voxenra logo">
</p>

# Voxenra

面向 CT、MR 与 PET 的跨平台 DICOM 工作台：多窗口阅片、灵活布局、序列对比、斜面重建、3D / 4D、融合与测量。

[macOS · Apple Silicon](https://github.com/l5769389/voxenra/releases/download/v1.1.0/Voxenra-1.1.0-macos-arm64.dmg) · [Windows · 安装包](https://github.com/l5769389/voxenra/releases/download/v1.1.0/Voxenra-1.1.0-windows-x64-setup.exe) · [Windows · 便携版](https://github.com/l5769389/voxenra/releases/download/v1.1.0/Voxenra-1.1.0-windows-x64-portable.exe) · [更新记录](https://github.com/l5769389/voxenra/releases/tag/v1.1.0)

> v1.1.0 新增 MR / Enhanced MR、灵活布局与序列对比；下方展示当前版本的主要功能。

## 影像与导入

| 类型 | 支持范围 |
| --- | --- |
| CT | 常规单帧灰度序列；2D、MPR、3D、平铺与对比；有效多时相组支持 4D。 |
| MR | 经典单帧、Enhanced MR 与 Legacy Converted Enhanced MR；灰度多帧按回波、扩散、时相和分量分组，支持阅片、对比及规则组重建。 |
| PET / PT | 经典单帧静态／全身 PET；2D、MPR、3D、PET/CT 融合，按元数据提供源单位或 SUVbw。 |
| 本地与 PACS | 文件、文件夹、ZIP / RAR / 7z / TAR 等压缩包混选或拖入；DICOMweb 查询与下载。 |

MPR / 3D 需要规则空间采样。暂不支持 NIfTI / NRRD、动态／门控 PET、MR 4D 播放及 fMRI / DTI 分析；归档解压与 DICOM 像素压缩解码是两回事。完整格式与解码限制见 [影像支持](docs/image-support.md)。

## MPR 四宫格

三平面与 3D 同屏，显示切面边框和交点；支持位置联动及可选的旋转联动。

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
<td width="50%" valign="top"><b>2D 多视口</b><br>预设／自定义网格，拖入序列，各格独立切换方向。<br>
<a href="docs/screenshots/10-2d-layout.png"><img src="docs/screenshots/10-2d-layout.png" alt="2D 多视口：预设／自定义网格，拖入序列，各格独立切换方向。" width="100%"></a></td>
<td width="50%" valign="top"><b>双序列 MPR 对比</b><br>六宫格、对应切面放大与可控联动，测量各自独立。<br>
<a href="docs/screenshots/09-mpr-compare.png"><img src="docs/screenshots/09-mpr-compare.png" alt="双序列 MPR 对比：六宫格、对应切面放大与可控联动，测量各自独立。" width="100%"></a></td>
</tr>
</table>

## 4D 多时相 · 动画

保持同一定位浏览不同 CT 时相，支持相位选择与循环播放。以下展示 10 个呼吸时相；[查看高清静态图](docs/screenshots/03-4d-mpr.png)。

![4D CT 十时相循环：三个切面的影像与相位同步变化](docs/screenshots/03-4d-playback.gif)

## 阅片与测量

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
<td width="50%" valign="top"><b>紧凑侧边栏</b><br>左右栏可独立收起，保留缩略图与直接操作工具。<br>
<a href="docs/screenshots/24-compact-sidebars.png"><img src="docs/screenshots/24-compact-sidebars.png" alt="紧凑侧边栏：左右栏可独立收起，保留缩略图与直接操作工具。" width="100%"></a></td>
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
