import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 素材文件夹路径(存放 01.md / 01.conversation, 02.md / 02.conversation ...)
SLIDES_DIR = os.path.join(BASE_DIR, "slides")

# 输出视频路径(实际文件名会在运行时加上时间戳,支持反复录制不覆盖)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILENAME_PREFIX = "lesson_video"

# TTS 缓存目录(生成过的语音会缓存在这里,避免重复调用 edge-tts)
TTS_CACHE_DIR = os.path.join(BASE_DIR, "tts_cache")

# 支持的语言(代码 -> 页面上显示的名称),顺序即页面选项顺序
LANGUAGES = {
    "zh": "汉语",
    "ja": "日语",
    "en": "英语",
}
DEFAULT_LANGUAGE = "zh"

# 字幕里说话人标签的多语言文案
SPEAKER_LABELS = {
    "zh": {"1": "说话人 1", "2": "说话人 2"},
    "ja": {"1": "話者 1", "2": "話者 2"},
    "en": {"1": "Speaker 1", "2": "Speaker 2"},
}

# speaker 编号 -> edge-tts voice 名称的映射,按语言分开
# speaker 1 = 女声, speaker 2 = 男声(固定映射)
VOICE_MAP = {
    "zh": {
        "1": "zh-CN-XiaoxiaoNeural",  # 女声
        "2": "zh-CN-YunxiNeural",     # 男声
    },
    "ja": {
        "1": "ja-JP-NanamiNeural",    # 女声
        "2": "ja-JP-KeitaNeural",     # 男声
    },
    "en": {
        "1": "en-US-JennyNeural",     # 女声
        "2": "en-US-GuyNeural",       # 男声
    },
}

# 本地 Web 服务
WEB_HOST = "127.0.0.1"
WEB_PORT = 5000

# ==== ffmpeg 录屏配置 ====
# --- Windows(gdigrab + dshow) ---
# 音频设备名称必须替换成你机器上实际的名称。
# 获取方法(在命令行运行):
#   ffmpeg -list_devices true -f dshow -i dummy
# 输出里 "DirectShow audio devices" 下面列出的名字就是可用值,例如:
#   "立体声混音 (Realtek High Definition Audio)"
#   "CABLE Output (VB-Audio Virtual Cable)"
FFMPEG_AUDIO_DEVICE = "virtual-audio-capturer"

# --- macOS(avfoundation) ---
# 格式为 "视频设备索引:音频设备索引",获取方法(在终端运行):
#   ffmpeg -f avfoundation -list_devices true -i ""
# 视频设备通常是 "Capture screen 0" 之类,索引示例见输出列表;
# 音频设备必须是虚拟声卡(如 BlackHole 2ch)才能采集到系统播放的声音,
# 选普通麦克风是录不到 TTS 播放出来的声音的。
FFMPEG_AVFOUNDATION_DEVICE = "1:0"  # 请替换成你机器上实际的索引组合

FFMPEG_FRAMERATE = 30

# 每组 md 展示前,播放该组语音前的停顿(秒),给浏览器渲染留出时间
SLIDE_SWITCH_DELAY = 0.5
