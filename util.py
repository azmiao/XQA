import asyncio
import json
import os
import random
import re
import urllib
import base64

from hoshino import R, logger, util
from sqlitedict import SqliteDict

from .textfilter.filter import DFAFilter

# ==================== ↓ 可修改的配置 ↓ ====================
'''
建议只修改配置，不删注释，不然以后会忘了怎么改还可以再看看
'''

# 储存数据位置（二选一，初次使用后不可改动，除非自己手动迁移，重启BOT生效，也可换成自己想要的路径）
FILE_PATH = R.img('xqa').path  # 数据在res文件夹里
# FILE_PATH = os.path.dirname(__file__)     # 数据在插件文件夹里

# 是否使用星乃自带的严格词库（二选一，可随时改动，重启BOT生效）
# USE_STRICT = True     # 使用星乃自带敏感词库，较为严格，安全可靠
USE_STRICT = False  # 使用XQA自带敏感词库，较为宽容，可自行增删

# 是否要启用消息分段发送，仅在查询问题时生效，避免消息过长发不出去（可随时改动，重启BOT生效）
IS_SPILT_MSG = True  # 是否要启用消息分段，默认开启，关闭改成False
MSG_LENGTH = 1000  # 消息分段长度限制，只能数字，千万不能太小，默认1000
SPLIT_INTERVAL = 1  # 消息分段发送时间间隔，只能数字，单位秒，默认1秒

# 是否使用转发消息发送，仅在查询问题时生效，和上方消息分段可同时开启（可随时改动，重启BOT生效）
IS_FORWARD = False  # 开启后将使用转发消息发送，默认关闭

# 设置问答的时候，是否校验回答的长度，最大长度和上方 MSG_LENGTH 保持一致（可随时改动，重启BOT生效）
IS_JUDGE_LENGTH = False  # 校验回答的长度，在长度范围内就允许设置问题，超过就不允许，默认开启

# 如果开启分段发送，且长度没超限制，且开启转发消息时，由于未超长度限制只有一条消息，这时是否需要直接发送而非转发消息（可随时改动，重启BOT生效）
IS_DIRECT_SINGER = True  # 直接发送，默认开启

# 看问答的时候，展示的分隔符（可随时改动，重启BOT生效）
SPLIT_MSG = ' | '  # 默认' | '，可自行换成'\n'或者' '等。单引号不能漏

#是否使用base64格式发送图片（适合使用docker部署或者使用shamrock）
ISBASE64 = False

# ==================== ↑ 可修改的配置 ↑ ====================


# 判断是否在群里
async def judge_ismember(bot, group_id: str, user_id: str) -> bool:
    member_list = await bot.get_group_member_list(group_id=int(group_id))
    user_list = []
    for member in member_list:
        user_id_tmp = member['user_id']
        user_list.append(str(user_id_tmp))
    if user_id in user_list:
        return True
    else:
        return False


# 获取数据库
async def get_database() -> SqliteDict:
    # 创建目录
    img_path = os.path.join(FILE_PATH, 'img/')
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    db_path = os.path.join(FILE_PATH, 'data.sqlite')
    # 替换默认的pickle为josn的形式读写数据库
    db = SqliteDict(db_path, encode=json.dumps, decode=json.loads, autocommit=True)
    return db


# 获取群列表
async def get_g_list(bot) -> list:
    group_list = await bot.get_group_list()
    g_list = []
    for group in group_list:
        group_id = group['group_id']
        g_list.append(str(group_id))
    return g_list


# 搜索问答
async def get_search(que_list: list, search_str: str) -> list:
    if not search_str:
        return que_list
    search_list = []
    for question in que_list:
        if re.search(rf'\S*{search_str}\S*', question):
            search_list.append(question)
    return search_list


# 匹配替换字符
async def replace_message(match_que: re.Match, match_dict: dict, que: str) -> str:
    ans_tmp = match_dict.get(que)
    # 随机选择
    ans = random.choice(ans_tmp)
    flow_num = re.search(r'\S*\$([0-9])\S*', ans)
    if not flow_num:
        return ans
    for i in range(int(flow_num.group(1))):
        ans = ans.replace(f'${i + 1}', match_que.group(i + 1))
    return ans


# 调整转义分割字符 “#”
async def adjust_list(list_tmp: list, char: str) -> list:
    ans_list = []
    str_tmp = list_tmp[0]
    i = 0
    while i < len(list_tmp):
        if list_tmp[i].endswith('\\'):
            str_tmp += char + list_tmp[i + 1]
        else:
            ans_list.append(str_tmp)
            str_tmp = list_tmp[i + 1] if i + 1 < len(list_tmp) else list_tmp[i]
        i += 1
    return ans_list


# 下载以及分类图片
async def doing_img(bot, img: str, is_ans: bool = False, save: bool = False) -> str:
    img_path = os.path.join(FILE_PATH, 'img/')
    if save:
        try:
            img_url = await bot.get_image(file=img)
            file = os.path.join(img_path, img)
            if not os.path.isfile(img_path + img):
                urllib.request.urlretrieve(url=img_url['url'], filename=file)
                logger.critical(f'XQA: 已下载图片{img}')
        except:
            if not os.path.isfile(img_path + img):
                logger.critical(f'XQA: 图片{img}已经过期，请重新设置问答')
            pass
    if is_ans:  # 保证保存图片的完整性，方便迁移和后续做操作
        return 'file:///' + os.path.abspath(img_path + img)
    return img


