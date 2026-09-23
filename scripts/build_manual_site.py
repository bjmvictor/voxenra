"""Build the GitHub Pages manual from the desktop app's chapter and locale JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/qt_dicom_viewer/qml/assets"
HELP = ASSETS / "help"
SITE = ROOT / "docs/manual-site"
LANGUAGES = {
    "zh": {"pack": "zh-CN", "name": "简体中文", "search": "搜索章节与正文", "menu": "目录", "site": "操作手册", "home": "手册首页", "related": "相关章节", "shortcuts": "快捷键", "figure": "示意图", "examples": ("CT 示例", "PET 示例"), "repo": "GitHub 仓库"},
    "en": {"pack": "en-US", "name": "English", "search": "Search chapters and content", "menu": "Contents", "site": "Manual", "home": "Manual home", "related": "Related chapters", "shortcuts": "Shortcuts", "figure": "Diagram", "examples": ("CT example", "PET example"), "repo": "GitHub repository"},
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def rich(value: str) -> str:
    """Match the desktop manual's limited emphasis syntax; never trust HTML."""
    parts = re.split(r"(\*\*[^\n*]+\*\*|`[^\n`]+`)", value)
    return "".join(
        "<strong>" + escape(part[2:-2]) + "</strong>" if part.startswith("**") and part.endswith("**")
        else "<strong>" + escape(part[1:-1]) + "</strong>" if part.startswith("`") and part.endswith("`")
        else escape(part).replace("\n", "<br>")
        for part in parts
    )


def icon(name: str, css_class: str = "") -> str:
    return f'<img class="{css_class}" src="../assets/icons/{escape(name)}.svg" alt="" aria-hidden="true">'


def figure(kind: str, messages: dict[str, str], language: dict[str, str]) -> str:
    """Portable diagram for the two QML canvas illustrations."""
    if kind == "segmentation":
        labels = [messages[f"text.{n}"] for n in ("0928", "0929", "0930", "0931", "0932", "0933", "0934")]
        drawing = '<path d="M80 86h180v100H80zM130 40h180v100H130zM80 86l50-46m130 46 50-46m-50 146 50-46" fill="none" stroke="#ef77e3" stroke-width="2"/>'
        coordinates = [(130, 208), (10, 135), (270, 30), (400, 67), (400, 102), (400, 137), (400, 172)]
    elif kind == "voi":
        labels = [messages[f"text.{n}"] for n in ("0935", "0936", "0937", "0938", "0939")]
        drawing = '<circle cx="130" cy="110" r="65" fill="none" stroke="#ef77e3" stroke-width="2"/><path d="M130 110h65" stroke="#61d7eb" stroke-width="2"/><ellipse cx="385" cy="110" rx="70" ry="40" fill="none" stroke="#61d7eb" stroke-width="2"/><circle cx="625" cy="95" r="62" fill="none" stroke="#ef77e3" stroke-width="2"/><circle cx="625" cy="95" r="32" fill="none" stroke="#61d7eb" stroke-width="2"/>'
        coordinates = [(75, 25), (140, 102), (50, 203), (310, 203), (520, 203)]
    else:
        raise ValueError(f"Unknown manual diagram: {kind}")
    text = "".join(f'<text x="{x}" y="{y}">{escape(label)}</text>' for label, (x, y) in zip(labels, coordinates))
    return f'<div class="figure" role="img" aria-label="{escape(language["figure"])}"><svg viewBox="0 0 760 220" xmlns="http://www.w3.org/2000/svg">{drawing}<g fill="#d8e4ed" font-size="13" font-family="system-ui,sans-serif">{text}</g></svg></div>'


