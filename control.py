"""
播放控制:一次"开始"会创建一个 PlaybackControl 实例,
在后台播放线程和 Flask 的 /api/pause /api/stop 之间共享,
用来实现运行中的暂停/继续/停止。
"""

import time
import threading


class PlaybackControl:
    def __init__(self):
        self._pause_event = threading.Event()  # 置位 = 暂停中
        self._stop_event = threading.Event()   # 置位 = 已请求停止

    def pause(self):
        self._pause_event.set()

    def resume(self):
        self._pause_event.clear()

    def toggle_pause(self):
        if self._pause_event.is_set():
            self.resume()
        else:
            self.pause()

    def request_stop(self):
        self._stop_event.set()
        self._pause_event.clear()  # 避免线程卡在暂停等待里退不出来

    def is_paused(self):
        return self._pause_event.is_set()

    def is_stop_requested(self):
        return self._stop_event.is_set()

    def sleep(self, seconds):
        """可被暂停/停止打断的 sleep:暂停时不消耗剩余等待时间,
        停止时立即返回。"""
        remaining = seconds
        while remaining > 0:
            if self._stop_event.is_set():
                return
            if self._pause_event.is_set():
                time.sleep(0.1)
                continue
            step = min(0.1, remaining)
            time.sleep(step)
            remaining -= step
