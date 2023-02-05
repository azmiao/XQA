'''
作者：AZMIAO

版本：1.4.0

XQA：支持正则，支持回流，支持随机回答，支持图片等CQ码的你问我答
'''

import re
import html
import os

from .operate_msg import set_que, show_que, show_all_group_que, del_que, copy_que
from .util import judge_ismember, get_database, match_ans, adjust_img, get_g_list, \
    delete_img, send_result_msg, MSG_LENTH, IS_JUDGE_LENTH
from .move_data import get_dict, write_info, format_info

from hoshino import Service, priv

sv_help = '''
=====注意=====

可多行匹配，可匹配图片等

回答可以用'#'分割回答，可以随机回复这几个回答,'\#'将不会分割

支持正则表达式，请用英文括号分组，回流用$加数字

正则例子：我问(.{0,19})我(.{0,19})你答$1优衣酱$2

然后发送：抱着我可爱的自己

bot就会回复：抱着优衣酱可爱的自己

=====================

[我问A你答B] 设置个人问题

[有人问C你答D] 群管理员设置本群的有人问

[看看有人问] 看本群设置的有人问

[看看有人问X] 搜索本群设置的有人问，X为搜索内容

[看看我问] 看自己设置的问题

[看看我问Y] 搜索自己设置的问题，Y为搜索内容

[查问答@某人] 限群管理单独查某人的全部问答

[查问答@某人G] 限群管理单独查某人的问答，G为搜索内容

[不要回答H] 删除某个回答H，优先删除我问其次有人问

[@某人不要回答H] 限群管理删除某人的某个回答H
'''.strip()

sv = Service('XQA', enable_on_default=True, help_=sv_help)


# 帮助界面
@sv.on_fullmatch('问答帮助')
async def help(bot, ev):
    await bot.send(ev, sv_help)


# 设置问答，支持正则表达式和回流
@sv.on_message('group')
async def set_question(bot, ev):
    results = re.match(r'^(全群|有人|我)问([\s\S]*)你答([\s\S]*)$', str(ev.message))
    if not results: return
    que_type, que_raw, ans_raw = results.group(1), results.group(2), results.group(3)
    if (not que_raw) or (not ans_raw):
        await bot.send(ev, f'发送“{que_type}问◯◯你答◯◯”我才记得住~')
        return
    if IS_JUDGE_LENTH and len(ans_raw) > MSG_LENTH:
        await bot.send(ev, f'回答的长度超过最大字符限制，限制{MSG_LENTH}字符，包括符号和图片转码，您设置的回答字符长度为[{len(ans_raw)}]')
        return
    group_id, user_id = str(ev.group_id), str(ev.user_id)

    if que_type == '有人':
        if priv.get_user_priv(ev) < 21:
            await bot.send(ev, f'有人问只能群管理设置呢')
            return
        user_id = 'all'
    elif que_type == '全群':
        if priv.get_user_priv(ev) < 999:
            await bot.send(ev, f'全群问只能维护组设置呢')
            return
        group_id = 'all'
    
    msg = await set_que(bot, group_id, user_id, que_raw, ans_raw, str(ev.group_id))
    await bot.send(ev, msg)


# 看问答，支持模糊搜索
@sv.on_rex(r'^看看(有人|我|全群)问([\s\S]*)$')
async def show_question(bot, ev):
    que_type, search_str = ev['match'].group(1), ev['match'].group(2)
    group_id, user_id = str(ev.group_id), str(ev.user_id)
    if que_type == '全群':
        group_list = await get_g_list(bot)
        result_list = await show_all_group_que(search_str, group_list)
    else:
        user_id = 'all' if que_type == '有人' else user_id
        msg_head = f'查询"{search_str}"相关的结果如下：\n' if search_str else ''
        result_list = await show_que(group_id, user_id, search_str, msg_head)
    # 发送消息
    await send_result_msg(bot, ev, result_list)


# 搜索某个成员的问题和回答，限群管理员
@sv.on_prefix('查问答')
async def search_question(bot, ev):
    if priv.get_user_priv(ev) < 21:
        await bot.send(ev, f'搜索某个成员的问答只能群管理操作呢。个人查询问答请使用“看看我问”+搜索内容')
        return
    search_match = re.match(r'\[CQ:at,qq=([0-9]+)\] ?(\S*)', str(ev.message))
    try:
        user_id, search_str = search_match.group(1), search_match.group(2)
    except:
        await bot.send(ev, f'请输入正确的格式！详情参考“问答帮助”')
        return
    group_id = str(ev.group_id)

    if not await judge_ismember(bot, group_id, user_id):
        await bot.send(ev, f'该成员{user_id}不在该群中，请检查')
        return

    msg_init = f'QQ({user_id})的查询结果：\n'
    msg_head = f'查询"{search_str}"相关的结果如下：\n' if search_str else ''
    result_list = await show_que(group_id, user_id, search_str, msg_init + msg_head)
    # 发送消息
    await send_result_msg(bot, ev, result_list)