def render_chapter(chapter: dict, messages: dict[str, str], language: dict[str, str], titles: dict[str, str], aliases: dict) -> str:
    chapter_id = chapter["id"]
    prefix = f"manual.{chapter_id}."
    title = messages[prefix + "title"]
    summary = messages[prefix + "summary"]
    category_title = messages["manual.category." + chapter["category"]]
    breadcrumb_middle = (f'<span aria-hidden="true">/</span><span>{escape(category_title)}</span>'
                         if category_title != title else "")
    content = [f'<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="index.html">{escape(language["home"])}</a>{breadcrumb_middle}<span aria-hidden="true">/</span><span>{escape(title)}</span></nav>',
               f'<h1>{escape(title)}</h1>',
               f'<p class="summary">{escape(summary)}</p>']
    if chapter.get("shortcuts"):
        chips = []
        for index, item in enumerate(chapter["shortcuts"]):
            label = messages[item.get("messageId", prefix + f"shortcut{index}")]
            chips.append(f'<span class="shortcut"><span>{escape(label)}</span><kbd>{escape(item["keys"])}</kbd><kbd>{escape(item["mac"])}</kbd></span>')
        content.append(f'<div class="shortcuts" aria-label="{escape(language["shortcuts"])}">{"".join(chips)}</div>')
    images = [chapter["example"]] if "example" in chapter else chapter.get("examples", [])
    if images:
        cards = []
        for index, image in enumerate(images):
            # The English screenshots are maintained separately in the same help bundle.
            folder = "en/" if language["pack"] == "en-US" else ""
            label = language["examples"][index] if len(images) > 1 else messages.get(prefix + "caption", title)
            cards.append(f'<figure><a href="../assets/help/{folder}{escape(image)}" target="_blank" rel="noopener"><img src="../assets/help/{folder}{escape(image)}" alt="{escape(label)}" loading="lazy"></a><figcaption>{escape(label)}</figcaption></figure>')
        content.append(f'<div class="examples">{"".join(cards)}</div>')
    if chapter.get("figure"):
        content.append(figure(chapter["figure"], messages, language))
    for index, section in enumerate(chapter["sections"]):
        key = section.get("messageId", prefix + f"section{index}")
        css = "step important" if section.get("important") else "step"
        content.append(f'<section class="{css}" id="step-{index + 1}"><h2>{escape(messages[key + ".title"])}</h2><p>{rich(messages[key + ".body"])}</p></section>')
    if chapter.get("related"):
        links = []
        for related in chapter["related"]:
            alias = aliases.get(related)
            target = (f'{alias["chapter"]}.html#step-{alias["section"] + 1}' if alias
                      else f"{related}.html")
            label = messages.get(f"manual.{related}.title", titles.get(related, related))
            links.append(f'<a href="{escape(target)}">{escape(label)} <span aria-hidden="true">↗</span></a>')
        content.append(f'<nav class="related" aria-label="{escape(language["related"])}"><h2>{escape(language["related"])}</h2><div>{"".join(links)}</div></nav>')
    return "\n".join(content)


