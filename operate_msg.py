import html
from .util import get_database, get_g_list, get_search, adjust_list, adjust_img, delete_img

# 保存问答
async def set_que(bot, group_id: str, user_id: str, que_raw: str, ans_raw: str) -> str:
    db = await get_database()
    que_raw = html.unescape(que_raw)
    que_raw = await adjust_img(bot,que_raw, save = True)
    ans_raw = html.unescape(ans_raw)
    ans_raw = await adjust_img(bot,ans_raw, save = True)
    ans = ans_raw.split('#')
    ans = await adjust_list(ans, '#')
    if group_id == 'all':
        group_list = await get_g_list(bot)
        for group_id in group_list:
            group_dict = db.get(group_id, {'all': {}})
            group_dict['all'][que_raw] = ans
            db[group_id] = group_dict
    elif user_id == 'all':
        group_dict = db.get(group_id, {'all': {}})
        group_dict['all'][que_raw] = ans
        db[group_id] = group_dict
    else:
        group_dict = db.get(group_id, {'all': {}})
        user_dict = group_dict.get(user_id, {})
        user_dict[que_raw] = ans
        group_dict[user_id] = user_dict
        db[group_id] = group_dict
    return '好的我记住了'

# 显示问答
async def show_que(group_id: str, user_id: str, search_str: str, is_self: bool=True) -> str:
    db = await get_database()
    search_str = html.unescape(search_str)
    msg = f'查询 “{search_str}” 相关的结果如下：\n' if (search_str and is_self) else ''
    msg_head = '本群中' if is_self else f'\n群{group_id}中'
    subject = '管理员' if user_id == 'all' else '你'
    if user_id == 'all':
        group_dict = db.get(group_id, {'all': {}})
        que_list = await get_search(list(group_dict['all'].keys()), search_str)
    else:
        group_dict = db.get(group_id, {'all': {}})
        user_dict = group_dict.get(user_id, {})
        que_list = await get_search(list(user_dict.keys()), search_str)
    if not que_list:
        msg += f'{msg_head}没有找到任何{subject}设置的问题呢' if is_self else ''
    else:
        msg += f'{msg_head}{subject}设置的问题有：\n' + ' | '.join(que_list)
    return msg

# 删除问答
async def del_que(group_id: str, user_id: str, unque_str: str, is_self: bool=True) -> str:
    db = await get_database()
    try :
        await delete_img(unque_str)
        print ('删除问答的图片成功')
    except:
        print ('删除问答的图片失败')
        pass
    unque_str = html.unescape(unque_str)
    group_dict = db.get(group_id, {'all': {}})
    user_dict = group_dict.get(user_id, {})
    if (not user_dict.get(unque_str)) and (not group_dict['all'].get(unque_str)):
        return '没有设置过该问题呢' if is_self else ''
    elif user_dict.get(unque_str):
        ans = user_dict.get(unque_str)
        user_dict.pop(unque_str)
        group_dict[user_id] = user_dict
    else:
        ans = group_dict['all'].get(unque_str)
        group_dict['all'].pop(unque_str)
    try :
        await delete_img(ans)
        print ('删除问答的图片成功')
    except:
        print ('删除问答的图片失败')
        pass
    ans_str = '#'.join(ans)
    db[group_id] = group_dict
    msg_head = '' if is_self else f'\n群{group_id}中'
    return f'{msg_head}我不再回答 “{ans_str}” 了'#想了想，这个地方暂时不改，容易头疼

# 复制问答
async def copy_que(group_1, group_2):
    db = await get_database()
    group_dict = db.get(group_1, {'all': {}})
    db[group_2] = group_dict
    return f'已将群{group_1}的有人问复制至群{group_2}'