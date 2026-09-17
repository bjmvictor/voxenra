# 加载失败页签与 PNG 可用性复核

## 原因与修改

- Enhanced MR 的支持性判断原先在侧栏、工作区创建页签之前返回，导致双击没有反馈。现在先创建页签，再由原有加载器校验；失败显示原始原因，不放宽像素、帧几何或重建校验。
- 本地 `emri_small` 四个编码副本均有 10 帧，但缺少 Shared / Per-frame Functional Groups。现在双击可见错误页，提示 Enhanced MR 帧信息不完整或无效，仍可单独打开 Tag。
- `SC_rgb_jpeg` 两个副本属于彩色对象，主阅片尚不支持。删除“可以导出 PNG”的错误承诺，明确当前画面不能导出 PNG。
- 工作区错误页只保留“关闭页签”。2D 子视口、平铺、MPR 三维参考及独立三维原生错误页采用相同关闭操作；关闭的是所属页签，不影响其他窗口的活动页签。
- 无患者姓名的页签使用序列描述作为标题；两者均缺失时显示“未知患者”。
- 右侧 PNG 按钮随当前页签、加载状态及可见平铺切片状态更新。失败、加载中或平铺未全部就绪时禁用并说明原因；导出接口、异步截图开始和保存前均复核状态。
- 同步中英文提示、工作区恢复文案与操作手册，移除已不存在的影像重试入口说明。导入扫描、PACS 网络等可恢复操作的重试功能保留。

## PNG 范围

右侧是**当前画面截图**，必须存在可用画面。左侧是**源序列逐帧转换**，已有 RGB／调色板转换能力：部分主阅片不支持的彩色对象仍可转换，但不能据此保证所有失败影像都能导出。保留真实存在的独立转换能力；失败页不再笼统推荐 PNG。源 DICOM 复制也不依赖主阅片是否显示成功。

## 验证

- 相关加载、MR/CT、PNG、匿名导出、序列转换、语言和 QML 专项：136 项通过。
- 补充后续切片失败关闭、标题回退和多窗口／加载生命周期复核：38 项通过，2 项按环境跳过。
- 本机 macOS 原生窗口与文件选择器验证：20 个本地公开样本全部按预期处理（包括正常显示及明确拒绝的样本），不是宣称所有文件都可阅片。覆盖 Enhanced MR 双击创建错误页、原因显示、关闭、Tag 仍可读、PNG 不可用及正常图像窗值变化。
- 全量执行：1862 项通过、62 项跳过，另外 2 项仍断言旧版彩色错误文案。更新为检查“不能导出当前画面 PNG”及 Tag 提示后，整个编解码模块 24 项重跑通过；合计 1864 项用例通过验证，无未解决的用例失败。这不是一次全绿的单进程运行；完整日志保留原先两个断言失败。
- 原生目标样本最终复核：Enhanced MR RLE 与两个彩色样本共 3 项通过，确认无姓名标题回退、错误关闭和图像工具禁用。初次打开失败时整组图像工具不可用；后续切片失败及程序调用由 PNG 自身的状态检查保护。
- 中间一轮全量运行出现 Qt QObject 析构崩溃。关闭请求改为直接连接 QObject 槽，避免闭包保留页签；关闭／多窗口专项 34 项通过、1 项跳过，随后全量运行完成且未再出现崩溃。未据此推断 Qt 内部缺陷。
- 静态检查：Ruff E9/F63/F7/F82、Git whitespace。

原生截图和逐样本结果位于 Git 忽略的 `build/validation/failed-views-20260917/`；不提交源影像、患者关联标签或截图。

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software .venv/bin/python -m pytest tests -q
VOXENRA_COMPRESSED_SAMPLE_DIR="$HOME/Documents/test_dicom/Compressed_DICOM_Public_20260916" \
VOXENRA_SAMPLE_QA_OUTPUT=build/validation/failed-views-20260917 \
QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software \
  .venv/bin/python -m pytest tests/manual/test_public_compressed_samples.py -q
```
