"""
录屏封装,支持 Windows 和 macOS。

录制整个屏幕 + 系统音频。录制"整个浏览器窗口"在两个平台上都不够稳定
(标题匹配、DPI 缩放、窗口被遮挡都会出问题),所以统一录制整个桌面 ——
使用前请把浏览器窗口最大化 / 按 F11 全屏,效果等同。

Windows 前提条件:
  1. ffmpeg 已安装并加入系统 PATH(命令行输入 ffmpeg -version 能看到版本号)
  2. 已启用一个可以采集"系统播放声音"的录音设备(如 立体声混音 / VB-Cable),
     并把设备名填入 config.py 的 FFMPEG_AUDIO_DEVICE
  这部分未经过 Windows 实机验证,如果 dshow 设备名或 gdigrab 参数报错,
  请先运行: ffmpeg -list_devices true -f dshow -i dummy
  确认设备名称拼写是否完全一致(包括括号里的厂商信息)。

macOS 前提条件:
  1. ffmpeg 已安装(推荐 brew install ffmpeg)
  2. 已安装一个能采集"系统播放声音"的虚拟声卡(如 BlackHole 2ch,免费),
     macOS 没有类似 Windows 立体声混音的内置方案,必须装虚拟声卡才能
     让 ffmpeg 采集到 TTS 播放出来的声音
  3. 把屏幕/音频设备索引填入 config.py 的 FFMPEG_AVFOUNDATION_DEVICE,
     格式为 "视频设备索引:音频设备索引",获取方法:
       ffmpeg -f avfoundation -list_devices true -i ""
  4. 第一次运行时,系统会弹窗要求给终端 / Python 授予"屏幕录制"权限
     (系统设置 -> 隐私与安全性 -> 屏幕录制),授权后可能需要重启终端
  这部分未经过 macOS 实机验证,如果设备索引或权限报错,请先按上面的
  list_devices 命令确认索引号。
"""

import os
import sys
import subprocess

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"


class ScreenRecorder:
    def __init__(self, output_path, audio_device=None, framerate=30, avfoundation_device=None):
        self.output_path = output_path
        self.audio_device = audio_device
        self.avfoundation_device = avfoundation_device
        self.framerate = framerate
        self.process = None

    def _build_cmd(self):
        if IS_MACOS:
            if not self.avfoundation_device:
                raise RuntimeError(
                    "请先在 config.py 里设置 FFMPEG_AVFOUNDATION_DEVICE"
                    "(运行 `ffmpeg -f avfoundation -list_devices true -i \"\"` 查看索引)"
                )
            return [
                "ffmpeg", "-y",
                "-f", "avfoundation",
                "-framerate", str(self.framerate),
                "-i", self.avfoundation_device,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-c:a", "aac",
                self.output_path,
            ]
        # 默认按 Windows 处理
        return [
            "ffmpeg", "-y",
            "-f", "gdigrab",
            "-framerate", str(self.framerate),
            "-i", "desktop",
            "-f", "dshow",
            "-thread_queue_size", "1024",
            "-i", f"audio={self.audio_device}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-c:a", "aac",
            self.output_path,
        ]

    def start(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        cmd = self._build_cmd()
        print("[录屏] 启动 ffmpeg:")
        print("  " + " ".join(cmd))

        popen_kwargs = {}
        if IS_WINDOWS:
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **popen_kwargs,
        )

    def stop(self):
        if self.process is None:
            return
        try:
            # ffmpeg 在收到标准输入的 'q' 时会正常结束并把文件写完整,
            # 这是让输出文件不损坏的正确停止方式(直接 kill 进程可能导致文件损坏)。
            self.process.communicate(input=b"q", timeout=20)
        except Exception as e:
            print(f"[录屏] 正常停止失败({e}),尝试强制结束进程")
            self.process.kill()
            self.process.wait(timeout=10)
        finally:
            print(f"[录屏] 已停止,文件保存在: {self.output_path}")
            self.process = None
