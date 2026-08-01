import re
import threading
import markdown as md_lib
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

import config
from control import PlaybackControl
from loader import list_courses, resolve_course_dir, load_slide_pairs

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
DETAILS_TAG_RE = re.compile(r"<details(?![^>]*\bmarkdown=)")
TASK_ITEM_RE = re.compile(r"<li>\[([ xX])\]\s*(.*?)</li>", re.DOTALL)


def _task_item(match):
    checked = " checked" if match.group(1).lower() == "x" else ""
    content = match.group(2)
    return f'<li class="task-item"><label><input type="checkbox"{checked}> {content}</label></li>'


def render_md_to_html(md_text):
    """把 markdown 转成 html,mermaid 代码块单独处理,转成 <pre class="mermaid">
    交给前端 mermaid.js 渲染成流程图。
    另外两点处理:
    1. 给没有显式声明的 <details> 自动加上 markdown="1"(配合 md_in_html 扩展),
       否则 <details> 内部的 markdown(加粗、列表、行内代码等)不会被转换,
       只会原样输出成文字。
    2. 把 "- [ ] 选项" 这种任务列表语法转成真正可勾选的 <input type="checkbox">,
       markdown 库本身只会把它转成字面的 "[ ] 选项" 文字。
    """
    md_text = DETAILS_TAG_RE.sub('<details markdown="1"', md_text)

    blocks = []

    def _stash(match):
        blocks.append(match.group(1))
        return f"@@MERMAID_BLOCK_{len(blocks) - 1}@@"

    stashed = MERMAID_BLOCK_RE.sub(_stash, md_text)
    html = md_lib.markdown(stashed, extensions=["fenced_code", "tables", "md_in_html"])

    for i, code in enumerate(blocks):
        placeholder = f"@@MERMAID_BLOCK_{i}@@"
        mermaid_html = f'<pre class="mermaid">{code}</pre>'
        # markdown 转换器常把独立占一行的文本包进 <p> 标签,这里两种情况都替换掉
        html = html.replace(f"<p>{placeholder}</p>", mermaid_html)
        html = html.replace(placeholder, mermaid_html)

    html = TASK_ITEM_RE.sub(_task_item, html)

    return html


class SessionEmitter:
    """每次点击"开始"都会创建一个新实例,绑定这一次运行实际用到的
    slides/rendered_slides(取决于选中的课程+语言),避免多次运行之间
    互相影响,也让课程/语言可以在每次运行时独立选择,不需要在服务启动时
    写死。"""

    def __init__(self, socketio, slides, rendered_slides):
        self.socketio = socketio
        self.slides = slides
        self.rendered_slides = rendered_slides

    def show_slide(self, slide_pos, progress_current, progress_total):
        self.socketio.emit("show_slide", {
            "html": self.rendered_slides[slide_pos],
            "index": self.slides[slide_pos]["index"],
            "progress_current": progress_current,
            "progress_total": progress_total,
        })

    def show_done(self):
        self.socketio.emit("all_done", {})

    def show_stopped(self):
        self.socketio.emit("stopped", {})

    def show_caption(self, lang, speaker, text):
        # text 为空字符串时表示清空字幕(切换 slide / 全部播完时用)
        label = config.SPEAKER_LABELS.get(lang, {}).get(speaker, "")
        self.socketio.emit("show_caption", {"speaker": speaker, "text": text, "label": label})


def _load_course(slides_root, course):
    """按课程标识解析出实际目录并加载 slides,失败返回 (None, None, 错误信息)。"""
    course_dir = resolve_course_dir(slides_root, course)
    if course_dir is None:
        return None, None, f"课程 '{course}' 下没有找到任何有效的 .md 素材"
    try:
        slides = load_slide_pairs(course_dir, list(config.LANGUAGES.keys()))
    except RuntimeError as e:
        return None, None, str(e)
    return slides, course_dir, None


def create_app(slides_root, on_start):
    """
    slides_root: slides 根目录,里面可以直接放 NN.md,也可以嵌套任意层
                 子文件夹,每个"直接放着 NN.md"的目录都会被列为一个课程
    on_start: 点击"开始"后要执行的函数
              (参数为 emitter, slides, lang, rate, volume, pitch,
               start_index, end_index, mode, control),
              会在后台线程运行,避免阻塞 Flask 的请求处理线程。
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "local-only-secret"
    socketio = SocketIO(app, cors_allowed_origins="*")

    @app.route("/")
    def index():
        courses = list_courses(slides_root)
        if not courses:
            return (
                f"在 {slides_root} 目录下没有找到任何有效的课程文件夹或素材,"
                "请检查 slides 目录结构。",
                500,
            )

        course = request.args.get("course") or courses[0]
        if course not in courses:
            course = courses[0]

        # 课程标识已经具体到叶子目录了,预览页不需要再按语言重新解析
        slides, _course_dir, error = _load_course(slides_root, course)
        if error:
            return f"加载课程 '{course}' 失败: {error}", 500

        rendered_slides = [render_md_to_html(s["md_text"]) for s in slides]
        slide_indices = [s["index"] for s in slides]

        return render_template(
            "index.html",
            courses=courses,
            selected_course=course,
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
            min_index=min(slide_indices),
            max_index=max(slide_indices),
            playback_modes=config.PLAYBACK_MODES,
            default_mode=config.DEFAULT_MODE,
        )

    @app.route("/api/start", methods=["POST"])
    def api_start():
        data = request.get_json(silent=True) or {}

        courses = list_courses(slides_root)
        if not courses:
            return jsonify({"status": "error", "message": "没有可用的课程"}), 400
        course = data.get("course")
        if course not in courses:
            course = courses[0]

        lang = data.get("lang")
        if lang not in config.LANGUAGES:
            lang = config.DEFAULT_LANGUAGE

        slides, course_dir, error = _load_course(slides_root, course)
        if error:
            return jsonify({"status": "error", "message": error}), 400

        rendered_slides = [render_md_to_html(s["md_text"]) for s in slides]
        slide_indices = [s["index"] for s in slides]
        min_index, max_index = min(slide_indices), max(slide_indices)

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

        mode = data.get("mode")
        if mode not in config.PLAYBACK_MODES:
            mode = config.DEFAULT_MODE

        control = PlaybackControl()
        app.current_control = control  # 供 /api/pause /api/stop 操作当前这次运行

        emitter = SessionEmitter(socketio, slides, rendered_slides)

        threading.Thread(
            target=on_start,
            args=(emitter, slides, lang, rate, volume, pitch, start_index, end_index, mode, control),
            daemon=True,
        ).start()
        return jsonify({
            "status": "started", "course": course, "course_dir": course_dir, "lang": lang,
            "rate": rate, "volume": volume, "pitch": pitch,
            "start_index": start_index, "end_index": end_index, "mode": mode,
        })

    @app.route("/api/pause", methods=["POST"])
    def api_pause():
        control = getattr(app, "current_control", None)
        if control is None or control.is_stop_requested():
            return jsonify({"status": "no_active_session"}), 400
        control.toggle_pause()
        return jsonify({"status": "paused" if control.is_paused() else "resumed"})

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        control = getattr(app, "current_control", None)
        if control is None:
            return jsonify({"status": "no_active_session"}), 400
        control.request_stop()
        return jsonify({"status": "stop_requested"})

    return app, socketio
