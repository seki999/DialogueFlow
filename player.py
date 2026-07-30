"""
用 pygame.mixer 播放 mp3,阻塞直到播放完成(方便主流程按顺序推进)。
"""

import time
import pygame

_inited = False


def _ensure_init():
    global _inited
    if not _inited:
        pygame.mixer.init()
        _inited = True


def play_blocking(path):
    _ensure_init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
