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
"""

import os
import re
import glob

CONV_LINE_RE = re.compile(r'^\s*speaker\s*([12])\s*[:\uFF1A]\s*(.+)$', re.IGNORECASE)


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
