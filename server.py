import re
import threading
import markdown as md_lib
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

import config

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def render_md_to_html(md_text):
    """把 markdown 转成 html,mermaid 代码块单独处理,转成 <pre class="mermaid">
    交给前端 mermaid.js 渲染成流程图。"""
    blocks = []

    def _stash(match):
        blocks.append(match.group(1))
        return f"@@MERMAID_BLOCK_{len(blocks) - 1}@@"

    stashed = MERMAID_BLOCK_RE.sub(_stash, md_text)
    html = md_lib.markdown(stashed, extensions=["fenced_code", "tables"])

    for i, code in enumerate(blocks):
        placeholder = f"@@MERMAID_BLOCK_{i}@@"
        mermaid_html = f'<pre class="mermaid">{code}</pre>'
        # markdown 转换器常把独立占一行的文本包进 <p> 标签,这里两种情况都替换掉
        html = html.replace(f"<p>{placeholder}</p>", mermaid_html)
        html = html.replace(placeholder, mermaid_html)

    return html


def create_app(slides, on_start):
    """
    slides: loader.load_slide_pairs() 返回的已排序列表
    on_start: 点击"开始录制"后要执行的函数(参数为选中的语言代码,如 "zh"),
              会在后台线程运行,避免阻塞 Flask 的请求处理线程。
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "local-only-secret"
    socketio = SocketIO(app, cors_allowed_origins="*")

    rendered_slides = [render_md_to_html(s["md_text"]) for s in slides]
    slide_indices = [s["index"] for s in slides]  # 排序后的实际章节编号列表(可能不连续)
    min_index = min(slide_indices)
    max_index = max(slide_indices)

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            slides_preview=[
                {"index": s["index"], "html": rendered_slides[i]}
                for i, s in enumerate(slides)
            ],
            languages=config.LANGUAGES,
            default_language=config.DEFAULT_LANGUAGE,
            rate_default=config.TTS_RATE_DEFAULT,
            rate_range=config.TTS_RATE_RANGE,
            volume_default=config.TTS_VOLUME_DEFAULT,
            volume_range=config.TTS_VOLUME_RANGE,
            pitch_default=config.TTS_PITCH_DEFAULT,
            pitch_range=config.TTS_PITCH_RANGE,
            slide_indices=slide_indices,
            min_index=min_index,
            max_index=max_index,
        )

    @app.route("/api/start", methods=["POST"])
    def api_start():
        data = request.get_json(silent=True) or {}
        lang = data.get("lang")
        if lang not in config.LANGUAGES:
            lang = config.DEFAULT_LANGUAGE

        def _clamp_int(value, default, value_range):
            try:
                value = int(value)
            except (TypeError, ValueError):
                return default
            lo, hi = value_range
            return max(lo, min(hi, value))

        rate = _clamp_int(data.get("rate"), config.TTS_RATE_DEFAULT, config.TTS_RATE_RANGE)
        volume = _clamp_int(data.get("volume"), config.TTS_VOLUME_DEFAULT, config.TTS_VOLUME_RANGE)
        pitch = _clamp_int(data.get("pitch"), config.TTS_PITCH_DEFAULT, config.TTS_PITCH_RANGE)

        start_index = _clamp_int(data.get("start_index"), min_index, (min_index, max_index))
        end_index = _clamp_int(data.get("end_index"), max_index, (min_index, max_index))
        if start_index > end_index:
            start_index, end_index = end_index, start_index

        threading.Thread(
            target=on_start,
            args=(lang, rate, volume, pitch, start_index, end_index),
            daemon=True,
        ).start()
        return jsonify({
            "status": "started", "lang": lang, "rate": rate, "volume": volume,
            "pitch": pitch, "start_index": start_index, "end_index": end_index,
        })

    def show_slide(slide_pos):
        socketio.emit("show_slide", {
            "html": rendered_slides[slide_pos],
            "index": slides[slide_pos]["index"],
            "total": len(slides),
        })

    def show_done():
        socketio.emit("all_done", {})

    def show_caption(lang, speaker, text):
        # text 为空字符串时表示清空字幕(切换 slide / 全部播完时用)
        label = config.SPEAKER_LABELS.get(lang, {}).get(speaker, "")
        socketio.emit("show_caption", {"speaker": speaker, "text": text, "label": label})

    # 把回调方法挂在 app 上,方便 main.py 里直接调用
    app.show_slide = show_slide
    app.show_done = show_done
    app.show_caption = show_caption

    return app, socketio