def render_page(chapter: dict, categories: list[dict], chapters: list[dict], messages: dict[str, str], code: str, aliases: dict) -> str:
    language = LANGUAGES[code]
    titles = {item["id"]: messages[f'manual.{item["id"]}.title'] for item in chapters}
    groups = []
    for category in categories:
        links = []
        for item in chapters:
            if item["category"] != category["id"]:
                continue
            selected = ' aria-current="page" class="selected"' if item["id"] == chapter["id"] else ""
            searchable = " ".join([titles[item["id"]], messages[f'manual.{item["id"]}.summary']] +
                                  [messages[section.get("messageId", f'manual.{item["id"]}.section{i}') + ".body"] for i, section in enumerate(item["sections"])])
            links.append(f'<a href="{escape(item["id"])}.html"{selected} data-search="{escape(searchable.lower())}">{escape(titles[item["id"]])}</a>')
        groups.append(f'<section class="nav-group"><h2>{escape(messages["manual.category." + category["id"]])}</h2>{"".join(links)}</section>')
    title = titles[chapter["id"]]
    other = "en" if code == "zh" else "zh"
    nav = "\n".join(groups)
    article = render_chapter(chapter, messages, language, titles, aliases)
    outline_links = []
    for index, section in enumerate(chapter["sections"]):
        key = section.get("messageId", f'manual.{chapter["id"]}.section{index}')
        outline_links.append(f'<a href="#step-{index + 1}">{escape(messages[key + ".title"])}</a>')
    outline = "".join(outline_links)
    return f'''<!doctype html>
<html lang="{language["pack"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(messages[f'manual.{chapter["id"]}.summary'])}">
<title>{escape(title)} · Voxenra {escape(language["site"])}</title>
<link rel="icon" href="../assets/voxenra-mark.svg" type="image/svg+xml"><link rel="stylesheet" href="../assets/manual.css">
<link rel="alternate" hreflang="zh-CN" href="../zh/{escape(chapter["id"])}.html"><link rel="alternate" hreflang="en-US" href="../en/{escape(chapter["id"])}.html">
</head><body><header class="topbar"><button type="button" class="menu-toggle" aria-label="{escape(language["menu"])}" aria-expanded="false" aria-controls="sidebar"><span></span><span></span><span></span></button>
<a class="brand" href="index.html"><img src="../assets/voxenra-mark.svg" alt=""><strong>Voxenra</strong><span>{escape(language["site"])}</span></a>
<nav class="toplinks" aria-label="Languages"><span class="current-language">{escape(language["name"])}</span><a href="../{other}/{escape(chapter["id"])}.html" lang="{LANGUAGES[other]["pack"]}">{escape(LANGUAGES[other]["name"])}</a><a class="github-link" href="https://github.com/l5769389/voxenra" target="_blank" rel="noopener"><img src="../assets/icons/github.svg" alt="">GitHub</a></nav></header>
<div class="layout"><aside id="sidebar" class="sidebar"><div class="search"><label class="sr-only" for="manual-search">{escape(language["search"])}</label><input id="manual-search" type="search" placeholder="{escape(language["search"])}" autocomplete="off"></div><nav aria-label="{escape(language["menu"])}">{nav}</nav><p class="no-results" hidden>{'没有匹配的章节' if code == 'zh' else 'No matching chapters'}</p></aside>
<main id="content"><div class="reading-layout"><article>{article}</article><aside class="page-outline"><h2>{'本页内容' if code == 'zh' else 'On this page'}</h2><nav>{outline}</nav></aside></div><footer>Voxenra · <a href="https://github.com/l5769389/voxenra">GitHub</a></footer></main></div>
<script src="../assets/manual.js" defer></script></body></html>'''


def render_landing(categories: list[dict], chapters: list[dict], messages: dict[str, str], code: str) -> str:
    language = LANGUAGES[code]
    other = "en" if code == "zh" else "zh"
    heading = "Voxenra 操作手册" if code == "zh" else "Voxenra Manual"
    description = ("从导入影像到测量、分割与导出，按任务查找操作步骤。" if code == "zh"
                   else "Find practical steps for importing, viewing, measuring, segmenting, and exporting medical images.")
    groups = []
    for category in categories:
        links = []
        for chapter in chapters:
            if chapter["category"] != category["id"]:
                continue
            title = messages[f'manual.{chapter["id"]}.title']
            searchable = " ".join([title, messages[f'manual.{chapter["id"]}.summary']] +
                                  [messages[section.get("messageId", f'manual.{chapter["id"]}.section{i}') + ".body"] for i, section in enumerate(chapter["sections"])])
            links.append(f'<a href="{escape(chapter["id"])}.html" data-search="{escape(searchable.lower())}">{escape(title)}</a>')
        groups.append(f'<section class="home-group">{icon(category["icon"])}<div><h2>{escape(messages["manual.category." + category["id"]])}</h2>{"".join(links)}</div></section>')
    return f'''<!doctype html><html lang="{language["pack"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(description)}"><title>{escape(heading)}</title>
<link rel="icon" href="../assets/voxenra-mark.svg" type="image/svg+xml"><link rel="stylesheet" href="../assets/manual.css">
<link rel="alternate" hreflang="zh-CN" href="../zh/index.html"><link rel="alternate" hreflang="en-US" href="../en/index.html"></head>
<body class="home"><header class="topbar"><a class="brand" href="index.html"><img src="../assets/voxenra-mark.svg" alt=""><strong>Voxenra</strong><span>{escape(language["site"])}</span></a>
<nav class="toplinks" aria-label="Languages"><span class="current-language">{escape(language["name"])}</span><a href="../{other}/index.html" lang="{LANGUAGES[other]["pack"]}">{escape(LANGUAGES[other]["name"])}</a><a class="github-link" href="https://github.com/l5769389/voxenra" target="_blank" rel="noopener"><img src="../assets/icons/github.svg" alt="">GitHub</a></nav></header>
<main class="home-main"><div class="home-hero"><div class="home-copy"><h1>{escape(heading)}</h1><p>{escape(description)}</p><div class="home-search"><label class="sr-only" for="landing-search">{escape(language["search"])}</label><input id="landing-search" type="search" placeholder="{escape(language["search"])}" autocomplete="off"></div><div class="home-actions"><a href="quick-start.html">{escape(messages["manual.quick-start.title"])}</a><a href="../{other}/index.html" lang="{LANGUAGES[other]["pack"]}">{escape(LANGUAGES[other]["name"])}</a></div></div><div class="home-visual"><img src="../assets/hero-mpr.png" alt="Voxenra MPR and 3D views" loading="eager"></div></div>
<div class="home-directory" aria-label="{escape(language["menu"])}">{"".join(groups)}</div><p class="no-results" hidden>{'没有匹配的章节' if code == 'zh' else 'No matching chapters'}</p>
<footer>Voxenra · <a href="https://github.com/l5769389/voxenra">GitHub</a></footer></main><script src="../assets/manual.js" defer></script></body></html>'''


