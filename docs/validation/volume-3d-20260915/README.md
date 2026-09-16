# P113 3D 显示与模板验证

日期：2026-09-15。基于 main `8f742225d16a8ead2281f8f1a11465496b1dda15`，
分支 `codex/3d-optimization`。

## 后续实机对照

本报告验证功能链路与基本输出；后续在本地小赛看看实际对照发现 AAA 偏白、采样条纹和
调窗响应差异。当前视觉验收结论以 [实机对照记录](../xiaosai-3d-comparison-20260915/README.md)为准。

## 问题原因

本地使用 `Documents/test_dicom/P113_dicom/MP1/ph0`，与参考图的 MP1_ph0 对应。
99 张 CT 切片构成 99 × 512 × 512 的体数据，体素间距约 0.9766 × 0.9766 × 3 mm。
所有相位的元数据检查发现未设置 WindowCenter / WindowWidth，RescaleSlope 为 1、
RescaleIntercept 为 0。MP1/ph0 模态值范围为 −1000～2976 HU，99 分位为 225 HU，
存在 238,638 个 >240 HU 体素和 15,896 个 >1000 HU 体素；数据正常包含高密度结构。

原默认 3D 采用通用灰度映射和 `0.08 × t²` 低透明度曲线，窗口继承二维默认值。
缺少 DICOM 窗信息时回退至 WL 40 / WW 400；此软组织窗配合灰度低透明度体绘制，
显示为发灰、半透明的投影。实际渲染复现了用户截图，因此原因是默认显示配置，
不是体数据全零、没有加载、Rescale 失败或 GPU 完全未输出。

改为默认 AAA 后，采用独立 3D 窗 WL 281.646 / WW 276.18，
以 HU 控制颜色、透明度及表面光照，显示出与参考图接近的暖色骨骼结构。
原始体素、二维窗和相机几何保持独立。

## 调窗检查

原先上下拖动平移、左右拖动拉伸颜色与透明度曲线的数学含义正确，
与 [3D Slicer 公开说明](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html)一致。
保留此行为，并验证颜色与透明度在窗内和窗外锚点上同步变化；不会把体素转换成二维窗后的灰度再做 3D。

修正后端未传 window 时错误使用序列窗的问题，现优先取当前模板默认窗。
界面移除 3D 面板中的二维切片窗列表及保存二维窗模板入口，加入 3D 调窗说明。
当前模板调窗重置、切换/再次选择模板、模板重置、全部重置均通过控制器及真实界面检查。

## 模板覆盖与来源

CT 可用模板由 6 个增加到 20 个，新增 14 个：AAA、Red、Cardiac、Muscle、Carotid、
Bone Plus Plate、Fracture、Lumbar、Hardware、Lung2、Lung3、Renals–Stomach、Vessel Outline、Bones。
MR 保留 3 个专用模板。完整参数、来源及许可证见 [模板说明](../../volume-presets.md)。

参考截图用于类别和效果比较；新增曲线由 3D Slicer 的公开配置与本项目独立配置组成，
不声称复制小赛看看未公开的二进制模板。器官名字不代表分割结果。

## 验证结果

- 定向 pytest：152 passed，覆盖体绘制状态、数据、编辑、全部模板 QML 选择、MR、窗面板、语言。
- 共享交互与工作区 pytest：185 passed、4 skipped，覆盖 MPR、PET、显示控件、加载、工作区及鼠标绑定。
  跳过项按现有测试的平台/桌面环境条件执行；另行完成下述原生桌面验收。
- 原生 Qt/QML/VTK smoke：20 个 CT 模板均有非空且不同的 GPU 输出；六方向、调窗重置、
  旋转、缩放、平移、裁剪、去床板、尺寸变化、2D/3D 切换、独立 Tab 和关闭重开全部通过。
  合成数据包含高密度金属，以实际验证 Hardware。
- 交互/静止帧像素差为 0；本机该次合成数据渲染记录为交互 12.1 ms、静止 3.7 ms。
  这是单次环境记录，不作为稳定性能基准。
- P113 MP1/ph0：以相同正面相机逐一渲染 20 个模板，全部成功生成 PNG；
  通用模板中央区域平均 RGB 为 94.95，AAA 为 148.80；对应颜色通道差均值为 1.31 / 32.38。
  统计仅用于确认画面和彩色输出，区域按每个模板可见像素分别统计，不代表临床图像质量评分。
- 原始体素与 VTK 输入保持复用；模板切换和相机交互不重新解码 DICOM。

本机影像产物位于 worktree 的忽略目录：

- `build/validation/volume-3d/comparison.png`：原通用显示与 AAA 对比。
- `build/validation/volume-3d/all-presets.png`：20 模板缩略图总览。
- `build/validation/volume-3d/p113/`：各模板完整 PNG 与 metrics.json。

影像产物未加入版本控制。报告未包含患者姓名、ID 或 UID。

## 复验命令

在该 worktree 下使用已有 Python 环境，或 `uv run --group dev`：

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m pytest -q \
  tests/test_volume_display.py tests/test_volume_view.py tests/test_volume_edit.py \
  tests/test_volume_panel_qml.py tests/test_enhanced_mr.py tests/test_display_completion.py \
  tests/test_linked_ct_window.py tests/test_appearance_language.py

QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m pytest -q \
  tests/test_mpr_layout.py tests/test_mr_qml.py tests/test_pet_volume.py \
  tests/test_standalone_pet_volume.py tests/test_display_settings_qml.py \
  tests/test_display_tools_qml.py tests/test_live_windowing_qml.py tests/test_mpr_voi_qml.py \
  tests/test_loading_responsiveness.py tests/test_workspace_persistence.py \
  tests/test_tool_controller.py tests/test_mouse_bindings.py tests/test_mip_qml.py

# 需原生桌面和 OpenGL；不设置 QT_QPA_PLATFORM=offscreen
PYTHONPATH=src python tests/manual/smoke_3d.py /tmp/volume.png
PYTHONPATH=src python tests/manual/render_ct_presets.py \
  /Users/jun/Documents/test_dicom/P113_dicom/MP1/ph0 build/validation/volume-3d/p113
```
