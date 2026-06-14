#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_photos.py  —— 根据 albums.txt 和 images/ 文件夹自动生成 photo.html

用法：
    python build_photos.py            # 只生成网页（不上传）
    python build_photos.py --publish  # 生成网页 + 提交 + 上传到网站
    （平时不用手动跑，双击 update_photos.bat 会自动调用本脚本并上传）

设计：
  · 读 albums.txt 决定相册顺序、标题、以及每个相册包含哪些图片。
  · 写法① "前缀 | 标题"：自动收集 images/ 里所有「前缀+数字」的图片。
  · 写法② "标题 ::: 文件1, 文件2"：按显式列表收集。
  · 找不到的图片会在终端给出警告，但不会中断（方便你先占位）。
  · 生成的 photo.html 套用 style-cards.css，与其它页面风格一致。
"""

import io
import os
import re
import sys
import subprocess

# 保证在 Windows 控制台也能正常输出中文（不随系统代码页乱码）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(ROOT, "images")
ALBUMS_FILE = os.path.join(ROOT, "albums.txt")
OUTPUT_FILE = os.path.join(ROOT, "photo.html")

IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def list_images():
    """返回 images/ 下所有图片文件名（原始大小写）。"""
    if not os.path.isdir(IMAGES_DIR):
        print(f"[错误] 找不到图片文件夹: {IMAGES_DIR}")
        sys.exit(1)
    return [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMG_EXTS)]


def natural_key(name):
    """让 City2 排在 City10 前面（按编号自然排序）。"""
    parts = re.split(r'(\d+)', name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def collect_by_prefix(prefix, all_images):
    """收集所有以 prefix 开头、紧跟数字的图片，按编号排序。"""
    pat = re.compile(r'^' + re.escape(prefix) + r'\d+', re.IGNORECASE)
    matched = [f for f in all_images if pat.match(os.path.splitext(f)[0])]
    return sorted(matched, key=natural_key)


def parse_albums():
    """解析 albums.txt，返回 ([(title, [filenames...]), ...], warnings)。"""
    if not os.path.isfile(ALBUMS_FILE):
        print(f"[错误] 找不到相册清单: {ALBUMS_FILE}")
        sys.exit(1)

    all_images = list_images()
    albums = []
    warnings = []

    with open(ALBUMS_FILE, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if ":::" in line:
                # 写法②：显式列表
                title, rest = line.split(":::", 1)
                title = title.strip()
                files = [f.strip() for f in rest.split(",") if f.strip()]
                present = []
                for f in files:
                    if f in all_images:
                        present.append(f)
                    else:
                        warnings.append(f"  第{lineno}行 相册「{title}」: 找不到图片 {f}")
                if present:
                    albums.append((title, present))
                else:
                    warnings.append(f"  第{lineno}行 相册「{title}」: 没有任何有效图片，已跳过")

            elif "|" in line:
                # 写法①：前缀 | 标题
                prefix, title = line.split("|", 1)
                prefix = prefix.strip()
                title = title.strip()
                files = collect_by_prefix(prefix, all_images)
                if files:
                    albums.append((title, files))
                else:
                    warnings.append(
                        f"  第{lineno}行 相册「{title}」(前缀 {prefix}): "
                        f"images/ 里没有 {prefix}1, {prefix}2... 这样的图片，已跳过"
                    )
            else:
                warnings.append(f"  第{lineno}行 格式无法识别，已跳过: {line}")

    return albums, warnings


def render_html(albums):
    """把相册列表渲染成完整 photo.html 字符串。"""
    groups = []
    for title, files in albums:
        imgs = "\n".join(
            f'                <img src="images/{f}" alt="{title}">' for f in files
        )
        groups.append(
            f'        <!-- {title} -->\n'
            f'        <div class="gallery-group">\n'
            f'            <h4>{title}</h4>\n'
            f'            <div class="gallery-grid">\n'
            f'{imgs}\n'
            f'            </div>\n'
            f'        </div>'
        )
    groups_html = "\n\n".join(groups)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photos - Chao Cai 蔡超</title>
    <link rel="stylesheet" href="style-cards.css">
    <!-- 本文件由 build_photos.py 自动生成，请勿手动编辑。改照片请编辑 albums.txt 后双击 update_photos.bat -->
</head>
<body>

<!-- Header -->
<header class="site-header">
    <div class="container">
        <div class="header-identity">
            <img class="header-photo" src="images/caichao.jpg" alt="Chao Cai">
            <div class="header-text">
                <h1>Chao Cai 蔡超</h1>
                <p>Associate Professor, College of Life Science and Technology, HUST</p>
            </div>
        </div>
    </div>
</header>

<!-- Navigation -->
<nav class="main-nav">
    <div class="container">
        <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="publications.html">Publications</a></li>
            <li><a href="demo.html">Projects</a></li>
            <li><a href="patents.html">Patents</a></li>
            <li><a href="photo.html" class="active">Photos</a></li>
        </ul>
    </div>
</nav>

<!-- Main Content -->
<div class="content-area">
    <div class="container">

        <div class="page-title">
            <h2>Photo Gallery</h2>
        </div>

{groups_html}

    </div>
</div>

<!-- Footer -->
<footer class="site-footer">
    <div class="container">
        <p>&copy; 2026 Chao Cai 蔡超 &mdash; Huazhong University of Science and Technology</p>
    </div>
</footer>

</body>
</html>
'''


def build():
    """生成 photo.html，返回 (相册数, 照片数)。"""
    albums, warnings = parse_albums()
    total_imgs = sum(len(f) for _, f in albums)
    html = render_html(albums)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    print("=" * 50)
    print("已生成 photo.html")
    print(f"  相册数: {len(albums)}")
    print(f"  照片数: {total_imgs}")
    for title, files in albums:
        print(f"    · {title}: {len(files)} 张")
    if warnings:
        print("-" * 50)
        print("[警告] 以下问题请检查（网页仍已生成）:")
        for w in warnings:
            print(w)
    print("=" * 50)
    return len(albums), total_imgs


def run_git(args):
    """运行 git 命令，返回 (returncode, 输出文本)。"""
    proc = subprocess.run(
        ["git"] + args, cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, proc.stdout.strip()


def publish():
    """git add / commit / push，把网页和图片上传到网站。"""
    print()
    print("[2/3] 记录改动 ...")
    run_git(["add", "images", "photo.html", "albums.txt",
             "build_photos.py", "update_photos.bat"])

    rc, _ = run_git(["diff", "--cached", "--quiet"])
    if rc == 0:
        print("    没有检测到任何改动，无需上传。")
        return 0

    rc, out = run_git(["commit", "-m", "Update photo gallery"])
    if rc != 0:
        print("[错误] 提交失败：")
        print(out)
        return 1

    print()
    print("[3/3] 上传到网站 ...")
    rc, out = run_git(["push", "origin", "master"])
    # 隐藏可能出现在 URL 里的凭据
    out = re.sub(r"//[^@\s]*@", "//***@", out)
    print(out)
    if rc != 0:
        print()
        print("[错误] 上传失败。常见原因：网络问题，或需要重新登录 GitHub。")
        print("        请把上面的英文提示截图发给助手。")
        return 1

    print()
    print("=" * 50)
    print("  完成！约 1-2 分钟后刷新网站即可看到新照片。")
    print("  网址: https://caichao.github.io/photo.html")
    print("=" * 50)
    return 0


def main():
    do_publish = "--publish" in sys.argv
    if do_publish:
        print("[1/3] 生成网页 ...")
    build()
    if do_publish:
        rc = publish()
        sys.exit(rc)


if __name__ == "__main__":
    main()
