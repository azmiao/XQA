import asyncio
import base64
import json
import os
import random
import re
from urllib import request

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

# 是否使用base64格式发送图片（适合使用docker部署或者使用shamrock）
IS_BASE64 = False

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
    # 替换默认的pickle为json的形式读写数据库
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


# 下载图片并转换图片路径
async def doing_img(bot, img_name: str, img_file: str, save: bool) -> str:
    img_path = os.path.join(FILE_PATH, 'img')
    file = os.path.join(img_path, img_name)

    # 调用协议客户端实现接口下载图片
    if save:
        # 先重新拿URL，防止被客户端CQ码的缓存忽悠
        img_data = None
        try:
            img_data = await bot.get_image(file=img_file)
        except Exception as e:
            logger.critical(f'XQA: 调用get_image接口查询图片{img_file}出错:' + str(e))
            assert Exception(f'调用get_image接口查询图片{img_file}出错:' + str(e))

        # 下载文件
        url = img_data['url']
        try:
            if not os.path.isfile(file):
                request.urlretrieve(url=url, filename=file)
                logger.critical(f'XQA: 已从{url}下载到图片{img_name}')
        except Exception as e:
            logger.critical(f'XQA: 从{url}下载图片{img_name}出错:' + str(e))
            assert Exception(f'调用get_image接口查询图片{img_name}出错:' + str(e))

    if IS_BASE64:
        # base64格式
        with open(file, 'rb') as f:
            image_file = 'base64://' + base64.b64encode(f.read()).decode()
    else:
        # file格式
        image_file = 'file:///' + os.path.abspath(file)
    return image_file


# 根据CQ中的"xxx=xxxx,yyy=yyyy,..."提取出file和file_name
async def extract_file(cq_code_str: str) -> (str, str):
    # 解析所有CQ码参数
    cq_split = cq_code_str.split(',')
    # 拿到file参数 | 如果是单文件名：原始CQ | 如果是带路径的文件名：XQA本地已保存的图片，需要获取到单文件名
    image_file_raw = next(filter(lambda x: x.startswith('file='), cq_split), '')
    file_data = image_file_raw.replace('file=', '')
    image_file = file_data.split('\\')[-1].split('/')[-1] if 'file:///' in file_data else file_data

    # 文件名 | Go-cq是没有这些参数的，可以直接用file参数 | 如果有才做特殊兼容处理：优先级：file_unique > filename > file_id
    image_file_name_raw = (next(filter(lambda x: x.startswith('file_unique='), cq_split), '')
                           .replace('file_unique=', ''))
    image_file_name_raw = (next(filter(lambda x: x.startswith('filename='), cq_split), '')
                           .replace('filename=', '')) if not image_file_name_raw else image_file_name_raw
    image_file_name_raw = (next(filter(lambda x: x.startswith('file_id='), cq_split), '')
                           .replace('file_id=', '')) if not image_file_name_raw else image_file_name_raw
    # 如果三个都没有 | 那就直接用file参数，比如Go-cq
    image_file_name = image_file_name_raw if image_file_name_raw else image_file
    # 补齐文件拓展名
    image_file_name = image_file_name if '.' in image_file_name[-10:] else image_file_name + '.image'
    return image_file, image_file_name


# 进行图片处理 | 问题：无需过滤敏感词，回答：需要过滤敏感词
async def adjust_img(bot, str_raw: str, is_ans: bool, save: bool) -> str:
    # 找出其中所有的CQ码
    cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)])', str_raw)
    # 整个消息过滤敏感词，问题：无需过滤
    flit_msg = beautiful(str_raw) if is_ans else str_raw
    # 对每个CQ码元组进行操作
    for cq_code in cq_list:
        # 对当前的完整的CQ码过滤敏感词，问题：无需过滤
        flit_cq = beautiful(cq_code[0]) if is_ans else cq_code[0]
        # 判断是否是图片
        if cq_code[1] == 'image':
            # 解析file和file_name
            image_file, image_file_name = await extract_file(cq_code[2])
            # 对图片单独保存图片，并修改图片路径为真实路径
            image_file = await doing_img(bot, image_file_name, image_file, save)
            # 图片CQ码：替换
            flit_msg = flit_msg.replace(flit_cq, f'[CQ:{cq_code[1]},file={image_file}]')
        else:
            # 其他CQ码：原封不动放回去，防止CQ码被敏感词过滤成错的了
            flit_msg = flit_msg.replace(flit_cq, cq_code[0])
    # 解决回答中不用于随机回答的\#
    flit_msg = flit_msg.replace('\\#', '#')
    return flit_msg


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
            # 找出其中所有的CQ码
            cq_list = re.findall(r'\[(CQ:(\S+?),(\S+?)=(\S+?))]', que)
            que_new = que
            for cq_msg in cq_list:
                que_new = que_new.replace(cq_msg[0], '[' + cq_msg[1] + ']')
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
        # 这里理论上是已经规范好了的图片 | file参数就直接是路径或者base64
        cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)])', str_raw)
        for cq_code in cq_list:
            cq_split = str(cq_code[2]).split(',')
            image_file_raw = next(filter(lambda x: x.startswith('file='), cq_split), '')
            image_file = image_file_raw.replace('file=', '').replace('file:///', '')
            if 'base64' in image_file:
                # 目前屎山架构base64不好删，不管了
                continue
            img_path = os.path.join(FILE_PATH, 'img', image_file)
            try:
                os.remove(img_path)
                logger.info(f'XQA: 已删除图片{image_file}')
            except Exception as e:
                logger.info(f'XQA: 图片{image_file}删除失败：' + str(e))


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
    length = len(init_msg)
    tmp_list = []
    for msg_tmp in msg_list:
        if msg_list.index(msg_tmp) == 0:
            msg_tmp = init_msg + msg_tmp
        length += len(msg_tmp)
        # 判断如果加上当前消息后会不会超过字符串限制
        if length < MSG_LENGTH:
            tmp_list.append(msg_tmp)
        else:
            result_list.append(SPLIT_MSG.join(tmp_list))
            # 长度和列表置位
            tmp_list = [msg_tmp]
            length = len(msg_tmp)
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
