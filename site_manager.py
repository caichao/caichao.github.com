#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
site_manager.py - 个人主页内容管理器（图形界面）

功能：论文 / 项目 / 照片 / 专利 / 首页条目 添加，一键 git push 发布。
用法：python site_manager.py  或双击「更新主页.bat」
依赖：仅 Python 标准库。
"""
import os, re, sys, shutil, subprocess, webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(ROOT, "images")
PROJ_DIRS = os.path.join(ROOT, "proj_dirs")
BACKUP_DIR = os.path.join(ROOT, ".site_backups")
INDEX_FILE = os.path.join(ROOT, "index.html")
PUB_FILE = os.path.join(ROOT, "publications.html")
DEMO_FILE = os.path.join(ROOT, "demo.html")
PATENT_FILE = os.path.join(ROOT, "patents.html")
ALBUMS_FILE = os.path.join(ROOT, "albums.txt")
BUILD_PHOTOS = os.path.join(ROOT, "build_photos.py")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
HOME_SECTIONS = [
    ("Research Goals", "研究目标"), ("Students", "学生"), ("Teaching", "教学课程"),
    ("Books", "著作"), ("Professional Activity", "学术兼职"),
    ("Reviewer Service", "审稿服务"), ("Interests", "兴趣爱好"),
]
RECENT_PUB_COUNT = 5


# ---------- 工具 ----------
def ensure_dirs():
    for d in (IMAGES_DIR, PROJ_DIRS, BACKUP_DIR):
        os.makedirs(d, exist_ok=True)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def backup_file(path):
    if not os.path.isfile(path):
        return None
    ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, os.path.join(BACKUP_DIR, f"{ts}_{os.path.basename(path)}"))

def find_block_end(html, start_pos, tag="div"):
    """栈匹配定位闭合标签。"""
    depth, pos = 1, start_pos
    op = re.compile(r'<' + tag + r'(?=[\s>])', re.I)
    cp = re.compile(r'</' + tag + r'\s*>', re.I)
    while pos < len(html):
        mo, mc = op.search(html, pos), cp.search(html, pos)
        if mc is None:
            return -1
        if mo is not None and mo.start() < mc.start():
            depth += 1; pos = mo.end()
        else:
            depth -= 1
            if depth == 0:
                return mc.start()
            pos = mc.end()
    return -1

def esc_attr(s):
    return s.replace('"', '&quot;')

def unique_image_name(filename):
    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)
    ext = ext or ".jpg"
    cand, i = filename, 1
    while os.path.exists(os.path.join(IMAGES_DIR, cand)):
        cand = f"{name}_{i}{ext}"; i += 1
    return cand


# ---------- 论文智能排版 ----------
_VENUE_HINTS = [
    "IEEE Transactions on Vehicular Technology",
    "IEEE Transactions on Vehicle Technology",
    "IEEE Transactions on Mobile Computing",
    "IEEE Transactions on Information Forensics and Security",
    "IEEE Transactions on Network and Service Management",
    "IEEE Transactions on Sustainable Computing",
    "IEEE Transactions on Radiation and Plasma Medical Sciences",
    "IEEE Transactions on Internet of Things",
    "IEEE Transactions on Service Computing",
    "IEEE Internet of Things Journal",
    "IEEE Transactions on Medical Imaging",
    "IEEE INFOCOM", "IEEE TrustCom", "IEEE ICC", "IEEE GLOBECOM",
    "ACM SenSys", "ACM Ubicomp", "ACM MobiCom", "ACM MobiSys",
    "NIMA", "Nature", "Science",
]

# 常见"标题词"——这些词出现在标题里但不是姓氏，避免误判为人名
# 注意：绝不要把真实姓氏（如 Cai/Zhou/Wang 等）放进来
_TITLE_WORDS = {
    # 常见技术/学术词，首字母大写但不是人名
    "Learning","Network","Networks","System","Systems","Computing","Processing",
    "Communication","Communications","Technology","Technologies","Method","Methods",
    "Algorithm","Algorithms","Approach","Recovery","Monitoring","Deployment","Routing",
    "Offloading","Multicast","Constellations","Defined","Software","Joint","Delay",
    "Sensitive","Efficient","Resource","Indoor","Localization","Adversarial","Attacks",
    "Physical","World","Object","Placement","Differentiable","Coincident","Boost",
    "Correct","Post","Improve","Performance","Multiple","Voltage","Threshold","Range",
    "Based","Game","Theoretic","Load","Balancing","Satellite","Lightweight","Hybrid",
    "Device","Identification","Applications","Service","Mesh","Clouds","Probabilistic",
    "Orchestration","Collaborative","Large","Scale","Data","Storage","Real","Efficiency",
    "Blockchain","Enhanced","Optimizing","Truly","Sampling","Category","Oriented",
    "Knowledge","Poisoning","Retrieval","Augmented","Generation","Establishing","Intra",
    "Solid","Sonic","Vital","Signs","Distillation","Leveraging","Fine","Grained",
    "Practical","Characterization","Vehicular","Heterogeneous","Edges","Deep",
    "Reinforcement","Aggregation","Latency","Task","Energy","Acoustic","Transceivers",
    "Secure","Edge","Crystal","Length","Using","Neural","Physics","Audio","Sounds",
    "Heart","Pressure","Blood","Information","Wireless","Powered","Passive",
    "Temperature","Vision","Computer","Crane","Stabilization","Cargo","Magnetic",
    "Resonance","Waterproof","Precision","Support","Point","Move","Reduce","Motion",
    "Relative","Ground","Conventional","Tapped","Line","Dead","Resilience",
    "Fluctuations","Chain","Resources","Increasing","Sensor","Sensors","Wearable",
    "Ear","Wearables","Readout","Electronics","Ultrasonic","Sensing","Spatial",
    "Thermometer","Mobile","Commodity","Turning","Continuous","Respiratory",
    "Analytical","Signal","Signals","Pulmonary","Artery","Microphone","Informed",
    "Adversarial","Robust","Broadband","Centers","Uav","Node","Ranking","Matrix",
    "Proportional","Reducing","Logic","Harvests","Communicates","Emulate","Unstable",
    "Board","Sea","Track","Speed","Multi","Channel","Acquisition","Build","Chained",
    "Together","Platform","Digital","Converter","Recover","Recovering","Contains",
    "Leverage","Find","Via","Through","Under","Over","From","Into","For","And",
    "The","Of","In","On","To","A","An","With","Without","Toward","Towards",
    "Against","Between","Within","Across","Internet","Things","Journal",
    "Transactions","Forensics","Sustainable","Medical","Imaging","Radiation",
    "Plasma","Sciences","Pervasive","Ubiquitous","Conference","Symposium",
    "Proceedings","Annual","International","Workshop","Special","Issue",
    # 数字/单位后面跟字母的不会出现，但安全起见
    "FPGA","REMVT","MVT","TwinPop","EarPCG","CORA","Loki","CatPoison","AcuTe",
}

def _is_name_pair(w1, w2):
    """判断两个词是否构成一个人名对（名+姓）。"""
    w1c = w1.rstrip('.,')
    w2c = w2.rstrip('.,')
    # 第二个词不能是标题词
    if w2c in _TITLE_WORDS:
        return False
    # 第一个词：单字母缩写 或 首字母大写的短词
    if len(w1c) == 1 and w1c.isupper():
        first_ok = True
    elif len(w1c) <= 10 and w1c and w1c[0].isupper() and w1c[1:].islower():
        first_ok = w1c not in _TITLE_WORDS
    else:
        first_ok = False
    # 第二个词：首字母大写，2-15字符，且不是标题词
    second_ok = (2 <= len(w2c) <= 15 and w2c[0].isupper()
                 and (w2c[1:].islower() or len(w2c) == 1))
    return first_ok and second_ok

def _find_authors_title(remaining):
    """占位，实际逻辑在下方 _find_authors_title_v2"""
    return _find_authors_title_v2(remaining)

def _find_authors_title_v2(remaining):
    """
    从去掉venue/year后的文本拆分作者和标题。
    核心思路：人名是2词组合（名+姓），多个连续人名（间隔仅逗号/空格）组成作者列表。
    标题单词多，人名块之外的文本就是标题。人名块可在任意位置。
    """
    remaining = re.sub(r'\s+', ' ', remaining).strip(' ,.')

    # 策略1：标题被引号包裹
    qm = re.search(r'[""\u2018\u2019]([^""\u2018\u2019]+)[""\u2018\u2019]', remaining)
    if qm:
        title = qm.group(1).strip()
        authors = (remaining[:qm.start()] + ' ' + remaining[qm.end():]).strip(' ,.')
        authors = re.sub(r',\s*,', ',', authors).strip(' ,.')
        # 作者里只剩 et al 的情况
        if authors.lower() in ('et al', 'et al.', 'et., al', 'et., al.'):
            authors = 'et al.'
        if authors and title and (',' in authors or 'et al' in authors.lower() or len(authors.split()) <= 8):
            return authors, title

    # 策略2：贪心扫描非重叠人名对，按连续性分组，选最长组作为作者
    tokens = re.findall(r'\S+', remaining)
    # 贪心非重叠：找到一对就跳过2个token，避免 "Wang Jiawen" 之类的重叠误判
    pairs = []
    i = 0
    while i < len(tokens) - 1:
        if _is_name_pair(tokens[i], tokens[i+1]):
            pairs.append((i, i+1))
            i += 2  # 跳过这一对，避免重叠
        else:
            i += 1
    if pairs:
        # 按连续性分组：两个pair之间间隔<=2个token（逗号/空格）算连续
        groups = []
        current = [pairs[0]]
        for p in pairs[1:]:
            gap = p[0] - current[-1][1]
            if 1 <= gap <= 2:  # 非重叠且间隔小（逗号/et al等）
                current.append(p)
            else:
                groups.append(current)
                current = [p]
        groups.append(current)
        # 至少2个人名对才可靠
        candidate = [g for g in groups if len(g) >= 2]
        if candidate:
            best = max(candidate, key=len)
            a_start_tok = best[0][0]
            a_end_tok = best[-1][1]
            # 检查作者后面是否紧跟 "et al" / "et. al." / "et., al"，若有则扩展作者区间
            j = a_end_tok + 1
            while j < len(tokens) and tokens[j] in (',', 'et', 'et.', 'et,', 'al', 'al.', 'al,'):
                a_end_tok = j
                j += 1
            # 转回字符位置
            char_pos = 0
            tok_positions = []
            for t in tokens:
                idx = remaining.find(t, char_pos)
                tok_positions.append((idx, idx + len(t)))
                char_pos = idx + len(t)
            a_start = tok_positions[a_start_tok][0]
            a_end = tok_positions[a_end_tok][1]
            authors = remaining[a_start:a_end].strip(' ,.')
            # 规范化 et al
            authors = re.sub(r',?\s*et\.?\s*,?\s*al\.?', ', et al.', authors, flags=re.I)
            authors = re.sub(r'^,\s*', '', authors).strip()
            title = (remaining[:a_start] + ' ' + remaining[a_end:]).strip(' ,.')
            title = re.sub(r'\s+', ' ', title).strip(' ,.')
            # 清理作者：补逗号（无逗号时按人名对重建）
            if authors and ',' not in authors and 'et al' not in authors.lower():
                name_strs = []
                for p in best:
                    name_strs.append(tokens[p[0]] + ' ' + tokens[p[1]].rstrip('.,'))
                authors = ', '.join(name_strs)
            if authors and title:
                return authors, title

    # 策略3：按 ". " 拆（作者列表以句号结尾）
    if '. ' in remaining:
        idx = remaining.find('. ')
        before = remaining[:idx].strip(' ,.')
        after = remaining[idx+2:].strip(' ,.')
        if before and after:
            before_words = len(before.split())
            after_words = len(after.split())
            if (',' in before or 'et al' in before.lower()) and after_words >= 3:
                return before, after
            if before_words <= 12 and after_words >= 4:
                return before, after

    return "", remaining

def _find_venue(text):
    for v in _VENUE_HINTS:
        m = re.search(re.escape(v), text, re.I)
        if m:
            return v, m.group(0)
    m = re.search(r'(?:IEEE\s+)?(?:Transactions on [A-Z][\w\s,]+?|Journal of [A-Z][\w\s,]+?|Proc\.?\s*of\s+[A-Z][\w\s,]+?)(?=[,\s"\'\n]|$)', text)
    if m:
        return m.group(0).strip(), m.group(0).strip()
    return None, None

def _find_year(text, fallback=None):
    years = re.findall(r'\b(20\d{2})\b', text)
    return years[-1] if years else fallback

def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] in '""\'\u2018\u2019' and s[-1] in '""\'\u2018\u2019':
        return s[1:-1].strip()
    return s

def format_publication(raw_text, year_hint=None):
    """排版任意格式论文 -> Authors. "Title", in <em>Venue</em>, Year"""
    if not raw_text or not raw_text.strip():
        return "", year_hint
    text = raw_text.strip()
    if "<em>" in text or "</a>" in text or "<strong>" in text:
        return text, _find_year(text, year_hint)
    text = re.sub(r'\s+', ' ', text)
    venue, venue_raw = _find_venue(text)
    year = _find_year(text, year_hint)
    # 移除 venue 和 year
    remaining = text
    if venue_raw:
        remaining = remaining.replace(venue_raw, ' \x00 ', 1)
    if year:
        remaining = re.sub(r'\b' + year + r'\b', ' \x00 ', remaining)
    remaining = re.sub(r'\bin\s+\x00', '\x00', remaining, flags=re.I, count=1)
    remaining = remaining.replace('\x00', ' ')
    remaining = re.sub(r'\s+', ' ', remaining).strip(' ,.')
    authors, title = _find_authors_title(remaining)
    title = _strip_quotes(title)
    # 如果作者无逗号但有多个姓名对，自动加逗号分隔
    if authors and ',' not in authors:
        pairs = re.findall(r'(?:[A-Z]\.?|[A-Z][a-z]{1,9})\s+[A-Z][a-z]{1,14}', authors)
        if len(pairs) > 1:
            authors = ', '.join(pairs)
    # 组装：Authors. "Title", in <em>Venue</em>, Year
    result = ""
    if authors:
        authors = re.sub(r',?\s*\bet\.?\s*,?\s*al\.?', ', et al.', authors, flags=re.I)
        result += authors.rstrip('.') + '. '
    if title:
        result += f'"{title}"'
    if venue:
        result += f', in&nbsp;<em>{venue}</em>'
    if year:
        result += f', {year}'
    result = result.strip()
    if not result:
        return text, year
    return result, year


# ---------- 论文 ----------
def add_publication(year, citation_html, sync_home=True):
    year = str(year).strip(); citation_html = citation_html.strip()
    if not year or not citation_html:
        return False, "年份和引文都不能为空。"
    html = read_file(PUB_FILE); backup_file(PUB_FILE)
    new_li = f'          <li>{citation_html}</li>\n'
    sec = re.compile(r'(<section class="publication-year" aria-labelledby="pub-' + re.escape(year) + r'">.*?<ul class="publication-list">)', re.S)
    m = sec.search(html)
    if m:
        html = html[:m.end()] + "\n" + new_li + html[m.end():]
        msg_pub = f"已插入到 publications.html 的 {year} 年份组最前。"
    else:
        ns = (f'      <section class="publication-year" aria-labelledby="pub-{year}">\n'
              f'        <h2 id="pub-{year}">{year}</h2>\n'
              f'        <ul class="publication-list">\n{new_li}        </ul>\n      </section>\n')
        years = [(int(y.group(1)), y.group(0)) for y in re.finditer(r'aria-labelledby="pub-(\d{4})"', html)]
        try:
            yi = int(year)
        except ValueError:
            yi = 0
        ip = None
        for yv, ft in years:
            if yv < yi:
                idx = html.find(ft); ss = html.rfind('<section', 0, idx)
                if ss != -1:
                    ip = ss; break
        if ip is None:
            ct = re.search(r'<section class="publication-years">\s*', html)
            ip = ct.end() if ct else html.find('<section class="publication-year"')
        html = html[:ip] + ns + html[ip:]
        msg_pub = f"已在 publications.html 新建 {year} 年份组并插入。"
    write_file(PUB_FILE, html)
    msg_home = ""
    if sync_home:
        idx = read_file(INDEX_FILE); backup_file(INDEX_FILE)
        ol = re.compile(r'(<ol class="publication-list">)(.*?)(</ol>)', re.S)
        om = ol.search(idx)
        if om:
            ex = re.findall(r'<li>.*?</li>', om.group(2), re.S)
            nl = ([f'<li>{citation_html}</li>'] + ex)[:RECENT_PUB_COUNT]
            ni = "\n        " + "\n        ".join(nl) + "\n      "
            idx = idx[:om.start(2)] + ni + idx[om.end(2):]
            write_file(INDEX_FILE, idx)
            msg_home = f" 首页 Recent Publications 已同步（保留最新{RECENT_PUB_COUNT}篇）。"
        else:
            msg_home = " （未找到首页 Recent Publications，跳过同步。）"
    return True, msg_pub + msg_home


# ---------- 项目 ----------
def add_project(title, description, image_src, page_slug="", create_page=False):
    title = title.strip(); description = description.strip()
    if not title:
        return False, "项目标题不能为空。"
    html = read_file(DEMO_FILE); backup_file(DEMO_FILE)
    dst = None
    if image_src and os.path.isfile(image_src):
        ensure_dirs(); dst = unique_image_name(image_src)
        shutil.copy2(image_src, os.path.join(IMAGES_DIR, dst))
        img = f'<img class="card-img" src="images/{dst}" alt="{esc_attr(title)}">'
    else:
        img = f'<img class="card-img" src="images/caichao.jpg" alt="{esc_attr(title)}">'
    link = ""
    if page_slug:
        link = f'                    <a class="card-link" href="proj_dirs/{page_slug}.html">Project Page \u2192</a>\n'
    card = (f'\n            <!-- Project (auto) -->\n'
            f'            <div class="project-card">\n'
            f'                {img}\n'
            f'                <div class="card-body">\n'
            f'                    <h4>{title}</h4>\n'
            f'                    <p>{description}</p>\n{link}'
            f'                </div>\n            </div>\n')
    gm = re.search(r'<div\s+class="project-grid"[^>]*>', html)
    if not gm:
        return False, "demo.html 中未找到 project-grid 容器。"
    ce = find_block_end(html, gm.end(), "div")
    if ce == -1:
        return False, "无法定位 project-grid 闭合标签。"
    html = html[:ce] + card + html[ce:]
    write_file(DEMO_FILE, html)
    msgs = [f"已在 demo.html 添加项目卡片「{title}」。"]
    if dst:
        msgs.append(f"图片已复制到 images/{dst}。")
    if create_page and page_slug:
        pp = os.path.join(PROJ_DIRS, page_slug + ".html")
        if os.path.exists(pp):
            msgs.append(f"详情页 proj_dirs/{page_slug}.html 已存在，未覆盖。")
        else:
            write_file(pp, _page_template(title, description))
            msgs.append(f"已生成详情页模板 proj_dirs/{page_slug}.html。")
    return True, " ".join(msgs)

def _page_template(title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Chao Cai</title>
    <link rel="stylesheet" href="../style-cards.css">
</head>
<body>
<header class="site-header"><div class="container"><div class="header-identity">
    <img class="header-photo" src="../images/caichao.jpg" alt="Chao Cai">
    <div class="header-text"><h1>Chao Cai \u8521\u8d85</h1>
    <p>Associate Professor, College of Life Science and Technology, HUST</p></div>
</div></div></header>
<nav class="main-nav"><div class="container"><ul>
    <li><a href="../index.html">Home</a></li>
    <li><a href="../publications.html">Publications</a></li>
    <li><a href="../demo.html" class="active">Projects</a></li>
    <li><a href="../patents.html">Patents</a></li>
    <li><a href="../photo.html">Photos</a></li>
</ul></div></nav>
<div class="content-area"><div class="container">
    <div class="page-title"><h2>{title}</h2></div>
    <section class="section-block"><h3>Project Description</h3><p>{description}</p>
    <!-- \u5728\u8fd9\u91cc\u8865\u5145\u8be6\u7ec6\u63cf\u8ff0\u3001\u56fe\u7247\u3001\u89c6\u9891\u3001demo \u94fe\u63a5\u7b49 -->
    </section>
    <section class="section-block"><h3>People</h3><ul>
        <li>Dr. Chao Cai (Associate Professor) - Huazhong University of Science and Technology</li>
    </ul></section>
    <section class="section-block"><h3>Related Publications</h3><ul>
        <!-- <li>...</li> -->
    </ul></section>
    <p><a href="../demo.html">\u2190 Back to Projects</a></p>
</div></div>
<footer class="site-footer"><div class="container">
    <p>&copy; {datetime.now().year} Chao Cai \u8521\u8d85 &mdash; Huazhong University of Science and Technology</p>
</div></footer>
</body></html>
'''


# ---------- 专利 ----------
def add_patent(title, patent_type, authors, image_src=""):
    title = title.strip()
    if not title:
        return False, "专利标题不能为空。"
    html = read_file(PATENT_FILE); backup_file(PATENT_FILE)
    if image_src and os.path.isfile(image_src):
        ensure_dirs(); dst = unique_image_name(image_src)
        shutil.copy2(image_src, os.path.join(IMAGES_DIR, dst))
        img = f'<img src="images/{dst}" alt="{esc_attr(title)}">'
    else:
        img = f'<img src="images/caichao.jpg" alt="{esc_attr(title)}">'
    block = (f'\n    <section class="project">\n      {img}\n      <div>\n'
             f'        <h2>{title}</h2>\n'
             f'        <p><em>{patent_type}</em></p>\n'
             f'        <p>{authors}</p>\n      </div>\n    </section>\n')
    fm = re.search(r'\s*<!-- Footer -->', html)
    ia = fm.start() if fm else html.rfind('</div>')
    if ia == -1:
        return False, "patents.html 结构异常。"
    html = html[:ia] + block + html[ia:]
    write_file(PATENT_FILE, html)
    return True, f"已在 patents.html 添加专利「{title}」。"


# ---------- 首页条目 ----------
def add_home_item(section_title, item_html, position="end"):
    item_html = item_html.strip()
    if not item_html:
        return False, "条目内容不能为空。"
    html = read_file(INDEX_FILE); backup_file(INDEX_FILE)
    sp = re.compile(r'(<h2>' + re.escape(section_title) + r'</h2>)(.*?)(</section>)', re.S)
    m = sp.search(html)
    if not m:
        return False, f"首页未找到栏目「{section_title}」。"
    inner = m.group(2)
    lp = re.compile(r'(<ul>)(.*?)(</ul>)', re.S); lm = lp.search(inner)
    if not lm:
        lp = re.compile(r'(<ol>)(.*?)(</ol>)', re.S); lm = lp.search(inner)
        if not lm:
            return False, f"栏目「{section_title}」没有可追加的列表。"
    lis = m.start(2) + lm.end(1); lie = m.start(2) + lm.start(3)
    nl = f'\n        <li>{item_html}</li>'
    html = (html[:lis] + nl + html[lis:]) if position == "start" else (html[:lie] + nl + html[lie:])
    write_file(INDEX_FILE, html)
    return True, f"已给首页「{section_title}」栏目添加条目。"


# ---------- 照片 ----------
def _parse_albums():
    if not os.path.isfile(ALBUMS_FILE):
        return []
    all_imgs = ([f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMG_EXTS)]
                if os.path.isdir(IMAGES_DIR) else [])
    def nk(n): return [int(p) if p.isdigit() else p.lower() for p in re.split(r'(\d+)', n)]
    def cbp(prefix):
        p = re.compile(r'^' + re.escape(prefix) + r'\d+', re.I)
        return sorted([f for f in all_imgs if p.match(os.path.splitext(f)[0])], key=nk)
    albums = []
    with open(ALBUMS_FILE, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if ":::" in line:
                t, r = line.split(":::", 1)
                albums.append((t.strip(), "explicit", [f.strip() for f in r.split(",") if f.strip()]))
            elif "|" in line:
                p, t = line.split("|", 1)
                albums.append((t.strip(), "prefix", cbp(p.strip())))
    return albums

def list_album_titles():
    return [a[0] for a in _parse_albums()]

def add_photos(image_paths, album_title, new_album=False):
    if not image_paths:
        return False, "请先选择图片。"
    if not album_title.strip():
        return False, "相册标题不能为空。"
    ensure_dirs(); copied = []
    for src in image_paths:
        if not os.path.isfile(src):
            continue
        d = unique_image_name(src); shutil.copy2(src, os.path.join(IMAGES_DIR, d)); copied.append(d)
    if not copied:
        return False, "没有可用的图片文件。"
    backup_file(ALBUMS_FILE)
    lines = []
    if os.path.isfile(ALBUMS_FILE):
        with open(ALBUMS_FILE, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    found = False
    if not new_album:
        for i, raw in enumerate(lines):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            t = mode = None
            if ":::" in line:
                t = line.split(":::", 1)[0].strip(); mode = "explicit"
            elif "|" in line:
                t = line.split("|", 1)[1].strip(); mode = "prefix"
            if t == album_title.strip():
                if mode == "explicit":
                    ex = [f.strip() for f in line.split(":::", 1)[1].split(",") if f.strip()]
                    lines[i] = f"{t} ::: " + ", ".join(ex + copied) + "\n"
                else:
                    pfx = line.split("|", 1)[0].strip()
                    p = re.compile(r'^' + re.escape(pfx) + r'\d+', re.I)
                    ai = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMG_EXTS)]
                    mt = sorted([f for f in ai if p.match(os.path.splitext(f)[0])],
                                key=lambda n: [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', n)])
                    af = mt + [c for c in copied if c not in mt]
                    lines[i] = f"{t} ::: " + ", ".join(af) + "\n"
                found = True; break
        if not found:
            new_album = True
    if new_album:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(f"\n{album_title.strip()} ::: " + ", ".join(copied) + "\n")
    with open(ALBUMS_FILE, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    msg = f"已复制 {len(copied)} 张图片到 images/，并更新 albums.txt。"
    if os.path.isfile(BUILD_PHOTOS):
        try:
            r = subprocess.run([sys.executable, BUILD_PHOTOS], cwd=ROOT,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            msg += "\n" + (r.stdout or r.stderr or "photo.html 已重建。")
        except Exception as e:
            msg += f"\n重建 photo.html 失败：{e}（可手动双击 update_photos.bat）"
    else:
        msg += " （未找到 build_photos.py，请手动更新 photo.html）"
    return True, msg


# ---------- Git ----------
def git_run(args):
    p = subprocess.run(["git"] + args, cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    return p.returncode, re.sub(r"//[^@\s]*@", "//***@", p.stdout.strip())

def git_status_text():
    rc, out = git_run(["status", "-s"])
    return out if out else "（工作区干净，没有改动）"

def git_publish(commit_msg, callback=None):
    def emit(s):
        if callback: callback(s)
        else: print(s)
    commit_msg = (commit_msg or "Update site content").strip()
    emit("[1/4] 检查工作区 ...")
    rc, out = git_run(["add", "-A"])
    if rc != 0:
        emit("git add 失败：\n" + out); return False, "git add 失败。"
    rc, _ = git_run(["diff", "--cached", "--quiet"])
    if rc == 0:
        emit("没有检测到任何改动，无需发布。"); return True, "没有改动需要发布。"
    emit("[2/4] 提交改动 ...")
    rc, out = git_run(["commit", "-m", commit_msg])
    if rc != 0:
        emit("git commit 失败：\n" + out); return False, "git commit 失败。"
    emit(out)
    emit("[3/4] 推送到远程 ...")
    rc, out = git_run(["push", "origin", "master"])
    emit(out)
    if rc != 0:
        emit("[!] 推送失败。常见原因：网络问题，或 GitHub 凭据过期需要重新登录。")
        return False, "git push 失败，请查看上方输出。"
    emit("[4/4] 完成！约 1-2 分钟后刷新网站即可看到更新。")
    emit("    网址: https://caichao.github.io/")
    return True, "发布成功！"


# ==================================================================
#  GUI
# ==================================================================
class SiteManagerApp:
    def __init__(self, root):
        self.root = root
        root.title("个人主页管理器 — Chao Cai 蔡超")
        root.geometry("900x720"); root.minsize(820, 640)
        try: root.tk.call("tk", "scaling", 1.2)
        except Exception: pass
        s = ttk.Style()
        try: s.theme_use("clam")
        except Exception: pass
        s.configure("TLabel", font=("Microsoft YaHei", 10))
        s.configure("TButton", font=("Microsoft YaHei", 10))
        s.configure("Header.TLabel", font=("Microsoft YaHei", 13, "bold"))
        s.configure("TNotebook.Tab", font=("Microsoft YaHei", 10))
        self._build_ui()

    def _st(self, parent, h=8):
        return scrolledtext.ScrolledText(parent, height=h, wrap="word", font=("Consolas", 9))

    def _show(self, w, ok, msg):
        w.delete("1.0", "end"); w.insert("1.0", ("[完成] " if ok else "[失败] ") + msg + "\n")
        self.status.config(text=("完成：" if ok else "失败：") + msg.splitlines()[0][:70])

    def _pick(self, var):
        ps = filedialog.askopenfilenames(title="选择图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.gif *.webp"), ("所有文件", "*.*")])
        if ps: var.set(ps[0])

    def _build_ui(self):
        nb = ttk.Notebook(self.root); nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._t_pub(nb); self._t_proj(nb); self._t_photo(nb); self._t_patent(nb)
        self._t_home(nb); self._t_publish(nb); self._t_help(nb)
        bar = ttk.Frame(self.root); bar.pack(fill="x", side="bottom")
        self.status = ttk.Label(bar, text="就绪。修改前会自动备份到 .site_backups/")
        self.status.pack(side="left", padx=8, pady=4)
        ttk.Button(bar, text="本地预览", command=self._preview).pack(side="right", padx=4, pady=4)

    # 论文
    def _t_pub(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F4C4 论文")
        ttk.Label(f, text="添加论文", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="年份：").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.pub_year = ttk.Entry(f, width=12); self.pub_year.grid(row=1, column=1, sticky="w", pady=6)
        self.pub_year.insert(0, str(datetime.now().year))
        # 输入模式：智能排版 / 原样HTML
        mode_frame = ttk.Frame(f); mode_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Label(mode_frame, text="输入内容：").pack(side="left")
        self.pub_mode = tk.StringVar(value="smart")
        ttk.Radiobutton(mode_frame, text="智能排版（推荐，随意粘贴即可）", variable=self.pub_mode, value="smart").pack(side="left", padx=4)
        ttk.Radiobutton(mode_frame, text="原样 HTML（自己写好 <em> 等标签）", variable=self.pub_mode, value="raw").pack(side="left", padx=4)
        # 内容输入框
        ttk.Label(f, text="内容：").grid(row=3, column=0, sticky="ne", padx=8, pady=6)
        self.pub_cit = scrolledtext.ScrolledText(f, width=76, height=6, wrap="word", font=("Microsoft YaHei", 10))
        self.pub_cit.grid(row=3, column=1, sticky="we", pady=6)
        ttk.Label(f, text="智能模式：直接粘贴论文信息（作者、标题、期刊、年份混在一起也行），程序会自动识别并排版。", foreground="#666").grid(row=4, column=1, sticky="w", padx=8)
        # 排版预览框
        ttk.Label(f, text="排版预览：").grid(row=5, column=0, sticky="ne", padx=8, pady=6)
        self.pub_preview = self._st(f, 3); self.pub_preview.grid(row=5, column=1, sticky="we", pady=6)
        self.pub_preview.config(state="disabled")
        # 按钮
        btn_frame = ttk.Frame(f); btn_frame.grid(row=6, column=1, sticky="w", pady=6)
        ttk.Button(btn_frame, text="🔍 预览排版", command=self._do_pub_preview).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="✓ 添加论文", command=self._do_pub).pack(side="left", padx=4)
        # 同步选项
        self.pub_sync = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text=f"同步更新首页 Recent Publications（保留最新{RECENT_PUB_COUNT}篇）", variable=self.pub_sync).grid(row=7, column=1, sticky="w", pady=6)
        # 结果
        self.pub_res = self._st(f, 4); self.pub_res.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(8, weight=1)

    def _do_pub_preview(self):
        """预览排版结果。"""
        raw = self.pub_cit.get("1.0", "end").strip()
        if not raw:
            messagebox.showinfo("提示", "请先输入论文内容。"); return
        year_hint = self.pub_year.get().strip()
        if self.pub_mode.get() == "raw":
            formatted = raw
        else:
            formatted, detected_year = format_publication(raw, year_hint)
            # 如果检测到年份且年份框为空，自动填充
            if detected_year and not year_hint:
                self.pub_year.delete(0, "end"); self.pub_year.insert(0, detected_year)
        self.pub_preview.config(state="normal")
        self.pub_preview.delete("1.0", "end")
        self.pub_preview.insert("1.0", formatted)
        self.pub_preview.config(state="disabled")

    def _do_pub(self):
        raw = self.pub_cit.get("1.0", "end").strip()
        if not raw:
            self._show(self.pub_res, False, "请输入论文内容。"); return
        year = self.pub_year.get().strip()
        if self.pub_mode.get() == "raw":
            citation = raw
        else:
            citation, detected_year = format_publication(raw, year)
            if detected_year and not year:
                year = detected_year
                self.pub_year.delete(0, "end"); self.pub_year.insert(0, detected_year)
        ok, msg = add_publication(year, citation, self.pub_sync.get())
        self._show(self.pub_res, ok, msg)
        if ok:
            self.pub_preview.config(state="normal")
            self.pub_preview.delete("1.0", "end")
            self.pub_preview.insert("1.0", citation)
            self.pub_preview.config(state="disabled")

    # 项目
    def _t_proj(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F9EA 项目")
        ttk.Label(f, text="添加项目", style="Header.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="项目标题：").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.pj_t = ttk.Entry(f, width=58); self.pj_t.grid(row=1, column=1, columnspan=2, sticky="we", pady=6)
        ttk.Label(f, text="一句话描述：").grid(row=2, column=0, sticky="ne", padx=8, pady=6)
        self.pj_d = scrolledtext.ScrolledText(f, width=64, height=3, wrap="word", font=("Microsoft YaHei", 10))
        self.pj_d.grid(row=2, column=1, columnspan=2, sticky="we", pady=6)
        ttk.Label(f, text="配图：").grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.pj_img = tk.StringVar()
        ttk.Entry(f, textvariable=self.pj_img, width=50).grid(row=3, column=1, sticky="we", pady=6)
        ttk.Button(f, text="浏览…", command=lambda: self._pick(self.pj_img)).grid(row=3, column=2, padx=4, pady=6)
        ttk.Label(f, text="详情页文件名：").grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.pj_slug = ttk.Entry(f, width=24); self.pj_slug.grid(row=4, column=1, sticky="w", pady=6)
        ttk.Label(f, text="（留空=无详情页；如 earpcg → proj_dirs/earpcg.html）", foreground="#666").grid(row=4, column=2, sticky="w", padx=4)
        self.pj_cp = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="同时生成详情页模板", variable=self.pj_cp).grid(row=5, column=1, sticky="w", pady=6)
        ttk.Button(f, text="添加项目", command=self._do_proj).grid(row=6, column=1, sticky="w", pady=10)
        self.pj_res = self._st(f, 5); self.pj_res.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(7, weight=1)

    def _do_proj(self):
        ok, msg = add_project(self.pj_t.get(), self.pj_d.get("1.0", "end").strip(),
                              self.pj_img.get().strip(), self.pj_slug.get().strip(), self.pj_cp.get())
        self._show(self.pj_res, ok, msg)

    # 照片
    def _t_photo(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F4F7 照片")
        ttk.Label(f, text="添加照片", style="Header.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="选择图片（可多选）：").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.ph_paths = []; self.ph_lbl = ttk.Label(f, text="（未选择）", foreground="#666")
        self.ph_lbl.grid(row=1, column=1, sticky="w", pady=6)
        ttk.Button(f, text="浏览…", command=self._pick_photos).grid(row=1, column=2, padx=4, pady=6)
        self.ph_new = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="新建相册", variable=self.ph_new, command=self._toggle_album).grid(row=2, column=0, sticky="e", padx=8, pady=6)
        ttk.Label(f, text="相册：").grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.ph_combo = ttk.Combobox(f, width=32, state="readonly"); self.ph_combo.grid(row=3, column=1, sticky="w", pady=6)
        self.ph_entry = ttk.Entry(f, width=34); self._refresh_albums()
        ttk.Button(f, text="添加照片", command=self._do_photos).grid(row=4, column=1, sticky="w", pady=10)
        self.ph_res = self._st(f, 8); self.ph_res.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(5, weight=1)

    def _toggle_album(self):
        if self.ph_new.get():
            self.ph_combo.grid_remove(); self.ph_entry.grid(row=3, column=1, sticky="w", pady=6)
        else:
            self.ph_entry.grid_remove(); self.ph_combo.grid(row=3, column=1, sticky="w", pady=6)

    def _refresh_albums(self):
        ts = list_album_titles(); self.ph_combo["values"] = ts if ts else ["（无）"]
        if ts: self.ph_combo.current(0)

    def _pick_photos(self):
        ps = filedialog.askopenfilenames(title="选择图片（可多选）",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.gif *.webp"), ("所有文件", "*.*")])
        if ps:
            self.ph_paths = list(ps)
            ns = [os.path.basename(p) for p in self.ph_paths]
            self.ph_lbl.config(text=f"已选 {len(ns)} 张：" + ", ".join(ns[:3]) + ("…" if len(ns) > 3 else ""))

    def _do_photos(self):
        if not self.ph_paths:
            messagebox.showinfo("提示", "请先选择图片。"); return
        if self.ph_new.get():
            t = self.ph_entry.get().strip()
            if not t: messagebox.showinfo("提示", "请输入新相册标题。"); return
            ok, msg = add_photos(self.ph_paths, t, True)
        else:
            t = self.ph_combo.get()
            if not t or t == "（无）": messagebox.showinfo("提示", "请选择已有相册，或勾选「新建相册」。"); return
            ok, msg = add_photos(self.ph_paths, t, False)
        self._show(self.ph_res, ok, msg)
        if ok: self._refresh_albums()

    # 专利
    def _t_patent(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F4DC 专利")
        ttk.Label(f, text="添加专利", style="Header.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="专利标题：").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.pt_t = ttk.Entry(f, width=56); self.pt_t.grid(row=1, column=1, columnspan=2, sticky="we", pady=6)
        ttk.Label(f, text="类型：").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.pt_type = ttk.Entry(f, width=40); self.pt_type.grid(row=2, column=1, sticky="w", pady=6)
        self.pt_type.insert(0, "Singapore patent")
        ttk.Label(f, text="如：中国发明专利 / Singapore patent", foreground="#666").grid(row=2, column=2, sticky="w", padx=4)
        ttk.Label(f, text="作者：").grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.pt_auth = ttk.Entry(f, width=56); self.pt_auth.grid(row=3, column=1, columnspan=2, sticky="we", pady=6)
        ttk.Label(f, text="配图：").grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.pt_img = tk.StringVar()
        ttk.Entry(f, textvariable=self.pt_img, width=48).grid(row=4, column=1, sticky="we", pady=6)
        ttk.Button(f, text="浏览…", command=lambda: self._pick(self.pt_img)).grid(row=4, column=2, padx=4, pady=6)
        ttk.Button(f, text="添加专利", command=self._do_patent).grid(row=5, column=1, sticky="w", pady=10)
        self.pt_res = self._st(f, 5); self.pt_res.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(6, weight=1)

    def _do_patent(self):
        ok, msg = add_patent(self.pt_t.get(), self.pt_type.get(), self.pt_auth.get(), self.pt_img.get().strip())
        self._show(self.pt_res, ok, msg)

    # 首页条目
    def _t_home(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F3E0 首页条目")
        ttk.Label(f, text="给首页栏目添加条目", style="Header.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="栏目：").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        titles = [t[0] for t in HOME_SECTIONS]
        self.hm_sec = ttk.Combobox(f, width=28, state="readonly", values=titles)
        self.hm_sec.grid(row=1, column=1, sticky="w", pady=6); self.hm_sec.current(0)
        ttk.Label(f, text="条目内容（可含 HTML，作为一条 <li>）：").grid(row=2, column=0, sticky="ne", padx=8, pady=6)
        self.hm_item = scrolledtext.ScrolledText(f, width=64, height=4, wrap="word", font=("Microsoft YaHei", 10))
        self.hm_item.grid(row=2, column=1, columnspan=2, sticky="we", pady=6)
        self.hm_pos = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="插到列表开头（默认追加到末尾）", variable=self.hm_pos).grid(row=3, column=1, sticky="w", pady=6)
        ttk.Button(f, text="添加条目", command=self._do_home).grid(row=4, column=1, sticky="w", pady=10)
        self.hm_res = self._st(f, 5); self.hm_res.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(5, weight=1)

    def _do_home(self):
        pos = "start" if self.hm_pos.get() else "end"
        ok, msg = add_home_item(self.hm_sec.get(), self.hm_item.get("1.0", "end").strip(), pos)
        self._show(self.hm_res, ok, msg)

    # 发布
    def _t_publish(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="\U0001F680 发布")
        ttk.Label(f, text="一键发布到 GitHub Pages", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(f, text="把所有改动 git add → commit → push 到远程。约 1-2 分钟后线上网站更新。", foreground="#666").grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        ttk.Label(f, text="提交信息：").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.pb_msg = ttk.Entry(f, width=50)
        self.pb_msg.grid(row=2, column=1, sticky="we", pady=6)
        self.pb_msg.insert(0, "Update site content " + datetime.now().strftime("%Y-%m-%d"))
        ttk.Label(f, text="当前改动：").grid(row=3, column=0, sticky="ne", padx=8, pady=6)
        self.pb_status = self._st(f, 6); self.pb_status.grid(row=3, column=1, sticky="we", pady=6)
        self._refresh_status()
        ttk.Button(f, text="刷新状态", command=self._refresh_status).grid(row=4, column=1, sticky="w", pady=4)
        ttk.Button(f, text="🚀 发布到远程", command=self._do_publish).grid(row=5, column=1, sticky="w", pady=10)
        self.pb_log = self._st(f, 10); self.pb_log.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.rowconfigure(6, weight=1)

    def _refresh_status(self):
        self.pb_status.delete("1.0", "end")
        self.pb_status.insert("1.0", git_status_text())

    def _do_publish(self):
        self.pb_log.delete("1.0", "end")
        msg = self.pb_msg.get().strip() or "Update site content"
        def emit(s):
            self.pb_log.insert("end", s + "\n")
            self.pb_log.see("end")
            self.root.update_idletasks()
        ok, summary = git_publish(msg, callback=emit)
        self._show(self.pb_log, ok, summary)
        self._refresh_status()
        if ok:
            messagebox.showinfo("发布", summary + "\n\n约 1-2 分钟后刷新：https://caichao.github.io/")

    # 帮助
    def _t_help(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="❓ 帮助")
        txt = scrolledtext.ScrolledText(f, wrap="word", font=("Microsoft YaHei", 10))
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        txt.insert("end",
            "个人主页管理器 使用说明\n"
            "========================\n\n"
            "1. 论文：填年份和引文（可含 <em>/<a> 等 HTML），点「添加论文」即插入 publications.html 对应年份最前；"
            f"勾选同步会更新首页 Recent Publications（保留最新 {RECENT_PUB_COUNT} 篇）。\n\n"
            "2. 项目：填标题、描述、配图、详情页文件名（如 earpcg）。会自动在 demo.html 添加卡片，"
            "图片复制到 images/，并可选生成 proj_dirs/earpcg.html 详情页模板。\n\n"
            "3. 照片：多选图片，选已有相册或勾选「新建相册」输入标题。会复制图片到 images/，"
            "更新 albums.txt 并自动调用 build_photos.py 重建 photo.html。\n\n"
            "4. 专利：填标题、类型（如 Singapore patent）、作者、可选配图，插入 patents.html。\n\n"
            "5. 首页条目：选栏目（Research Goals/Students/Teaching 等），填条目内容，追加到对应 <ul>。\n\n"
            "6. 发布：填提交信息，点「🚀 发布到远程」执行 git add→commit→push。\n\n"
            "安全：每次修改 HTML 前自动备份到 .site_backups/ 目录。\n\n"
            "本地预览：点底部「本地预览」按钮在浏览器打开 index.html。\n"
        )
        txt.config(state="disabled")

    # 预览
    def _preview(self):
        webbrowser.open("file:///" + INDEX_FILE.replace("\\", "/"))
        self.status.config(text="已在浏览器打开本地预览。")


def main():
    root = tk.Tk()
    SiteManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()