def build(output: Path) -> None:
    manifest = load_json(HELP / "manual.json")
    categories = manifest["categories"]
    chapters = [chapter for category in categories for chapter in load_json(HELP / category["file"])]
    if len({item["id"] for item in chapters}) != len(chapters):
        raise ValueError("Duplicate manual chapter IDs")
    known_ids = {item["id"] for item in chapters}
    aliases = manifest["aliases"]
    for chapter in chapters:
        if any(related not in known_ids and related not in aliases for related in chapter.get("related", [])):
            raise ValueError(f'Unknown related chapter in {chapter["id"]}')
    output.mkdir(parents=True, exist_ok=True)
    asset_output = output / "assets"
    asset_output.mkdir(exist_ok=True)
    shutil.copy2(ASSETS / "brand/voxenra-mark.svg", asset_output / "voxenra-mark.svg")
    shutil.copy2(ROOT / "docs/screenshots/11-mpr-3d-layout.png", asset_output / "hero-mpr.png")
    for name in ("manual.css", "manual.js"):
        shutil.copy2(SITE / name, asset_output / name)
    used_icons = {item["icon"] for item in categories} | {"github"}
    (asset_output / "icons").mkdir(exist_ok=True)
    for name in used_icons:
        shutil.copy2(ASSETS / "icons" / f"{name}.svg", asset_output / "icons" / f"{name}.svg")
    used_images = {name for chapter in chapters for name in ([chapter["example"]] if "example" in chapter else chapter.get("examples", []))}
    for name in used_images:
        for prefix in ("", "en/"):
            destination = asset_output / "help" / prefix / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HELP / prefix / name, destination)
    (output / ".nojekyll").touch()
    (output / "index.html").write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=zh/index.html"><link rel="canonical" href="zh/index.html"><title>Voxenra 操作手册</title></head><body><a href="zh/index.html">Voxenra 操作手册</a></body></html>', encoding="utf-8")
    for code, language in LANGUAGES.items():
        messages = load_json(ASSETS / "languages" / f'{language["pack"]}.json')["messages"]
        directory = output / code
        directory.mkdir(exist_ok=True)
        for chapter in chapters:
            (directory / f'{chapter["id"]}.html').write_text(render_page(chapter, categories, chapters, messages, code, aliases), encoding="utf-8")
        (directory / "index.html").write_text(render_landing(categories, chapters, messages, code), encoding="utf-8")
    print(f"Built {len(chapters)} chapters in {len(LANGUAGES)} languages at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output directory for static pages")
    build(parser.parse_args().output)
