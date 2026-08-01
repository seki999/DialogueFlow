import os
import time
import webbrowser
from datetime import datetime

import config
from loader import list_courses
from tts_engine import synthesize
from player import play_blocking
from recorder import ScreenRecorder
from server import create_app


def _fmt_pct(value):
    return f"{value:+d}%"


def _fmt_hz(value):
    return f"{value:+d}Hz"


def run_playback_and_recording(emitter, slides, lang, rate, volume, pitch, start_index, end_index, mode, control):
    """点击"开始"后执行的完整流程:
    (录屏模式下先开始录屏 ->) 依次显示每组 md 并播放选中语言的对应对话 ->
    全部结束后(录屏模式下停止录屏)。
    每次录屏都会生成一个带时间戳的新文件名,方便反复录制、互不覆盖。
    emitter: server.SessionEmitter 实例,这次运行绑定的具体课程/语言对应的
    slides 已经加载好了,通过它把画面/字幕/进度推送到浏览器。
    rate/volume/pitch: 页面滑块传来的整数值(百分比/Hz),这里统一转换成
    edge-tts 需要的字符串格式,例如 10 -> "+10%"。
    start_index/end_index: 只播放/录制编号在 [start_index, end_index] 区间内的章节
    (闭区间,单章节时 start_index == end_index)。
    mode: "play_record"(播放并录屏)或 "play_only"(只播放,不启动 ffmpeg)。
    control: PlaybackControl 实例,用于响应运行中的暂停/继续/停止请求。
    注意:暂停只会暂停语音播放和翻页节奏,如果是"播放并录屏"模式,
    ffmpeg 录屏进程本身不会跟着暂停,画面会停在暂停那一刻直到继续。
    """
    selected = [
        (pos, slide) for pos, slide in enumerate(slides)
        if start_index <= slide["index"] <= end_index
    ]
    if not selected:
        print(f"[警告] 编号区间 [{start_index}, {end_index}] 内没有任何章节,已取消")
        return

    range_tag = f"{start_index}-{end_index}" if start_index != end_index else f"{start_index}"

    recorder = None
    if mode == "play_record":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            config.OUTPUT_DIR,
            f"{config.OUTPUT_FILENAME_PREFIX}_{lang}_ch{range_tag}_{timestamp}.mp4",
        )
        recorder = ScreenRecorder(
            output_path=output_path,
            audio_device=config.FFMPEG_AUDIO_DEVICE,
            framerate=config.FFMPEG_FRAMERATE,
            avfoundation_device=config.FFMPEG_AVFOUNDATION_DEVICE,
        )

    voice_map = config.VOICE_MAP[lang]
    rate_str = _fmt_pct(rate)
    volume_str = _fmt_pct(volume)
    pitch_str = _fmt_hz(pitch)

    mode_label = config.PLAYBACK_MODES.get(mode, mode)
    action = "开始录制" if recorder else "开始播放"
    print(
        f"[提示] 模式: {mode_label} / 语言: {config.LANGUAGES[lang]} ({lang})"
        f" / 语速 {rate_str} / 音量 {volume_str} / 音高 {pitch_str}"
        f" / 章节 {range_tag}(共 {len(selected)} 组)"
        f",3 秒后{action},请确认浏览器已经全屏..."
    )
    time.sleep(3)

    if control.is_stop_requested():
        return

    if recorder:
        recorder.start()
        time.sleep(1.5)  # 给 ffmpeg 一点启动时间,避免录到的视频开头缺帧

    try:
        for i, (pos, slide) in enumerate(selected, start=1):
            if control.is_stop_requested():
                break

            segments = slide["segments_by_lang"].get(lang)
            emitter.show_slide(pos, i, len(selected))
            emitter.show_caption(lang, "", "")  # 切换到新一组时先清空上一组残留的字幕
            print(f"[播放] 第 {slide['index']} 组 ({os.path.basename(slide['md_path'])})")
            control.sleep(config.SLIDE_SWITCH_DELAY)

            if control.is_stop_requested():
                break

            if segments is None:
                print(f"  [警告] 第 {slide['index']} 组没有 {lang} 语言的对话文件,跳过语音/字幕")
                continue

            for speaker, text in segments:
                if control.is_stop_requested():
                    break
                voice = voice_map.get(speaker)
                if voice is None:
                    print(f"  [警告] 未知 speaker '{speaker}',跳过: {text}")
                    continue
                emitter.show_caption(lang, speaker, text)  # 先显示这句字幕
                audio_path = synthesize(
                    voice, text, config.TTS_CACHE_DIR,
                    rate=rate_str, volume=volume_str, pitch=pitch_str,
                )
                play_blocking(audio_path, control)

        if control.is_stop_requested():
            print("[提示] 已手动停止")
            emitter.show_stopped()
        else:
            emitter.show_done()
        emitter.show_caption(lang, "", "")  # 结束时清空字幕
        control.sleep(1.5)
    finally:
        if recorder:
            recorder.stop()


def main():
    courses = list_courses(config.SLIDES_DIR)
    if not courses:
        print(f"[错误] 在 {config.SLIDES_DIR} 目录下没有找到任何有效的课程文件夹或素材")
        return
    print(f"[加载] 在 {config.SLIDES_DIR} 下找到 {len(courses)} 个课程:")
    for c in courses:
        label = "(根目录)" if c == "." else c
        print(f"  - {label}")
    print("[提示] 具体每个课程有多少章节,会在浏览器里选好课程/语言后显示")

    def on_start(emitter, slides, lang, rate, volume, pitch, start_index, end_index, mode, control):
        run_playback_and_recording(
            emitter, slides, lang, rate, volume, pitch, start_index, end_index, mode, control
        )

    app, socketio = create_app(config.SLIDES_DIR, on_start)

    url = f"http://{config.WEB_HOST}:{config.WEB_PORT}/"
    webbrowser.open(url)

    print(f"[启动] 本地服务已启动: {url}")
    print("[启动] 请在浏览器里选好课程/模式/语言/章节后点击开始")
    socketio.run(app, host=config.WEB_HOST, port=config.WEB_PORT)


if __name__ == "__main__":
    main()
