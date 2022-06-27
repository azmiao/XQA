## XQA

一个支持正则，支持回流，支持随机回答，支持图片等CQ码的你问我答

PS.lan佬不开源，艾琳佬没有回流，所以还是自己动手丰衣足食吧，代码已经尽量简洁了

如遇到问题请反馈，要不点个star支持一下（

## 如何更新

> 若是从 v1.2.0 版本之后(包括 v1.2.0)的版本更新到最新版，直接

```
git pull
```

> 若是从 v1.2 版本之前(不包括 v1.2)的版本更新到最新版

先进行：
```
git pull
```
再找个群使用命令`.xqa_format_data`格式化一次。格式化期间可以看着后台日志，更新完后按照bot回复提示处理以下过期的图片

## 最近四条更新日志

22-06-24    v1.2.0  支持下载图片，以防图片过期，更新请务必使用命令`.xqa_format_data`格式化一次，感谢[@morarity123](https://github.com/morarity123)

22-06-01    v1.1.1  修复图片CQ码存储问题，emmm正则表达式写错了2333

22-05-26    v1.1.0  添加功能“看看全群问M”，“全群不要回答N”，“复制问答from..to..”，修正有人问权限错误

22-05-21    v1.0.1  优化逻辑，精简代码，现在匹配优先完全匹配其次正则匹配，以避免报错，请更新后删除res/img/xqa/data.sqlite文件后重新迁移一下数据

## 注意

### 软件要求

 + gocqhttp == 1.0.0-rc1 (大于此版本请自测效果有没有问题，未测试rc2及以上版本)

 + hoshino >= 2.0.0

### 使用说明

<details>
<summary>请点开查看</summary>

> 设置方式：
+ 支持多行匹配
+ 支持小表情，@人等
+ 支持图片，图片采用本地下载保存，永远不会过期

> 问题设置
+ 支持正则表达式
+ 需要回流请用英文括号分组
+ 只有群管理员可以设置有人问，维护组设置的全群问无特殊权限，等同于有人问，只是相当于多个群同时设置有人问，仅仅是方便维护组的功能

> 回答设置
+ 支持随机回复，用'#'分割回答，可以随机回复这几个回答，加上反斜杠形成'\#'就不会分割
+ 回流用$加数字，$1对应问题中第一个括号里的内容，$2就是第二个，以此类推

> 如何回答
+ 回答时优先完全匹配问题，匹配不到才正则匹配
+ 回答顺序按照设置顺序倒序，后设置的先回答
+ 优先返回第一个匹配到的问题对应的回答
+ 优先回答个人问，匹配不到再回答有人问

> 查看问题
+ 显示原始的问题，不会转义正则表达式
+ 显示顺序按照设置顺序，先设置的显示在前面
+ 普通群员和群管理员都可以查看或搜索：有人问和我问
+ 群管理员可以使用查问答@某人，查看他设置的个人问答，也可加搜索参数
+ 维护组使用看看全群问，可以在所有群里搜索问题

> 不要回答
+ 普通群员可以删除自己的问答，群管理员可以删除有人问
+ 群管理可以使用@某人不要回答，来删除某个群员的个人问答
+ 维护组使用全群不要回答，可以在所有群里都删除某个问答，某个群没有这个问答就跳过

</details>

## 功能

<details>
<summary>请点开查看</summary>

### 一般功能

| 功能命令 | 介绍 |
| :---- | :---- |
| 我问A你答B | 设置个人问题 |
| 有人问C你答D | 群管理员设置全群问答 |
| 查问答@某人 | 限群管理单独查某人的全部问答 |
| 查问答@某人G | 限群管理单独搜索某人的问答，G为搜索内容 |
| 不要回答H | 删除某个回答H，优先删除我问其次删除有人问，一次只删一个 |
| @某人不要回答H | 限群管理删除某人的某个回答H |
| 看看有人问 | 看全群设置的问题 |
| 看看有人问X | 搜索全群设置的问题，X为搜索内容 |
| 看看我问 | 看自己设置的问题 |
| 看看我问Y | 搜索自己设置的问题，Y为搜索内容 |

### 维护组命令

| 功能命令 | 介绍 |
| :---- | :---- |
| 全群问E你答F | 维护组设置bot所加的所有群都回答的内容 |
| 看看全群问M | 维护组搜索所有群的有人问，M为搜索内容 |
| 全群不要回答N | 维护组在每个群的有人问里都删除某个问答，没有就跳过 |
| 复制问答from群号1to群号2 | 将群号1的有人问复制到群号2<br>例如：复制问答from11248to114514。<br>注：该功能是为了bot新加群方便快速复制其他群的有人问过来，正常情况不建议使用 |

### 维护组附赠

>   如果之前使用过艾琳佬的[eqa](https://github.com/pcrbot/erinilis-modules/tree/master/eqa)，可以通过该功能将数据提取出来，不会删除原文件
    但请确保modules下有eqa，且eqa启用不启用均可

>   注意：移动数据只能移动每个群的有人问和我问，eqa的能多个群的有人问这里只能复制一个群(创建该有人问的那个群)，本插件里多群问答请使用全群问
    其他正则匹配的内容可能无法复制过来，您可以参照文末数据结构自己修改data_config.json

    总结:
    第一个命令：eqa的db数据 -> db_config.json -> data_config.json，有需要的请修改data_config.json
    第二个命令：data_config.json -> data.sqlite数据库(本插件使用的数据库)

| 功能命令 | 介绍 |
| :---- | :---- |
| .xqa_extract_data | 提取数据，注意：点号别漏 |
| .xqa_write_data | 将上一步提取的数据写入数据库，原有xqa的相同问答会被覆盖 |
| .xqa_format_data | 格式化数据，危险命令，只有从旧版本更新到v1.2.0才需要使用，首次安装就>=1.2.0的不需要使用 |

</details>

## 举几个例子

<details>
<summary>请点开查看</summary>

#### 设置问题

- 我问111你答222
  
    发送：111

    bot回复：222

- 我问(.{0,19})我(.{0,19})你答$1优衣酱$2
  
    发送：抱着我可爱的自己

    bot回复：抱着优衣酱可爱的自己

- 有人问333你答444#555#666

    发送：333

    bot回复：444或者555或者666，这里是随机发送

- 有人问(这里是某张图片)你答啊哈哈哈，寄汤来咯

    发送：(刚才某张图片)

    bot回复：啊哈哈哈，寄汤来咯

- 我问(.{1,19})饿了你答不准饿

    发送：我饿了

    bot回复：不准饿

#### 查看我问

- 看看我问

    bot回复：(你的所有问答)

- 看看我问123

    bot回复：(和123有关的你的所有问答)

#### 管理员查问答

- 查问答@某人

    bot回复：(这个人的所有问答)

- 查问答@某人456

    bot回复：(这个人的和456有关的所有问答)

</details>

## 使用教程

懒得写了，模块名'XQA'，和其他插件一样安装就`git clone`，更新就`git pull`，别忘了先装依赖

## 提取的数据结构 `data_config.json`

<details>
<summary>请点开查看(如果需要修改数据的话)</summary>

```
注："all"为有人问
保留全部CQ码，转移过来的图片依旧保持绝对目录，新设置的图片只用缓存
全部不转义，仅有问题由正则，正则就直接写正则匹配表达式
仅有回答里有回流，回流符号$直接写不用转义

{
    "qq群1": {
        "all": {
            "问题1": [
                "回答1",
                "回答2",
                "回答3"
            ],
            "问题2": [
                "回答"
            ]
        },
        "群员qq1": {
            "问题1": [
                "回答"
            ]
        },
        "群员qq2": {
            "问题1": [
                "回答"
            ]
        }
    },
    "qq群2": {
        "all": {
            "问题1": [
                "回答"
            ]
        }
}
```

</details>