# 不要回答，管理员可以@人删除回答
@sv.on_message('group')
async def delete_question(bot, ev):
    unque_match = re.match(r'^(\[CQ:at,qq=[0-9]+\])? ?(全群)?不要回答([\s\S]*)$', str(ev.message))
    if not unque_match: return
    user, is_all, unque_str = unque_match.group(1), unque_match.group(2), unque_match.group(3)
    group_id, user_id = str(ev.group_id), str(ev.user_id)
    if not unque_str:
        await bot.send(ev, f'删除问答请带上删除内容哦')
        return
    # 全群问的删除
    if is_all:
        if priv.get_user_priv(ev) < 999:
            await bot.send(ev, f'只有维护组可以删除所有群设置的有人问')
            return
        group_list = await get_g_list(bot)
        msg_dict = {}
        msg = f''
        for group_id in group_list:
            m, _ = await del_que(bot, group_id, 'all', unque_str, False)
            if m and not msg_dict.get(m): msg_dict[m] = []
            if m: msg_dict[m].append(group_id)
        for msg_tmp in list(msg_dict.keys()):
            g_list = msg_dict[msg_tmp]
            g_msg = ','.join(g_list)
            msg += f'\n在群{g_msg}中' + msg_tmp
        msg = '没有在任何群里找到该问题呢' if msg == f'' else msg.strip()
        await bot.send(ev, msg)
        return
    # 有人问和我问的删除
    if user:
        user_id = str(re.findall(r'[0-9]+', user)[0])
        if priv.get_user_priv(ev) < 21:
            await bot.send(ev, f'删除他人问答仅限群管理员呢')
            return
        if not await judge_ismember(bot, group_id, user_id):
            await bot.send(ev, f'该成员{user_id}不在该群')
            return
    # 仅调整不要回答的问题中的图片
    unque_str = await adjust_img(bot, unque_str)
    msg, del_image = await del_que(bot, group_id, user_id, unque_str, True, priv.get_user_priv(ev) < 21)
    await bot.send(ev, msg)
    await delete_img(del_image)


# 回复问答
@sv.on_message('group')
async def xqa(bot, ev):
    group_id, user_id, message = str(ev.group_id), str(ev.user_id), str(ev.message)
    db = await get_database()
    group_dict = db.get(group_id, {'all': {}})
    message = html.unescape(message)
    # 仅调整问题中的图片
    message = await adjust_img(bot, message)
    # 优先回复自己的问答
    ans = await match_ans(group_dict.get(user_id, {}), message, '')
    # 没有自己的问答才回复有人问
    ans = await match_ans(group_dict['all'], message, ans) if not ans else ans
    if ans:
        ans = await adjust_img(bot, ans, is_ans=True, save=True)
        await bot.send(ev, ans)


# 复制问答
@sv.on_prefix('复制问答from')
async def copy_question(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, f'该功能限维护组')
        return
    msg_list = str(ev.message).split('-')
    try:
        msg_0, msg_1 = str(msg_list[0]), str(msg_list[1])
    except:
        msg_0, msg_1 = str(msg_list[0]), ''
    group_list = msg_0.split('to')
    try:
        group_1, group_2 = str(int(group_list[0])), str(int(group_list[1]))
    except:
        await bot.send(ev, f'请输入正确的格式！')
        return
    group_list = await get_g_list(bot)
    if (group_1 not in group_list) or (group_2 not in group_list):
        await bot.send(ev, f'群号输入错误！请检查')
        return
    msg = await copy_que(group_1, group_2, msg_1)
    await bot.send(ev, msg)

# 添加敏感词
@sv.on_prefix('XQA添加敏感词')
async def add_sensitive_words(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, f'该功能限维护组')
        return
    info = ev.message.extract_plain_text().strip()
    infolist = info.split(' ')
    for i in infolist:
        file = os.path.join(os.path.dirname(__file__), 'textfilter/sensitive_words.txt')
        with open(file, 'a+', encoding='utf-8') as f:
            f.write(i + '\n')
    await bot.send(ev, f'添加完毕')


# 删除敏感词
@sv.on_prefix('XQA删除敏感词')
async def del_sensitive_words(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, f'该功能限维护组')
        return
    info = ev.message.extract_plain_text().strip()
    infolist = info.split(' ')
    for i in infolist:
        file = os.path.join(os.path.dirname(__file__), 'textfilter/sensitive_words.txt')
        with open(file, "r", encoding='utf-8') as f:
            lines = f.readlines()
        with open(file, "w", encoding='utf-8') as f:
            for line in lines:
                if line.strip("\n") != i:
                    f.write(line)
    await bot.send(ev, f'删除完毕')


# 提取艾琳佬的eqa数据
@sv.on_fullmatch('.xqa_extract_data')
async def hahahaha(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER): return
    await bot.send(ev, await get_dict())


# 写入提取出的数据
@sv.on_fullmatch('.xqa_write_data')
async def xixixixi(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER): return
    await bot.send(ev, await write_info())


# 格式化数据
@sv.on_fullmatch('.xqa_format_data')
async def lalalala(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER): return
    await bot.send(ev, '正在进行格式化，请查看后台日志')
    await bot.send(ev, await format_info(bot))
