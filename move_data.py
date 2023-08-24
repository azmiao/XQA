"""
作者：AZMIAO
说明：该文件用于将艾琳佬的数据复制部分到本插件，请确保安装完依赖
"""

import base64
import hashlib
import json
import os
import re
import shutil

from hoshino import logger
from sqlitedict import SqliteDict

from .util import get_database, adjust_img, FILE_PATH


# 艾琳佬的数据库
async def read_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'eqa/data/db.sqlite')
    db = SqliteDict(db_path, encode=json.dumps, decode=json.loads, autocommit=True)
    return db


# 创建格式化后的文件
async def create_info():
    data = {}
    with open(os.path.join(FILE_PATH, 'db_config.json'), 'r', encoding='UTF-8') as f:
        config = json.load(f)
    for question in list(config.keys()):
        # 同一个问题的问答列表 list
        que_list = config[question]
        for que_tmp in que_list:
            user_id = que_tmp['user_id']
            group_id = que_tmp['group_id']
            # 是否是个人问答 bool
            is_me = que_tmp['is_me']
            # 回答列表 list
            message_list = que_tmp['message']
            msg = ''
            for message in message_list:
                if message['type'] == 'text':
                    msg += message['data']['text']
                elif message['type'] == 'at':
                    msg += f"[CQ:at,qq={message['data']['qq']}]"
                elif message['type'] == 'image':
                    try:
                        img_name = re.search(r'file:///\S+\\(\S+\.\S+)', message['data']['file']).group(1)
                        img_path = os.path.join(FILE_PATH, f'img/{img_name}')
                        i = open(os.path.abspath(img_path), "rb")
                        fd = i.read()
                        pmd5 = hashlib.md5(fd)
                        shutil.copyfile(img_path, str(pmd5.hexdigest()) + '.image')
                        msg += f"[CQ:image,file=file:///{str(pmd5.hexdigest()) + '.image'}]".replace('\\', '/')
                    except:
                        rm_base64(message['data']['file'])
                        i = open(message['data']['file'], "rb")
                        fd = i.read()
                        pmd5 = hashlib.md5(fd)
                        imgdata = base64.b64decode(fd)
                        file = open(FILE_PATH + '/img/' + str(pmd5.hexdigest()) + '.image', 'wb')
                        file.write(imgdata)
                        file.close()
                        msg += f"[CQ:image,file={str(pmd5.hexdigest()) + '.image'}]".replace('\\', '/')
            msg_list = [msg]
            # 迁移文本数据
            group_dict = data.get(group_id, {'all': {}})
            if not is_me:
                group_dict['all'][question] = msg_list
            else:
                user_dict = group_dict.get(user_id, {})
                user_dict[question] = msg_list
                group_dict[user_id] = user_dict
            data[group_id] = group_dict
    with open(os.path.join(FILE_PATH, 'data_config.json'), 'w', encoding='UTF-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# 只读形式临时转存艾琳佬的数据库
async def get_dict():
    if not os.path.exists(FILE_PATH):
        os.mkdir(FILE_PATH)
    if not os.path.exists(os.path.join(FILE_PATH, 'data_config.json')):
        db = await read_db()
        logger.info('临时数据文件不存在，因此开始转存艾琳佬的数据')
        with open(os.path.join(FILE_PATH, 'db_config.json'), 'w', encoding='UTF-8') as f:
            json.dump(dict(db), f, indent=4, ensure_ascii=False)
        await create_info()
        return f'''
成功临时转存数据至 -> hoshino/resimg/xqa/data_config.json，您可以打开改文件进行相关修改，数据结构详见README
注意：移动数据只能移动每个群的有人问和我问，eqa的能多个群的有人问这里只能复制一个群(创建该有人问的那个群)，本插件里多群问答请使用全群问
其他正则匹配的内容可能无法复制过来，您可以参照README自己修改data_config.json
本命令总结：eqa的db数据 -> db_config.json -> data_config.json，有需要的请修改data_config.json
下一个命令：data_config.json -> data.sqlite数据库(本插件使用的数据库)
        '''.strip()
    else:
        return 'hoshino/resimg/xqa/db_config.json 已存在，因此不再重新转存临时数据，需要重新生成请手动删除后再次使用本命令'


# 复制图片文件
async def copydirs(from_file, to_file):
    if not os.path.exists(to_file):
        os.mkdir(to_file)
    files = os.listdir(from_file)
    for f in files:
        shutil.copy(from_file + '/' + f, to_file + '/' + f)


# 写入本插件的数据库
async def write_info():
    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'eqa/data/db.sqlite')):
        return 'eqa数据不存在，请确保之前使用过eqa且未移动其位置'
    if not os.path.exists(os.path.join(FILE_PATH, 'db_config.json')):
        return '临时数据文件不存在，请先使用命令：.xqa_extract_data'
    # 新建新的数据库
    db = await get_database()
    with open(os.path.join(FILE_PATH, 'data_config.json'), 'r', encoding='UTF-8') as f:
        config = json.load(f)
    logger.info('创建本插件的数据库成功，开始迁移数据...')
    for group_id in list(config.keys()):
        db[group_id] = config[group_id]
    # 复制图片
    logger.info('开始复制图片')
    from_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'eqa/data/img')
    await copydirs(from_file, os.path.join(FILE_PATH, f'img/'))
    logger.info('复制完成，进程结束')
    return '数据复制完成，请自己检查确认是否正常'


# 格式化旧版数据
async def format_info(bot):
    db = await get_database()
    config = dict(db)
    for group_id in list(config.keys()):
        for user_id in list(config[group_id].keys()):
            for question in list(config[group_id][user_id].keys()):
                user = '有人问' if user_id == 'all' else 'qq:' + user_id
                logger.critical(f'开始格式化群{group_id}的{user}的问题: {question}')
                # 对问题：调整并下载图片
                question_new = await adjust_img(bot, question, save=True)
                # 对回答：调整并下载图片
                answer_list = []
                for answer in config[group_id][user_id][question]:
                    answer_new = await adjust_img(bot, answer, save=True)
                    answer_list.append(answer_new)
                # 修改config内容
                if question_new != question:
                    config[group_id][user_id][question_new] = answer_list
                    config[group_id][user_id].pop(question)
                else:
                    config[group_id][user_id][question] = answer_list
                logger.critical(f'该问题格式化完成！')
    # 写入格式化后的数据
    for group_id in list(config.keys()):
        db[group_id] = config[group_id]
    return '格式化完成！请自行在hoshino/log/critical.log检查格式化结果，若有提示图片过期的情况请自行删除他们或重新设置问题覆盖他们。'


def rm_base64(refile: str):
    lineList = []
    with open(refile, 'r', encoding='UTF-8') as file:
        line = file.readline()
        line2 = line.replace('base64://', '')
        lineList.append(line2)
    file.close()
    file = open(refile, 'w', encoding='UTF-8')
    for i in lineList:
        file.write(i)
    file.close()
