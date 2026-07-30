"""
Windows 专用的 ffmpeg 录屏封装。

录制整个屏幕(gdigrab) + 系统音频(dshow)。
录制"整个浏览器窗口"在 Windows 上用 ffmpeg 精确抓取单一窗口并不稳定
(标题匹配、DPI 缩放、窗口被遮挡都会出问题),所以这里改为录制整个
桌面 —— 使用前请把浏览器窗口最大化 / 按 F11 全屏,效果等同。

前提条件:
  1. ffmpeg 已安装并加入系统 PATH(命令行输入 ffmpeg -version 能看到版本号)
  2. 已启用一个可以采集"系统播放声音"的录音设备(如 立体声混音 / VB-Cable),
     并把设备名填入 config.py 的 FFMPEG_AUDIO_DEVICE

这部分未经过 Windows 实机验证,如果 dshow 设备名或 gdigrab 参数报错,
请先运行:
    ffmpeg -list_devices true -f dshow -i dummy
确认设备名称拼写是否完全一致(包括括号里的厂商信息)。
"""

import os
import subprocess


class ScreenRecorder:
    def __init__(self, output_path, audio_device, framerate=30):
        self.output_path = output_path
        self.audio_device = audio_device
        self.framerate = framerate
        self.process = None
        self.log_path = os.path.splitext(output_path)[0] + "_log.txt"
        self._log_file = None

    def start(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
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
        print("[录屏] 启动 ffmpeg:")
        print("  " + " ".join(cmd))
        print(f"[录屏] ffmpeg 完整日志会写到: {self.log_path}")

        # 把 ffmpeg 的输出(包括音频设备打开失败之类的警告)写到日志文件,
        # 方便事后排查"有没有声音"这类问题。
        self._log_file = open(self.log_path, "w", encoding="utf-8", errors="replace")
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
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
            if self._log_file:
                self._log_file.close()
                self._log_file = None
            print(f"[录屏] 已停止,文件保存在: {self.output_path}")
            print(f"[录屏] 如果没有声音,先看一下日志: {self.log_path}")
            self.process = None
