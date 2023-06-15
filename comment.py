from bilibili_api import comment, sync, bvid2aid, Credential
import datetime
import json

# 读取配置文件
with open('config.json') as f:
    config = json.load(f)


BV = config['VIDEO']['BV']
# 打开浏览器 按F12 找到 b站 的 cookie
SESSDATA = config['USER']['SESSDATA']
BILI_JCT = config['USER']['BILI_JCT']
BUVID3 = config['USER']['BUVID3']

# 黑名单，用逗号隔开 数组
blackList = config['VIDEO']['BlackList'].replace(' ', '').split(',')

# 默认开启子评论检测，速度较慢
able_subcomment = True
able_subcomment = config['VIDEO']['able_subcomment']


# 实例化 Credential 类
credential = Credential(
    sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
# oid
av = bvid2aid(BV)

# 需要用户信息才能查看更多相关评论


async def get_all_sub_comments(rpid):
    # 存储评论
    subComments = []
    page_index = 1
    # 实例化 Comment 类
    com = comment.Comment(
        oid=av, type_=comment.CommentResourceType.VIDEO, rpid=rpid, credential=credential)

    while True:
        c = await com.get_sub_comments(page_index=page_index)
        page_index += 1
        if c['replies']:
            subComments.extend(c['replies'])
        else:
            break
    return subComments

# 检测是否含有 关键字


def black_cheak(cmt, blackList, upper_mid):
    # upper 操作过就不删除
    if cmt["mid"] == upper_mid:
        print('upper comment')
        return False
    if cmt["up_action"]["like"] or cmt["up_action"]["reply"]:
        print('upper like or reply')
        return False
    return any(e in cmt['content']['message'] for e in blackList)


async def main():
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
    if c['top_replies']:
        comments.extend(c['top_replies'])

    while True:
        # 获取评论
        c = await comment.get_comments(av, comment.CommentResourceType.VIDEO, page)
        # print(c)
        # 存储评论，如果被评论被删除的多，后面的数据就为空了
        if c['replies']:  # 这是一页评论
            for reply in c['replies']:
                # 判断 阿B 有么有把 子评论 隐藏了
                if able_subcomment and ('sub_reply_entry_text' in reply['reply_control']):
                    reply['replies'] = await get_all_sub_comments(reply['rpid'])
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
    print(f"\n\n{datetime.datetime.now()} {BV}")
    print("blackList:", blackList)
    countSub = 0
    for cmt in comments:
        print(
            f"rpid:{cmt['rpid']} {cmt['member']['uname']}: {cmt['content']['message']}")
        # 黑名单检测
        if black_cheak(cmt, blackList, upper_mid):
            delcommentList.append(cmt['rpid'])
            print('x')
        # 对子评论
        if cmt['replies']:
            for reply in cmt['replies']:
                countSub += 1
                print(
                    f"\t 子评论： rpid:{reply['rpid']} {reply['member']['uname']}: {reply['content']['message']}")
                # 对子评论也检测
                if black_cheak(reply, blackList, upper_mid):
                    delcommentList.append(reply['rpid'])
                    print('\t x')

    # 打印评论总数
    print(
        f"共有 {count + countSub} 条评论（含子评论 {countSub} 条）,被删除或系统屏蔽有 {sumCount - count}", "条")
    print('删除', len(delcommentList), '条', delcommentList)

    # 执行删除的名单
    for delcomment in delcommentList:
        # 实例化 Comment 类
        com = comment.Comment(
            oid=av, type_=comment.CommentResourceType.VIDEO, rpid=delcomment, credential=credential)
        await com.delete()


sync(main())
