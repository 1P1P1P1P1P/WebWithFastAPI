# -*- coding = utf-8 -*-
# @Author : VV1P1n
# @time : 2024/4/26 : 13:23

"""
bilibili音频获取模块
"""
import asyncio
import json
import random
import re
import aiohttp
import requests
from datetime import datetime

from models.music import AudioBilibili, AudioBilibiliList

header = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
}


class BilibiliClient:
    def __init__(self):
        self.session = requests.Session()
        self.cookie_jar = aiohttp.CookieJar(unsafe=True)

    async def get_audio_url(self, bvid: str):
        audio_list = AudioBilibiliList()
        try:
            first_audio, pages = await self._try_to_get_audio_url(bvid)
            audio_list.list.append(first_audio)
            if pages > 1:
                tasks = [self._try_to_get_audio_url(bvid, i) for i in range(2, pages + 1)]
                futures = await asyncio.gather(*tasks)
                audio_list.list.extend([future[0] for future in futures if future is not None])
            audio_list.pages = len(audio_list.list)
            return audio_list
        except Exception as e:
            print(e)
            return None

    async def _try_to_get_audio_url(self, bvid: str, p: int = 1):
        url = f"https://www.bilibili.com/video/{bvid}/"
        param = {
            "p": p,
            "vd_source": "a97ce8f6ce42e3ca9a7f2426d0a483f0"
        }
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(url, params=param, headers=header) as response:
                # 等待响应时间
                text = await self._wait_for_text(response, 2)
                # text = await response.text()
                if response.status == 200 and text is not None:
                    try:
                        pattern_info = r'<script>window.__INITIAL_STATE__=(.*?);\(function'
                        info_data = re.findall(pattern_info, text, re.S)[0]
                        pattern_audio = r'<script>window.__playinfo__=(.*?)</script>'
                        audio_data = re.findall(pattern_audio, text, re.S)[0]
                        info_data = json.loads(info_data)
                        audio = {
                            'audio_url': json.loads(audio_data)['data'].get('dash').get('audio')[0].get('base_url'),
                            'aid': info_data.get('aid'),
                            'bvid': bvid,
                            'cid': info_data.get('videoData').get('pages')[p - 1].get('cid'),
                            'title': info_data.get('videoData').get('title'),
                            'part': info_data.get('videoData').get('pages')[p - 1].get('part'),
                            'desc': info_data.get('videoData').get('desc'),
                            'time_public': datetime.fromtimestamp(info_data.get('videoData').get('pubdate')).strftime(
                                '%Y-%m-%d'),
                            'owner_id': info_data.get('upData').get('mid'),
                            'owner_name': info_data.get('upData').get('name'),
                            'face': info_data.get('upData').get('face'),
                            'pic_url': info_data.get('videoData').get('pic')
                        }

                        pages = info_data.get('videoData').get('videos')
                        return AudioBilibili(**audio), pages
                    except Exception as e:
                        print(f"{e}: something wrong in _try_to_get_audio_url")
                else:
                    return None

    async def _wait_for_text(self, response, timeout=10):
        text = await response.text()
        pattern_audio = r'<script>window.__playinfo__=(.*?)</script>'
        audio_data = re.findall(pattern_audio, text, re.S)[0]
        audio_url = json.loads(audio_data)['data'].get('dash').get('audio')[0].get('base_url')
        # 检查文本内容是否包含预期的文本
        if "https://xy" in audio_url:
            return text
        else:
            time_2_sleep = random.random()
            await asyncio.sleep(random.random())
            timeout -= time_2_sleep
            if timeout > 0:
                return await self._wait_for_text(response, timeout=timeout)
            else:
                return None


if __name__ == '__main__':
    client = BilibiliClient()
    print(client.get_audio_url("BV18m411271p"))
    # print(client.get_audio_url("BV1SA41157Nt"))
