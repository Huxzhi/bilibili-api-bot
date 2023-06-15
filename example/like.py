import asyncio
from bilibili_api import video, Credential


# 获取 cookie
SESSDATA = ''
BILI_JCT = ''
BUVID3 = ''


async def main() -> None:
    # 实例化 Credential 类
    credential = Credential(
        sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    # 实例化 Video 类
    v = video.Video(bvid="BV14c411g7Ld", credential=credential)
    info = await v.get_info()
    print(info)
    # 给视频点赞
    await v.like(True)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