# 进行图片处理
async def adjust_img(bot, str_raw: str, is_ans: bool = False, save: bool = False) -> str:
    flit_msg = beautiful(str_raw)  # 整个消息匹配敏感词
    cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)=(\S+?)])', str_raw)  # 找出其中所有的CQ码
    # 对每个CQ码元组进行操作
    for cqcode in cq_list:
        flit_cq = beautiful(cqcode[0])  # 对当前的CQ码匹配敏感词
        raw_body = cqcode[3].split(',')[0].split('.image')[0].split('/')[-1].split('\\')[-1]  # 获取等号后面的东西，并排除目录
        if cqcode[1] == 'image':
            # 对图片单独保存图片，并修改图片路径为真实路径
            raw_body = raw_body if '.' in raw_body else raw_body + '.image'
            raw_body = await doing_img(bot, raw_body, is_ans, save)
        if is_ans:
            #回答问题用base64格式发送
            if ISBASE64:
                with open(raw_body.replace('file:///', ''),"rb") as file:
                    raw_body = "base64://" + base64.b64encode(file.read()).decode()
            # 如果是回答的时候，就将 匹配过的消息 中的 匹配过的CQ码 替换成未匹配的
            flit_msg = flit_msg.replace(flit_cq, f'[CQ:{cqcode[1]},{cqcode[2]}={raw_body}]')
        else:
            # 如果是保存问答的时候，就只替换图片的路径，其他CQ码的替换相当于没变
            str_raw = str_raw.replace(cqcode[0], f'[CQ:{cqcode[1]},{cqcode[2]}={raw_body}]')
    # 解决回答中不用于随机回答的\#
    flit_msg = flit_msg.replace('\#', '#')
    return str_raw if not is_ans else flit_msg


# 匹配消息
async def match_ans(info: dict, message: str, ans: str) -> str:
    list_tmp = list(info.keys())
    list_tmp.reverse()
    # 优先完全匹配
    if message in list_tmp:
        return random.choice(info[message])
    # 其次正则匹配
    for que in list_tmp:
        try:
            cq_list = re.findall(r'\[(CQ:(\S+?),(\S+?)=(\S+?))\]', que)  # 找出其中所有的CQ码
            que_new = que
            for cq_msg in cq_list:
                que_new = que_new.replace(cq_msg[0], '\[' + cq_msg[1] + '\]')
            if re.match(que_new + '$', message):
                ans = await replace_message(re.match(que_new + '$', message), info, que)
                break
        except re.error:
            # 如果que不是re.pattern的形式就跳过
            continue
    return ans


# 删啊删
async def delete_img(list_raw: list):
    for str_raw in list_raw:
        img_list = re.findall(r'(\[CQ:image,file=(.+?\.image)\])', str_raw)
        for img in img_list:
            file = img[1]
            try:
                file = os.path.split(file)[-1]
            except:
                pass
            try:
                os.remove(os.path.abspath(FILE_PATH + '/img/' + img[1]))
                logger.info(f'XQA: 已删除图片{file}')
            except:
                logger.info(f'XQA: 图片{file}不存在，无需删除')


# 和谐模块
def beautifulworld(msg: str) -> str:
    w = ''
    infolist = msg.split('[')
    for i in infolist:
        if i:
            try:
                w = w + '[' + i.split(']')[0] + ']' + beautiful(i.split(']')[1])
            except:
                w = w + beautiful(i)
    return w


# 切换和谐词库
def beautiful(msg: str) -> str:
    beautiful_message = DFAFilter()
    beautiful_message.parse(os.path.join(os.path.dirname(__file__), 'textfilter', 'sensitive_words.txt'))
    if USE_STRICT:
        msg = util.filt_message(msg)
    else:
        msg = beautiful_message.filter(msg)
    return msg


# 消息分段 | 输入：问题列表 和 初始的前缀消息内容 | 返回：需要发送的完整消息列表（不分段列表里就一个）
def spilt_msg(msg_list: list, init_msg: str) -> list:
    result_list = []
    # 未开启长度限制
    if not IS_SPILT_MSG:
        logger.info('XQA未开启长度限制')
        result_list.append(init_msg + SPLIT_MSG.join(msg_list))
        return result_list

    # 开启了长度限制
    logger.info(f'XQA已开启长度限制，长度限制{MSG_LENGTH}')
    lenth = len(init_msg)
    tmp_list = []
    for msg_tmp in msg_list:
        if msg_list.index(msg_tmp) == 0:
            msg_tmp = init_msg + msg_tmp
        lenth += len(msg_tmp)
        # 判断如果加上当前消息后会不会超过字符串限制
        if lenth < MSG_LENGTH:
            tmp_list.append(msg_tmp)
        else:
            result_list.append(SPLIT_MSG.join(tmp_list))
            # 长度和列表置位
            tmp_list = [msg_tmp]
            lenth = len(msg_tmp)
    result_list.append(SPLIT_MSG.join(tmp_list))
    return result_list


# 发送消息函数
async def send_result_msg(bot, ev, result_list):
    # 未开启转发消息
    if not IS_FORWARD:
        logger.info('XQA未开启转发消息，将循环分时直接发送')
        # 循环发送
        for msg in result_list:
            await bot.send(ev, msg)
            await asyncio.sleep(SPLIT_INTERVAL)
        return

    # 开启了转发消息但总共就一条消息，且 IS_DIRECT_SINGER = True
    if IS_DIRECT_SINGER and len(result_list) == 1:
        logger.info('XQA已开启转发消息，但总共就一条消息，将直接发送')
        await bot.send(ev, result_list[0])
        return

    # 开启了转发消息
    logger.info('XQA已开启转发消息，将以转发消息形式发送')
    forward_list = []
    for result in result_list:
        data = {
            "type": "node",
            "data": {
                "name": "你问我答BOT",
                "uin": str(ev.self_id),
                "content": result
            }
        }
        forward_list.append(data)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=forward_list)
