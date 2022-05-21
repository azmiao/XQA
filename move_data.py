'''
作者：AZMIAO

说明：该文件用于将艾琳佬的数据迁移到本插件，请确保原来的db.sqlite在本目录下，并安装完依赖
'''

from sqlitedict import SqliteDict
import os
import json
import re
import shutil

from hoshino import R

# 艾琳佬的数据库
async def read_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'eqa/data/db.sqlite')
    db = SqliteDict(db_path, encode=json.dumps, decode=json.loads, autocommit=True)
    return db

# 只写形式临时转存艾琳佬的数据库
async def get_dict():
    if not os.path.exists(os.path.join(R.img('xqa').path, 'db_config.json')):
        db = await read_db()
        print('临时数据文件不存在，因此开始转存艾琳佬的数据')
        with open(os.path.join(R.img('xqa').path, 'db_config.json'), 'w', encoding='UTF-8') as f:
            json.dump(dict(db), f, indent=4, ensure_ascii=False)
        print('成功临时转存数据至 -> db_config.json')
    else:
        print('临时数据文件 db_config.json 已生成，因此不再重新转存临时数据')

# 本插件的数据库
async def read_data_db():
    db_path = os.path.join(R.img('xqa').path, 'data.sqlite')
    db = SqliteDict(db_path, encode=json.dumps, decode=json.loads, autocommit=True)
    return db

# 复制图片文件
async def copydirs(from_file, to_file):
    if not os.path.exists(to_file):
        os.makedirs(to_file)
    files = os.listdir(from_file)
    for f in files:
        shutil.copy(from_file + '/' + f, to_file + '/' + f)

# 转义
async def process_cq(que_raw: str) -> str:
    que_raw.replace('\\', '\\\\').replace('|', '\|')
    que_raw.replace('?', '\?').replace('.', '\.')
    que_raw.replace('+', '\+').replace('*', '\*')
    que_raw.replace('[', '\[').replace(']', '\]')
    que_raw.replace('[', '\[').replace(']', '\]')
    que_raw.replace('^', '\^').replace('$', '\$')
    return que_raw

# 写入本插件的数据库
async def write_info():
    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'eqa/data/db.sqlite')):
        return 'eqa数据不存在，请确保之前使用过eqa且未移动其位置'
    # 提取数据并保存
    await get_dict()
    # 新建新的数据库
    db = await read_data_db()
    print('创建本插件的数据库成功，开始迁移数据...')
    with open(os.path.join(R.img('xqa').path, 'db_config.json'), 'r', encoding='UTF-8') as f:
        config = json.load(f)
    for question in list(config.keys()):
        #同一个问题的问答列表 list
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
                    img_name = re.search(r'file:///\S+\\(\S+\.\S+)', message['data']['file']).group(1)
                    img_path = os.path.join(R.img('xqa').path, f'img/{img_name}')
                    msg += f"[CQ:image,file=file:///{os.path.abspath(img_path)}]".replace('\\', '/')
            msg_list = [msg]
            # 迁移文本数据
            question = await process_cq(question)
            group_dict = db.get(group_id, {'all': {}})
            if not is_me:
                group_dict['all'][question] = msg_list
            else:
                user_dict = group_dict.get(user_id, {})
                user_dict[question] = msg_list
                group_dict[user_id] = user_dict
            db[group_id] = group_dict
    # 复制图片
    print('开始复制图片')
    from_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'eqa/data/img')
    await copydirs(from_file, os.path.join(R.img('xqa').path, f'img/'))
    print('复制完成，进程结束')
    return '数据复制完成，请自己检查确认是否正常'