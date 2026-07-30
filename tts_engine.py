"""
edge-tts 封装:按 (voice, text) 的哈希做缓存,避免重复调用在线接口。
edge-tts 需要联网(调用微软 Edge 的公开接口),但代码本身在本地运行。
"""

import os
import hashlib
import asyncio
import edge_tts


def _cache_path(cache_dir, voice, text):
    key = hashlib.sha256(f"{voice}|{text}".encode("utf-8")).hexdigest()
    return os.path.join(cache_dir, f"{key}.mp3")


async def _synth(voice, text, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def synthesize(voice, text, cache_dir):
    """生成语音文件并返回路径。如果之前已经生成过相同内容,直接复用缓存。"""
    os.makedirs(cache_dir, exist_ok=True)
    out_path = _cache_path(cache_dir, voice, text)
    if not os.path.isfile(out_path):
        asyncio.run(_synth(voice, text, out_path))
    return out_path
