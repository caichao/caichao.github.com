# 项目长期记忆

## 个人主页项目 (d:\personweb / caichao.github.com)
- 站点结构：index.html(首页) / publications.html(论文) / demo.html(项目) / patents.html(专利) / photo.html(照片)
- 照片由 albums.txt + build_photos.py 生成 photo.html，update_photos.bat 一键重建
- 项目详情页在 proj_dirs/ 下，CSS 在 style-cards.css
- git remote: https://github.com/caichao/caichao.github.com，分支 master
- GitHub Pages 网址: https://caichao.github.io/

## 主页更新工具 (site_manager.py)
- 2026-07-03 创建：图形界面(tkinter)，纯标准库零依赖，双击「更新主页.bat」启动
- 功能：论文/项目/照片/专利/首页条目 添加，一键 git push 发布
- 每次修改 HTML 前自动备份到 .site_backups/
- 论文插入按年份分组，可同步首页 Recent Publications(保留最新5篇)
- 照片功能复用 albums.txt + build_photos.py 体系
