# 外观与语言

设置 → 外观与语言可即时切换浅色／深色和简体中文、English、Português (Brasil)，也可选择用户添加的语言。初次安装与旧配置保持深色、简体中文。偏好保存到现有设置的 `appearance.theme`、`appearance.language`，不修改影像、测量、撤销记录或工作区状态。

## 编辑或添加语言

1. 点击“打开语言包目录”，应用会打开本地的 `languages` 目录；目录不存在时自动创建。软件内不需要填写语言名称或代码。
2. 将符合下述格式的 UTF-8 JSON 语言包放入目录。文件名须与包内 `locale` 一致，例如 `fr-FR.json`。已有文件不会由软件覆盖。
3. 重启软件，新语言会自动出现在设置的下拉列表中，选择后立即生效。选中的语言在下次启动时保持。编辑现有包后也可点击“重新加载语言包”，无需重启。

翻译 `messages` 时保持文案 ID 和占位符名称、格式不变，例如 `{value1}`、`{count}`；不要将参数翻译成其他名字。手册也在语言包中，`**重点**` 与反引号保留重点和快捷键样式。

```json
{
  "formatVersion": 1,
  "locale": "fr-FR",
  "name": "Français",
  "messages": {
    "text.0539": "Annuler",
    "sidebar.selected": "{count} séries sélectionnées"
  }
}
```

同语言外部包优先于内置包。省略的条目回退到内置同语言；新语言回退英文。无效 JSON、语言标识或占位符会在设置中报告，保留最后有效内容。修正后重新加载；也可移走有问题的外部文件，重新加载以恢复内置包。完整的中英文及巴西葡萄牙语模板随软件提供。

数据目录通常为：

- macOS：`~/Library/Application Support/Voxenra/Voxenra/languages`
- Windows：`%LOCALAPPDATA%\Voxenra\Voxenra\languages`

以软件“打开语言包目录”实际打开的位置为准。患者姓名、路径、用户命名和自由标注不会被翻译。应用拥有的提示与按钮跟随所选语言；系统文件选择窗口的系统侧栏跟随操作系统语言。

CSV 的可读列名、测量类型和 PDF 正文随导出开始时的语言固定，导出期间切换语言不会混用。数据、列顺序、单位及匿名规则保持一致。PDF 保持适合打印的浅色页面。

开发校验：`tests/test_appearance_language.py` 检查内置包完整性、参数、覆盖、回退、持久化和实时界面切换。`tests/manual/capture_manual.py OUTPUT --english` 使用合成 CT/PET 和真实 Qt/VTK 窗口生成英文手册截图。
