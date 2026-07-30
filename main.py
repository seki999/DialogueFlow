import os
import time
import webbrowser
from datetime import datetime

import config
from loader import load_slide_pairs
from tts_engine import synthesize
from player import play_blocking
from recorder import ScreenRecorder
from server import create_app


def run_playback_and_recording(app, slides):
    """点击"开始录制"后执行的完整流程:
    开始录屏 -> 依次显示每组 md 并播放对应对话 -> 全部结束后停止录屏。
    每次调用都会生成一个带时间戳的新文件名,方便反复录制、互不覆盖。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        config.OUTPUT_DIR, f"{config.OUTPUT_FILENAME_PREFIX}_{timestamp}.mp4"
    )

    recorder = ScreenRecorder(
        output_path=output_path,
        audio_device=config.FFMPEG_AUDIO_DEVICE,
        framerate=config.FFMPEG_FRAMERATE,
    )

    print("[提示] 3 秒后开始录制,请确认浏览器已经全屏...")
    time.sleep(3)

    recorder.start()
    time.sleep(1.5)  # 给 ffmpeg 一点启动时间,避免录到的视频开头缺帧

    try:
        for pos, slide in enumerate(slides):
            app.show_slide(pos)
            print(f"[播放] 第 {slide['index']} 组 ({os.path.basename(slide['md_path'])})")
            time.sleep(config.SLIDE_SWITCH_DELAY)

            for speaker, text in slide["segments"]:
                voice = config.VOICE_MAP.get(speaker)
                if voice is None:
                    print(f"  [警告] 未知 speaker '{speaker}',跳过: {text}")
                    continue
                audio_path = synthesize(voice, text, config.TTS_CACHE_DIR)
                play_blocking(audio_path)

        app.show_done()
        time.sleep(1.5)
    finally:
        recorder.stop()


def main():
    slides = load_slide_pairs(config.SLIDES_DIR)
    print(f"[加载] 共找到 {len(slides)} 组素材:")
    for s in slides:
        print(f"  - 第 {s['index']} 组: {os.path.basename(s['md_path'])} / {len(s['segments'])} 句对话")

    def on_start():
        run_playback_and_recording(app, slides)

    app, socketio = create_app(slides, on_start)

    url = f"http://{config.WEB_HOST}:{config.WEB_PORT}/"
    webbrowser.open(url)

    print(f"[启动] 本地服务已启动: {url}")
    print("[启动] 请在浏览器里确认素材一览,全屏后点击'开始录制'")
    socketio.run(app, host=config.WEB_HOST, port=config.WEB_PORT)


if __name__ == "__main__":
    main()
