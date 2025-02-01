## XQA

一个支持正则，支持回流参数，支持设置随机回答，支持图片等CQ码的你问我答

### ⚠ 警告 ⚠

请勿将多个拥有问答功能的BOT放在同一个群，否则由于他人恶意设置正则以致BOT相互问答的炸群风险自行负责

## 版本说明

#### 初版测试过基本可用的代码已停止更新，最后一版存在分支[v1.5.4](https://github.com/azmiao/XQA/tree/v1.5.4))中

#### v1.6.0+版本迁移了部分自用的闭源YuiChyanBot代码，理论上更兼容LLOnebot和NapCat，但由于本地已无HoshinoBot环境，未经完全测试，有问题请提出

## 最近更新日志

25-02-01    v1.6.1  从YuiChyanBot同步部分代码，并新增依赖httpx用于下载图片，以修复LLOnebot不能下载图片的问题

25-01-01    v1.6.0  重构部分代码，优化删除图片逻辑，优化解析逻辑兼容性，去除已经不能使用的迁移EQA相关代码

<details>
<summary>更以前的更新日志</summary>

24-11-05    v1.5.4  优化逻辑，尝试兼容NapCat新版本

24-09-02    v1.5.3  对NapCat最新版本进行兼容处理, [issue #15](https://github.com/azmiao/XQA/issues/15)

24-05-24    v1.5.2  新增图片的base64发送方式，在`util.py`中修改配置即可，默认不启用

23-08-31    v1.5.1  新增分群清空我问或者有人问

23-08-24    v1.5.0  新增分群控制启用或者禁用个人问答的功能，默认启用

23-03-04    v1.4.1  修复删除回答时@人的权限问题，同时增加本文档开头的警告提示【务必看一下】

23-02-05    v1.4.0  新增部分自定义配置在`util.py`中

22-12-08    v1.3.4  复制问答功能新增参数，方便群被封后转移数据，详情见下方维护组命令

22-09-26    v1.3.3  全群不要回答的时候缩减显示长度，[issue #8](https://github.com/azmiao/XQA/issues/8)

22-08-25    v1.3.2  修复普通人可以删除有人问的BUG~~呜呜，为什么现在才有人提醒我~~

22-08-25    v1.3.1  默认接入[@morarity123](https://github.com/morarity123)的自定义词库，比星乃的宽容

22-08-24    v1.3.0  【强烈建议更新】接入敏感词系统，防止出事

22-07-10    v1.2.2  兼容gocq的1.0.0-rc2及以上版本，并修复因为修复问题导致的问题

22-06-28    v1.2.1  改回以前的保存格式，方便转移以及其他可能的操作，修复一些可能出现的问题

22-06-24    v1.2.0  支持下载图片，以防图片过期，从旧版更新请务必使用命令`.xqa_format_data`格式化一次，感谢[@morarity123](https://github.com/morarity123)

22-06-01    v1.1.1  修复图片CQ码存储问题，emmm正则表达式写错了2333

22-05-26    v1.1.0  添加功能“看看全群问M”，“全群不要回答N”，“复制问答from..to..”，修正有人问权限错误

</details>

## 注意

### BASE64的说明

> 注意：BASE64模式下部分功能不可用，逻辑上可能无法实现，例如设置图片为问题

### 软件要求

> 协议实现客户端任选之一：
 + go-cqhttp(原版) >= 1.0.0-rc1 (优先推荐)
 + NapCat >= 3.0.0 (次级推荐，因为不同版本有差异，可能不太稳定，建议自测哦)
 + LLOnebot >= 4.6.2 (次级推荐)
 + go-cqhttp(LagrangeDev版) >= 2.0.0 (未测试)
 + OpenShamrock >= 1.1.1 (未测试)

> BOT后台支持：
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

> 添加/删除敏感词
+ 仅限维护组使用，添加敏感词可立刻作用于所有群
+ 支持一次添加多个敏感词或者删除多个敏感词，以空格相隔
+ 仅在使用XQA自带的敏感词库时生效

</details>

## 功能菜单（含维护组命令）

<details>
<summary>请点开查看</summary>

### 一般功能

| 功能命令     | 介绍                           |
|:---------|:-----------------------------|
| 我问A你答B   | 设置个人问题                       |
| 有人问C你答D  | 群管理员设置全群问答                   |
| 查问答@某人   | 限群管理单独查某人的全部问答               |
| 查问答@某人G  | 限群管理单独搜索某人的问答，G为搜索内容         |
| 不要回答H    | 删除某个回答H，优先删除我问其次删除有人问，一次只删一个 |
| @某人不要回答H | 限群管理删除某人的某个回答H               |
| 看看有人问    | 看全群设置的问题                     |
| 看看有人问X   | 搜索全群设置的问题，X为搜索内容             |
| 看看我问     | 看自己设置的问题                     |
| 看看我问Y    | 搜索自己设置的问题，Y为搜索内容             |

### 维护组命令

| 功能命令                  | 介绍                                                                                     |
|:----------------------|:---------------------------------------------------------------------------------------|
| 全群问E你答F               | 维护组设置bot所加的所有群都回答的内容                                                                   |
| 看看全群问M                | 维护组搜索所有群的有人问，M为搜索内容                                                                    |
| 全群不要回答N               | 维护组在每个群的有人问里都删除某个问答，没有就跳过                                                              |
| 复制问答from群号1to群号2      | 仅将群号1的有人问复制到群号2<br>例如：复制问答from11248to114514<br>注：该功能是为了bot新加群方便快速复制其他群的有人问过来，正常情况不建议使用 |
| 复制问答from群号1to群号2-self | 将群号1的个人问答复制到群号2<br>例如：复制问答from11248to114514-self                                       |
| 复制问答from群号1to群号2-full | 将群号1的全部问答（有人问+个人问答）复制到群号2<br>例如：复制问答from11248to114514-full                             |
| XQA新增敏感词 A B C        | 维护组可一次添加不限数量的敏感词，每个敏感词需要用空格隔开                                                          | 
| XQA删除敏感词 A B C        | 维护组可一次删除不限数量的敏感词，每个敏感词需要用空格隔开                                                          |
| XQA禁用我问               | 维护组可在某个群发送命令以禁用该群的个人问答相关功能，默认启用                                                        |
| XQA启用我问               | 维护组可在某个群发送命令以启用该群的个人问答相关功能                                                             |
| XQA清空本群所有我问           | 维护组可在某个群发送命令以清空该群所有人设置的我问                                                              |
| XQA清空本群所有有人问          | 维护组可在某个群发送命令以清空该群的有人问                                                                  |
| XQA提取数据               | 维护组可在某个群发送命令以将数据提取成json                                                                |
| XQA重建数据               | 维护组可在某个群发送命令以将json数据转换回data_temp.sqlite                                                |

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
