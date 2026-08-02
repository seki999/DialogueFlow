"""
用 pygame.mixer 播放 mp3,阻塞直到播放完成(方便主流程按顺序推进)。
可选传入 control(PlaybackControl 实例)支持运行中暂停/停止。
"""

import time
import pygame

_inited = False


def _ensure_init():
    global _inited
    if not _inited:
        pygame.mixer.init()
        _inited = True


def play_blocking(path, control=None):
    _ensure_init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    paused = False
    while True:
        if control and control.is_stop_requested():
            pygame.mixer.music.stop()
            return

        if control and control.is_paused():
            if not paused:
                pygame.mixer.music.pause()
                paused = True
            time.sleep(0.1)
            continue

        if paused:
            pygame.mixer.music.unpause()
            paused = False

        if not pygame.mixer.music.get_busy():
            return
        time.sleep(0.1)
