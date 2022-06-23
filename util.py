from sqlitedict import SqliteDict
import json
import os
import re
import random
import urllib

from hoshino import R, logger

# 数据储存数据位置（初次使用后不可改动，默认与hoshino原生代码风格一致）
file_path = R.img('xqa').path # 数据在res文件夹里
# file_path = os.path.dirname(__file__) # 数据在插件文件夹里

# 判断是否在群里
async def judge_ismember(bot, group_id: str, user_id: str) -> bool:
    member_list = await bot.get_group_member_list(group_id = int(group_id))
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
    img_path = os.path.join(file_path, 'img/')
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    db_path = os.path.join(file_path, 'data.sqlite')
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
        ans = ans.replace(f'${i+1}', match_que.group(i+1))
    return ans

# 调整转义分割字符 “#”
async def adjust_list(list_tmp: list, char: str) -> list:
    ans_list = []
    str_tmp = list_tmp[0]
    i = 0
    while i < len(list_tmp):
        if list_tmp[i].endswith('\\'):
            str_tmp += char + list_tmp[i+1]
        else:
            ans_list.append(str_tmp)
            str_tmp = list_tmp[i+1] if i+1 < len(list_tmp) else list_tmp[i]
        i += 1
    return ans_list

# 匹配消息
async def match_ans(info: dict, message: str, ans: str) -> str:
    list_tmp = list(info.keys())
    list_tmp.reverse()
    for que in list_tmp:
        # 优先完全匹配
        if que == message:
            ans = random.choice(info[que])
            break
        # 其次正则匹配
        try:
            if re.match(que + '$', message):
                ans = await replace_message(re.match(que + '$', message), info, que)
                break
        except re.error:
            # 如果que不是re.pattern的形式就跳过
            continue
    return ans

# 进行图片处理和下载
async def adjust_img(bot, str_raw: str, save: bool = False) -> str:
    img_path = os.path.join(file_path, 'img/')
    # 缓存之前旧版的图片，如果是新问答这一块应该都不会执行
    for image in re.findall(r'(\[CQ:image,file=(\S+?\.image)\])', str_raw):
        if '\\' in image[1]:
            continue
        imgurl = await bot.get_image(file = image[1])
        file = os.path.join(img_path, image[1])
        img_file = file_path + '/img/' + image[1]
        try:
            urllib.request.urlretrieve(url=imgurl['url'], filename=file)
            logger.critical(f'XQA: 已下载图片{image[1]}')
            str_raw = str_raw.replace(image[0], f'[CQ:image,file=file:///{os.path.abspath(img_file)}]')
        except:
            logger.critical(f'XQA: 图片{image[1]}已经过期，请重新设置问答')
            pass
    # 缓存新问答的图片，如果是旧问答这一块应该都不会执行
    for image in re.findall(r'(\[CQ:image,file=(\S+?)\,url=(\S+?)\,subType\S*?\])', str_raw):
        try:
            file = os.path.join(img_path, image[1])
            img_file = file_path + '/img/' + image[1]
            if save and image[1] not in os.listdir(img_path):
                urllib.request.urlretrieve(url=image[2], filename=file)
                logger.info(f'XQA: 已下载图片{image[1]}')
            str_raw = str_raw.replace(image[0], f'[CQ:image,file=file:///{os.path.abspath(img_file)}]')
        except:
            pass
    return str_raw

# 删除图片
async def delete_img(list_raw: list) -> list:
    list_end = []
    for str_raw in list_raw:
        img_list = re.findall(r'(\[CQ:image,file=file:///(.+?\.image)\])', str_raw)
        for img in img_list:
            file = img[1]
            try:
                os.remove(file)
                logger.info(f'XQA: 已删除图片{file}')
            except:
                logger.info(f'XQA: 图片{file}不存在，无需删除')
        # 返回值换回缓存显示
        str_raw = str_raw.replace('file:///'+str(os.path.abspath(file_path + '/img'))+'\\', '')
        list_end.append(str_raw)
    return list_end