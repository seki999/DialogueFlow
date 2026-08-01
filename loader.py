"""
加载 slides 文件夹里的 NN.md / NN.conversation.<lang> 文件组。

对话文件格式约定(大小写不敏感):
    speaker 1: 这是第一句话
    speaker 2: 这是回应
    speaker 1: 可以换行继续这句话
              这一行仍然算 speaker 1 的内容,直到出现下一个 speaker 标记

编号(NN)决定播放顺序,必须是整数,00.md/00.conversation.zh 都可以,
不要求连续,但每个编号必须有 .md,以及至少一份对话文件(带语言后缀或不带都行)。

多语言对话文件命名: NN.conversation.<lang>,例如:
    01.conversation.zh
    01.conversation.ja
    01.conversation.en
不带语言后缀的 NN.conversation 是"通用兜底文件":对于任何一种语言,
只要没有对应的 NN.conversation.<lang>,就会退回读取 NN.conversation
(用该语言的 TTS 音色朗读这份文本内容,并不会做翻译)。

课程文件夹(slides 根目录下的子文件夹,比如"OCI课程包_对照AWS"):
不限制嵌套多少层,程序会递归扫描 slides 根目录下所有目录,只要某个
目录里直接放着 NN.md,就会被列为一个可选的"课程"(用相对 slides 根
目录的路径表示,比如 "OCI课程包_对照AWS/中文版"),在页面的课程下拉框
里可以直接选到这一层,不需要再额外靠文件夹名猜语言。
"""

import os
import re
import glob

CONV_LINE_RE = re.compile(r'^\s*speaker\s*([12])\s*[:\uFF1A]\s*(.+)$', re.IGNORECASE)

ROOT_COURSE = "."  # 特殊值,代表"课程"就是 slides 根目录本身(自己直接放着 .md 的情况)


def _has_md(path):
    return bool(glob.glob(os.path.join(path, "*.md")))


def list_courses(slides_root):
    """递归扫描 slides_root,返回所有"直接放着 .md"的目录,不限制嵌套深度。
    每一项用相对 slides_root 的路径表示(统一用 "/" 分隔,方便放进 URL
    query 参数),slides_root 自己直接有 .md 的话用 ROOT_COURSE 表示。
    按路径排序返回,ROOT_COURSE(如果存在)排最前面。
    """
    courses = []
    if not os.path.isdir(slides_root):
        return courses

    for dirpath, dirnames, filenames in os.walk(slides_root):
        dirnames.sort()  # 保证遍历顺序稳定,和最终排序无关但方便调试
        if any(name.endswith(".md") for name in filenames):
            rel = os.path.relpath(dirpath, slides_root)
            courses.append(ROOT_COURSE if rel == "." else rel.replace(os.sep, "/"))

    courses.sort(key=lambda c: (c != ROOT_COURSE, c))
    return courses


def resolve_course_dir(slides_root, course):
    """把课程标识(list_courses() 返回的相对路径)解析成绝对目录;
    course 已经是具体到"直接放着 NN.md"的那一层了,不需要再猜语言子文件夹。
    找不到或者目录下确实没有 .md 时返回 None。
    """
    if course == ROOT_COURSE:
        path = slides_root
    else:
        path = os.path.join(slides_root, *course.split("/"))
    return path if os.path.isdir(path) and _has_md(path) else None


LEAF = "__LEAF__"  # 标记这一层目录本身直接放着 NN.md,可以直接选中,不用再往下一级


def build_course_tree(slides_root):
    """把 slides_root 下的目录结构变成嵌套字典,给前端做多级级联下拉框用。
    每一层的 key 是文件夹名,value 要么是 LEAF(这一层直接放着 NN.md,
    可以在这一级直接选中),要么是下一层的字典(还有子文件夹)。
    如果 slides_root 自己直接放着 .md,整棵树就是 LEAF 本身(不需要下拉框)。
    """
    def _walk(path):
        if _has_md(path):
            return LEAF
        node = {}
        if not os.path.isdir(path):
            return node
        for name in sorted(os.listdir(path)):
            sub = os.path.join(path, name)
            if os.path.isdir(sub):
                child = _walk(sub)
                if child:  # 空字典(该子树完全没有 .md)就不收进去
                    node[name] = child
        return node

    return _walk(slides_root)


def default_course(courses, hint):
    """从 list_courses() 的结果里挑默认选中项:优先选路径第一层等于 hint 的,
    找不到就退回第一个;courses 为空时返回 None。"""
    if not courses:
        return None
    for c in courses:
        if c == ROOT_COURSE:
            continue
        if c.split("/")[0] == hint:
            return c
    return courses[0]


def load_slide_pairs(slides_dir, languages):
    """
    languages: 支持的语言代码列表,例如 ["zh", "ja", "en"]
    返回的每个 slide 里 segments_by_lang 覆盖 languages 里的每一种语言:
    优先用 NN.conversation.<lang>,没有的话退回不带后缀的 NN.conversation。
    只有两者都不存在时,该语言才会缺失(调用方需要自行处理缺失情况)。
    """
    md_files = glob.glob(os.path.join(slides_dir, "*.md"))
    pairs = []

    for md_path in md_files:
        base = os.path.splitext(os.path.basename(md_path))[0]

        try:
            index = int(base)
        except ValueError:
            print(f"[警告] 文件名 '{base}' 不是数字编号,跳过")
            continue

        fallback_path = os.path.join(slides_dir, f"{base}.conversation")
        fallback_segments = None
        if os.path.isfile(fallback_path):
            fallback_segments = parse_conversation(fallback_path)
            if not fallback_segments:
                print(f"[警告] 对话文件解析为空: {fallback_path}")
                fallback_segments = None

        segments_by_lang = {}
        for lang in languages:
            conv_path = os.path.join(slides_dir, f"{base}.conversation.{lang}")
            if os.path.isfile(conv_path):
                segments = parse_conversation(conv_path)
                if segments:
                    segments_by_lang[lang] = segments
                else:
                    print(f"[警告] 对话文件解析为空,跳过: {conv_path}")
            elif fallback_segments is not None:
                # 没有该语言专属文件,退回用不带后缀的通用文件朗读
                segments_by_lang[lang] = fallback_segments

        if not segments_by_lang:
            print(f"[警告] 缺少任何对话文件,跳过: {md_path}")
            continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        pairs.append({
            "index": index,
            "md_path": md_path,
            "md_text": md_text,
            "segments_by_lang": segments_by_lang,
        })

    pairs.sort(key=lambda p: p["index"])

    if not pairs:
        raise RuntimeError(f"在 {slides_dir} 中没有找到任何有效的 md/conversation 文件组")

    return pairs


def parse_conversation(conv_path):
    segments = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker is not None:
            text = " ".join(current_lines).strip()
            if text:
                segments.append((current_speaker, text))

    with open(conv_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            m = CONV_LINE_RE.match(line)
            if m:
                flush()
                current_speaker = m.group(1)
                current_lines = [m.group(2).strip()]
            else:
                if current_speaker is not None:
                    current_lines.append(line.strip())
        flush()

    return segments
