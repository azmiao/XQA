from .util import get_database, get_g_list, get_search, adjust_list, adjust_img

# 保存问答
async def set_que(bot, group_id: str, user_id: str, que_raw: str, ans_raw: str) -> str:
    db = await get_database()
    que_raw = await adjust_img(que_raw)
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

# 显示问答 (is_keys: 是->显示问题 否->显示回答, 目前用不上)
async def show_que(group_id: str, user_id: str, search_str: str, is_keys: bool=True) -> str:
    db = await get_database()
    msg = f'查询 “{search_str}” 相关的结果如下：\n' if search_str else ''
    subject = '管理员' if user_id == 'all' else '你'
    if user_id == 'all':
        group_dict = db.get(group_id, {'all': {}})
        que_list = list(group_dict['all'].keys()) if is_keys else list(group_dict['all'].values())
        que_list = await get_search(que_list, search_str)
    else:
        group_dict = db.get(group_id, {'all': {}})
        user_dict = group_dict.get(user_id, {})
        que_list = list(user_dict.keys()) if is_keys else list(group_dict['all'].values())
        que_list = await get_search(que_list, search_str)
    show_type = '问题' if is_keys else '回答'
    if not que_list:
        msg += f'没有找到任何{subject}设置的{show_type}呢'
    else:
        msg += f'本群中{subject}设置的{show_type}有：\n' + ' | '.join(que_list)
    return msg

# 删除问答
async def del_que(group_id: str, user_id: str, unque_str: str) -> str:
    db = await get_database()
    group_dict = db.get(group_id, {'all': {}})
    user_dict = group_dict.get(user_id, {})
    if (not user_dict.get(unque_str)) and (not group_dict['all'].get(unque_str)):
        return '没有设置过该问题呢'
    elif user_dict.get(unque_str):
        ans = user_dict.get(unque_str)
        user_dict.pop(unque_str)
        group_dict[user_id] = user_dict
    else:
        ans = group_dict['all'].get(unque_str)
        group_dict['all'].pop(unque_str)
    ans_str = '#'.join(ans)
    db[group_id] = group_dict
    return f'我不再回答 “{ans_str}” 了'