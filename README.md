---
date: 2023-06-14 19:45
tag: ZK
updated: 2023-06-15 09:27
---
# B站 评论区 控评 脚本

起初是做了一个稍带争议的视频，底下全是复读，烂梗的评论。看到了就手动删除，有点烦

弹幕可以设置 关键字 屏蔽，简单很多

就想写一个爬虫脚本检测，包含 关键字 的评论就直接删除，对 评论区 进行 控评



## 市场调研

说干就干，市场调研之后，发现 python3 有一个在维护的库， https://github.com/Nemo2011/bilibili-api

这就根据 api 写一个脚本，立即行动✌️

B站是 `B/S` 架构，特别好理解，很多都是 `Rustful` 请求，只要知道请求参数就可以获取数据了

首先要获取用户凭证信息（cookie） https://nemo2011.github.io/bilibili-api/#/get-credential

## 使用方式

首先要 安装 `python3` 和 `pip3` ，安装 `python3` 的时候会自动安装 `pip3。` 记得 添加 `path` 路径

cmd 执行：`$ pip3 install bilibili-api-python`

第二步，填写配置信息， 修改 `config_example.json` 的内容

```json
{
  "USER": {
    "SESSDATA": "请填写自己的 B站 cookie",
    "BILI_JCT": "不知道怎么写看 README",
    "BUVID3": "最后把本文件名改为 config.json "
  },
  "VIDEO": [
    {
      "BV": "BV1uv411q7Mv",
      "able_delete": false,      // 默认不开启删除，可以先测试一下，是否是需要删除的评论
      "able_subcomment": true,   // 把隐藏的子评论读取出来
      "able_printcomment": true, // 输出读取到的评论，否则只显示被删除的评论，测试成功后建议关闭
      "BlackList": "巨婴,脑残",  // 用英文逗号隔开关键字
      "WhiteList": "太牛了"
    },
    {                            // 多个视频 重复添加即可，用 {} ，逗号隔开
      "BV": "BV1uv411q7Mv",
      "able_delete": false,
      "able_subcomment": true,
      "able_printcomment": true,
      "BlackList": "巨婴,脑残",
      "WhiteList": "太牛了"
    }
  ]
}
```

填写 用户凭证信息（cookie） 后  
将 `config_example.json` 重命名为 `config.json`

最后一步
cmd 执行： `python3 comment.py >> comment.log`

同一个文件夹内 会出现一个 `comment.log`  用 默认的笔记本 打开
## 根据 api 自己写代码

一开始做一个简单的，针对单个视频：

1. 获取评论
    1. 获取评论简单，类似数据库的分页请求，根据 `page` 和 `count` 判断是否获取到全部评论。 阿B会返回 `replies` 数组 和 部分 二级子评论 `replies` 数组 ， 如果数据删的多了，最后几页为空
    2. 置顶评论是单独返回的
    3. 获取该评论的子评论，需要用户凭证。 阿B 会隐藏一些不好的评论，或者评论的人多一页展示不完，需要判断 阿B 有没有隐藏评论，然后获取该评论的子评论，这会显著降低速度
2. 检测关键字，保存需要删除的 `rpid`
    1. 建立一个 字符串数组，评论里面包含其中一个关键字，就添加到 删除名单 
    2. 在此之前增加判断 是不是 upper 发言，或者点赞评论 就不删除
    3. 增加了 白名单 检测
3. 发送删除请求
    1. 需要用户为 upper 或 upper的骑士团成员。推荐用骑士团成员，在 upper 粉丝中心 还可以撤回删除的评论
    2. 循环遍历删除名单，根据 `rpid` 发送删除请求

多个视频话 `for循环` 执行

完整代码见: [comment.py](./comment.py) 增加读取配置的代码

## 定时执行

控评肯定要反复执行

爬虫讲究一个度，不能太急 阿B 也会风控的，被 ip 封住的话，切换代理，要么就等两天解封

windows 有 定时任务管理器，就不细说了
Linux 用 https://juejin.cn/post/7082771155332890655

```sh
# crontab 定时任务清单查看 
crontab -l 
# crontab 定时任务清单编写 
crontab -e 

# shell脚本设置 
# 每19分钟执行一次 
*/19 * * * * * python3 /root/comment.py >> /root/comment.log
```

## 进阶

api接口和返回的数据具有实效性，如果有变动，需要修改可以提 issue，也可以自己改，我应该把我的思路讲得比较清晰了 

有什么想法，欢迎在 issue 提，比如

- 增加 动态 的评论区控制
- 更加精细的恶意检测
  - 对发送者进行判断，指定粉丝牌 和 限制等级 进行判定
- 将数据导出
- 对指定 up 的评论区 进行控评


## 个人想法

一开始的想法是，

爬虫，读取评论，把 评论的人的 Id ，违禁词，rpid 全部保存到mysql 

然后对数据进行分析，甚至ai语意分析，把恶心的人找出来，如果老是触发屏蔽词，直接拉黑

符合恶意的就删除

后来想想，唉，没必要，之后有需求了在搞，也是不难的事情，一个晚上就能写出来，就是需要资源去支持，需要花钱买服务器。

现在只需要自己电脑 安装一个 python3 就可以搞定，速度也很快
