"""
加载 slides 文件夹里的 NN.md / NN.conversation 文件对。

对话文件格式约定(大小写不敏感):
    speaker 1: 这是第一句话
    speaker 2: 这是回应
    speaker 1: 可以换行继续这句话
              这一行仍然算 speaker 1 的内容,直到出现下一个 speaker 标记

编号(NN)决定播放顺序,必须是整数,00.md/00.conversation 都可以,
不要求连续,但同一个编号必须同时存在 .md 和 .conversation 两个文件。
"""

import os
import re
import glob

CONV_LINE_RE = re.compile(r'^\s*speaker\s*([12])\s*[:\uFF1A]\s*(.+)$', re.IGNORECASE)


def load_slide_pairs(slides_dir):
    md_files = glob.glob(os.path.join(slides_dir, "*.md"))
    pairs = []

    for md_path in md_files:
        base = os.path.splitext(os.path.basename(md_path))[0]
        conv_path = os.path.join(slides_dir, f"{base}.conversation")

        if not os.path.isfile(conv_path):
            print(f"[警告] 缺少对应的对话文件,跳过: {md_path}")
            continue

        try:
            index = int(base)
        except ValueError:
            print(f"[警告] 文件名 '{base}' 不是数字编号,跳过")
            continue

        segments = parse_conversation(conv_path)
        if not segments:
            print(f"[警告] 对话文件解析为空,跳过: {conv_path}")
            continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        pairs.append({
            "index": index,
            "md_path": md_path,
            "md_text": md_text,
            "segments": segments,
        })

    pairs.sort(key=lambda p: p["index"])

    if not pairs:
        raise RuntimeError(f"在 {slides_dir} 中没有找到任何有效的 md/conversation 文件对")

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
