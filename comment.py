from bilibili_api import comment, sync, bvid2aid, Credential
import datetime
import json

# 读取配置文件
with open('config.json') as f:
    config = json.load(f)

# 打开浏览器 按F12 找到 b站 的 cookie
SESSDATA = config['USER']['SESSDATA']
BILI_JCT = config['USER']['BILI_JCT']
BUVID3 = config['USER']['BUVID3']

# 实例化 Credential 类
credential = Credential(
    sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)


# 需要用户信息才能查看更多相关评论


async def get_all_sub_comments(av, rpid):
    # 存储评论
    subComments = []
    page_index = 1
    ps = 10
    # 实例化 Comment 类
    com = comment.Comment(
        oid=av, type_=comment.CommentResourceType.VIDEO, rpid=rpid, credential=credential)

    while True:
        c = await com.get_sub_comments(page_index=page_index)
        # print(c)
        page_index += 1
        # 'page': {'num': 1, 'size': 10, 'count': 27} 也可以根据 num * size >= count 来判断已经全部读取
        if c['replies']:
            subComments.extend(c['replies'])
            if len(c['replies']) < ps:   # 请求10数据，获取不到10条，说明到底了
                break
        else:
            break
    return subComments

# 把隐藏的子评论读取出来


async def get_all_page_comments(av, replies):
    for reply in replies:
        # 判断 阿B 有么有把 子评论 隐藏了
        if ('sub_reply_entry_text' in reply['reply_control']):
            reply['replies'] = await get_all_sub_comments(av, reply['rpid'])
    return replies

# 检测是否含有 关键字


def black_cheak(cmt, blackList, whiteList, upper_mid, able_printcomment) -> bool:
    # upper 操作过就不删除
    if cmt["mid"] == upper_mid:
        if able_printcomment:
            print('[upper comment]')
        return False
    elif cmt["up_action"]["like"] or cmt["up_action"]["reply"]:
        if able_printcomment:
            print('[upper like or reply]')
        return False
    elif any(e in cmt['content']['message'] for e in whiteList):
        if able_printcomment:
            print('[whiteList]')
        return False
    return any(e in cmt['content']['message'] for e in blackList)


async def main():

    for conf in config['VIDEOS']:
        BV = conf['BV']
        desc = ''
        if 'desc' in conf:
            desc = conf['desc']
        # oid
        av = bvid2aid(BV)
        # 黑名单，用逗号隔开 数组
        blackList = []
        if 'BlackList' in conf:
            blackList = conf['BlackList'].replace(' ', '').split(',')
            blackList = list(filter(None, blackList))  # 去掉 空字符串
        whiteList = []
        if 'WhiteList' in conf:
            whiteList = conf['WhiteList'].replace(' ', '').split(',')
            whiteList = list(filter(None, whiteList))  # 去掉 空字符串

        # 默认开启子评论检测，速度较慢
        able_subcomment = True
        if 'able_subcomment' in conf:
            able_subcomment = conf['able_subcomment']

        able_printcomment = True
        if 'able_printcomment' in conf:
            able_printcomment = conf['able_printcomment']

        able_delete = False
        if 'able_delete' in conf:
            able_delete = conf['able_delete']

        # 存储评论
        comments = []
        # 页码
        page = 1

        # 当前已获取数量
        count = 0

        # 要删除的名单
        delcommentList = []

        # 阿B 返回的结果，置顶单独有一列
        c = await comment.get_comments(av, comment.CommentResourceType.VIDEO, page)
        sumCount = c['page']['count']
        upper_mid = c['upper']['mid']
        # 置顶单独有一列，是数组
        if 'top_replies' in c:
            if able_subcomment:
                c['top_replies'] = await get_all_page_comments(av, c['top_replies'])
            comments.extend(c['top_replies'])

        while True:
            # 获取评论
            c = await comment.get_comments(av, comment.CommentResourceType.VIDEO, page)
            # print(c)
            # 存储评论，如果被评论被删除的多，后面的数据就为空了
            if c['replies']:  # 这是一页评论
                if able_subcomment:
                    c['replies'] = await get_all_page_comments(av, c['replies'])
                comments.extend(c['replies'])
            else:
                break
            # 增加已获取数量
            count += c['page']['size']
            # 增加页码
            page += 1

            if count >= c['page']['count']:
                # 当前已获取数量已达到评论总数，跳出循环
                break

        # 打印评论，并检测
        print(f"\n\n{datetime.datetime.now()} {BV} 描述： {desc}")
        if blackList:
            print("blackList:", blackList)
        if whiteList:
            print("whiteList:", whiteList)
        countSub = 0
        for cmt in comments:

            # 黑名单检测
            if black_cheak(cmt=cmt, blackList=blackList, whiteList=whiteList, upper_mid=upper_mid, able_printcomment=able_printcomment):
                delcommentList.append(cmt['rpid'])
                print(
                    f"x rpid:{cmt['rpid']} mid:{cmt['mid']} {cmt['member']['uname']}: {cmt['content']['message']}")
            elif able_printcomment:
                print(
                    f"rpid:{cmt['rpid']} {cmt['member']['uname']}: {cmt['content']['message']}")
            # 对子评论
            if cmt['replies']:
                for reply in cmt['replies']:
                    countSub += 1
                    # 对子评论也检测
                    if black_cheak(cmt=reply, blackList=blackList, whiteList=whiteList, upper_mid=upper_mid, able_printcomment=able_printcomment):
                        delcommentList.append(reply['rpid'])
                        print(
                            f"\tx 子评论： rpid:{reply['rpid']} mid:{reply['mid']} {reply['member']['uname']}: {reply['content']['message']}")
                    elif able_printcomment:
                        print(
                            f"\t 子评论： rpid:{reply['rpid']} {reply['member']['uname']}: {reply['content']['message']}")
        # 打印评论总数
        print(
            f"共有 {count + countSub} 条评论（含子评论 {countSub} 条）,被删除或系统屏蔽有 {sumCount - count}", "条")

        # 执行删除的名单
        # ps: b站 阿瓦隆评论系统 太有名了，被删除的人一般不会意识到被自己被删除了，反而骂 阿瓦隆的人也有，先推给阿瓦隆系统准没错，都是阿瓦隆屏蔽你了 ，当然 b站后台肯定有记录的 hh
        if able_delete:
            for delcomment in delcommentList:
                # 实例化 Comment 类
                com = comment.Comment(
                    oid=av, type_=comment.CommentResourceType.VIDEO, rpid=delcomment, credential=credential)
                await com.delete()
            print('删除', len(delcommentList), '条', delcommentList)


sync(main())
