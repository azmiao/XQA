from .util import *


# 保存问答
async def set_que(bot, group_id: str, user_id: str, que_raw: str, ans_raw: str, gid: str) -> str:
    db = await get_database()

    # 新问题只调整 | 但不要下载图片，只要能匹配上就可以
    que_raw = await adjust_img(bot, que_raw, False, False)
    # 已有问答再次设置的话，就先删除旧图片
    gid = gid if group_id == 'all' else group_id
    ans_old = db.get(gid, {}).get(user_id, {}).get(que_raw, [])
    if ans_old:
        await delete_img(ans_old)

    # 保存新的回答
    ans_raw = await adjust_img(bot, ans_raw, True, True)
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


# 显示有人/我问 和 查其他人的问答
async def show_que(group_id: str, user_id: str, search_str: str, msg_head: str) -> list:
    db = await get_database()
    # 对象
    user_object = '管理员' if user_id == 'all' else '你'

    # 查询问题列表
    if user_id == 'all':
        group_dict = db.get(group_id, {'all': {}})
        que_list = await get_search(list(group_dict['all'].keys()), search_str)
    else:
        group_dict = db.get(group_id, {'all': {}})
        user_dict = group_dict.get(user_id, {})
        que_list = await get_search(list(user_dict.keys()), search_str)

    # 获取消息列表
    if not que_list:
        result_list = [f'{msg_head}本群中没有找到任何{user_object}设置的问题呢']
    else:
        result_list = spilt_msg(que_list, f'{msg_head}{user_object}在群里设置的问题有：\n')
    return result_list


# 显示全群问答 | 单独做个函数
async def show_all_group_que(search_str: str, group_list: list) -> list:
    db = await get_database()
    result_list = []
    init_msg = f'查询"{search_str}"相关的结果如下：\n' if search_str else ''

    for group_id in group_list:
        msg_head = f'\n群{group_id}中设置的问题有：\n' if group_list.index(group_id) != 0 \
            else init_msg + f'\n群{group_id}中设置的问题有：\n'
        group_dict = db.get(group_id, {'all': {}})
        que_list = await get_search(list(group_dict['all'].keys()), search_str)
        # 找不到就跳过
        if not que_list:
            continue
        result_list += spilt_msg(que_list, msg_head)

    # 如果一个问题都没有 | 寄
    if not result_list:
        result_list.append('没有查到任何结果呢')
    return result_list


# 删除问答
async def del_que(group_id: str, user_id: str, no_que_str: str, is_singer_group: bool = True, is_self: bool = False):
    db = await get_database()
    # 调整问题文本图片
    no_que_str = await adjust_img(None, no_que_str, False, False)
    group_dict = db.get(group_id, {'all': {}})
    user_dict = group_dict.get(user_id, {})
    # 删除我问
    if is_self:
        if (not user_dict.get(no_que_str)) and (not group_dict['all'].get(no_que_str)):
            return '没有设置过该问题呢', ''
        elif (not user_dict.get(no_que_str)) and (group_dict['all'].get(no_que_str)):
            return '你没有权限删除有人问呢', ''
        else:
            ans = user_dict.get(no_que_str)
            user_dict.pop(no_que_str)
            group_dict[user_id] = user_dict
    # 删除有人问和全群问
    else:
        if (not user_dict.get(no_que_str)) and (not group_dict['all'].get(no_que_str)):
            return '没有设置过该问题呢' if is_singer_group else '', ''
        elif user_dict.get(no_que_str):
            ans = user_dict.get(no_que_str)
            user_dict.pop(no_que_str)
            group_dict[user_id] = user_dict
        else:
            ans = group_dict['all'].get(no_que_str)
            group_dict['all'].pop(no_que_str)
    ans_str = '#'.join(ans)
    # 调整回答文本图片
    ans_str = await adjust_img(None, ans_str, True, False)
    ans.append(no_que_str)
    db[group_id] = group_dict
    return f'我不再回答 “{ans_str}” 了', ans  # 返回输出文件以及需要删除的图片


# 复制问答
async def copy_que(group_1, group_2, copy_type):
    db = await get_database()
    if not copy_type:
        group_dict = db.get(group_1, {'all': {}}).get('all', {})
        group_dict_2 = db.get(group_2, {'all': {}})
        group_dict_2['all'] = group_dict
        db[group_2] = group_dict_2
        return f'已将群{group_1}的有人问复制至群{group_2}'
    elif copy_type == 'full':
        group_dict = db.get(group_1, {'all': {}})
        db[group_2] = group_dict
        return f'已将群{group_1}的全部问答复制至群{group_2}'
    elif copy_type == 'self':
        group_dict = db.get(group_1, {'all': {}})
        group_dict_2 = db.get(group_2, {'all': {}}).get('all', {})
        group_dict['all'] = group_dict_2
        db[group_2] = group_dict
        return f'已将群{group_1}的个人问答复制至群{group_2}'
    else:
        return f'不支持的复制类型输入：{copy_type}'


# 清空问答
async def delete_all(group_id, is_self):
    db = await get_database()
    group_dict = db.get(group_id, {'all': {}})
    if is_self:
        # 清除个人问答
        all_que = group_dict.get('all', {})
        group_dict.clear()
        group_dict['all'] = all_que
    else:
        # 清除所有有人问
        group_dict['all'] = {}
    db[group_id] = group_dict
