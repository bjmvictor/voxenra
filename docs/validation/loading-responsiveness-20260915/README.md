# 视图加载响应验证 — 2026-09-15

在 `codex/sidebar-style-polish` worktree 完成。此次针对偶发加载卡顿，覆盖后台准备、关闭旧任务、原生 3D 和完整主窗口的页签切换。

## 修复内容

- 原生窗口收到每次 `Expose` 都请求绘制；macOS 上换帧又触发 `Expose`，可形成持续空闲重绘。现在仅在重新暴露时请求初次绘制，真实状态变化、尺寸变化和交互仍正常触发重绘。
- 体数据有限值检查、连续数组转换及 MR padding 掩膜准备移到后台。Qt/VTK 对象及 OpenGL 操作留在窗口线程；完成后只安装当前视图仍需要的数据，忽略关闭或替换后的过期结果。
- 原生窗口创建推迟到下一次页面事件。验证中进一步发现 `Qt.callLater` 回调可能在 QML Loader 销毁页面后执行，现改为页面拥有的单次定时器，销毁时一并取消。
- 关闭页签时清除等待请求并取消进行中的读取；读取中的单个切片处理结束后检查取消状态，尚未开始的任务直接跳过。过期成功和失败结果都不会回写当前界面。
- 体数据缓存按最近访问顺序淘汰，预算为 1 GiB。允许保留一份超过预算的体数据，避免 MPR 三个切面反复解码同一大序列。活动视图持有的数据不受缓存淘汰影响，因此这不是整个程序的内存上限。
- 导出在后台数组准备完成后才允许执行，避免首次画面尚未准备好时导出空图。

原始像素、体数据分辨率、患者坐标、采样距离与测量计算均未降级。MR MONOCHROME1/2 padding 掩膜、CT/PET 融合各自的填充值保持既有含义。

## 自动回归

结果摘要见 [checks.json](checks.json)。

- 核心加载、CT/MR/Enhanced MR、体绘制、裁剪、PET、鼠标及请求队列：257 通过，1 个原生用例跳过。
- 手册、语言和完整 QML 页面加载切换：56 通过。过程中发现的已销毁页面延迟回调错误已修复并重跑通过。
- Cocoa 原生桌面：3 通过，覆盖真实主窗口加载中切换手册并快速往返、CT/PT MPR 四宫格交互、布局切换、导出和关闭。
- 专门检查了准备阶段 GUI 定时器继续响应、关闭后重新打开、取消排队请求、旧结果晚到，以及缓存淘汰后活动数据仍可用。

核心检查中仍有 VTK 的 NumPy 数组 shape API 弃用提示；无测试失败。原生基准没有 QML 警告或渲染错误。

## 具体影像与原生窗口验证

每组连续三轮：打开 3D → 等待首帧 → 稳定后观察 300 ms 空闲绘制次数 → 切到手册 → 返回 → 导出 → 关闭；开始前另做一次结果尚未返回时关闭。测量使用 10 ms GUI 定时器观察事件间隔。

| 数据 | 体数据尺寸（切片 × 行 × 列） | 三轮首帧就绪时间 | 最大 GUI 事件间隔 | 稳定后的空闲重绘 |
| --- | --- | --- | --- | --- |
| 大 CT，合成体数据已放入正常缓存 | 457 × 512 × 512 | 357 / 325 / 324 ms | 267 / 242 / 249 ms | 均为 0 |
| 文稿中的 Thin-3D-T1 MR | 192 × 256 × 256 | 358 / 221 / 188 ms | 156 / 155 / 148 ms | 均为 0 |
| 文稿中的螺旋 mtf CT | 20 × 1024 × 1024 | 285 / 217 / 212 ms | 165 / 185 / 182 ms | 均为 0 |

原始指标：[大 CT](native-large-ct.json)、[真实 MR](native-real-mr.json)、[真实 CT](native-real-ct.json)。所有打开、切换返回、导出、关闭步骤通过，无持续卡死。记录只含尺寸与性能指标，不含患者标识或影像截图。

目录扫描与 VTK 模块导入在计时前完成；真实数据首轮包含实际解码，后续轮次可复用缓存；合成大 CT 不包含解码。这些数值用于定位当前机器上的阻塞阶段，不是所有设备的性能保证。

## 仍然存在的边界

首帧 GPU 初始化、纹理上传与绘制仍在窗口线程执行；本轮最大 GUI 间隔约 0.15–0.27 秒，较早的原生运行曾测到约 0.42 秒。因此首次 3D 仍可能短暂停顿，不能承诺任意数据和显卡上完全无等待。后台取消也不会强行中断第三方解码器正在处理的单个文件。此前偶发问题未必全部来自同一原因，本次已修复可确认的重绘循环、页面回调时序及后台准备阻塞。

## 复现

使用项目虚拟环境；macOS 设置 `QT_QPA_PLATFORM=cocoa`，Windows 使用 `windows`。原生探针必须在桌面会话运行。

```sh
PYTHONPATH=src:tests:tests/manual QT_QPA_PLATFORM=cocoa python tests/manual/benchmark_volume_loading.py /tmp/volume-loading.json
PYTHONPATH=src:tests:tests/manual QT_QPA_PLATFORM=cocoa python tests/manual/benchmark_volume_loading.py /tmp/mr-loading.json /path/to/Thin-3D-T1
PYTHONPATH=src:tests:tests/manual QT_QPA_PLATFORM=cocoa VOXENRA_NATIVE_QA=1 python -m pytest tests/test_loading_responsiveness.py tests/test_mpr_layout.py -k 'native_main_window or native_four_up'
```
