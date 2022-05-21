'''
作者：AZMIAO

版本：1.0

XQA：支持正则，支持回流，支持随机回答，支持图片等CQ码的你问我答
'''

import re
from .operate_msg import set_que, show_que, del_que
from .util import judge_permission, judge_ismember, get_database, replace_message
from .move_data import write_info

from hoshino import Service

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
[有人问C你答D] 群管理员设置全群问答
[全群问E你答F] 维护组设置所有群都回答的内容

[查问答@某人] 限群管理单独查某人的全部问答
[查问答@某人G] 限群管理单独查某人的问答，G为搜索内容

[不要回答H] 删除某个回答H，优先删除我问其次有人问
[@某人不要回答H] 限群管理删除某人的某个回答H

[看看有人问] 看全群设置的问题
[看看有人问X] 搜索全群设置的问题，X为搜索内容

[看看我问] 看自己设置的问题
[看看我问Y] 搜索自己设置的问题，Y为搜索内容
'''.strip()

sv = Service('XQA', enable_on_default = True)

# 帮助界面
@sv.on_fullmatch('问答帮助')
async def help(bot, ev):
    await bot.send(ev, sv_help)

# 设置问答，支持正则表达式和回流
@sv.on_message('group')
async def set_question(bot, ev):
    results = re.match(r'^(全群|有人|我)问([\s\S]*)你答([\s\S]*)$', str(ev.message))
    if not results:
        return
    que_type = results.group(1)
    que_raw = results.group(2)
    ans_raw = results.group(3)
    if (not que_raw) or (not ans_raw):
        await bot.finish(ev, f'发送“{que_type}问◯◯你答◯◯”我才记得住~')
    group_id = str(ev.group_id)
    user_id = str(ev.user_id)
    if que_type == '有人':
        permission = await judge_permission(ev)
        if permission < 21:
            await bot.finish(ev, f'有人问只能群管理设置呢')
        user_id = 'all'
    elif que_type == '全群':
        permission = await judge_permission(ev)
        if permission < 999:
            await bot.finish(ev, f'全群问只能维护组设置呢')
        group_id = 'all'
    msg = await set_que(bot, group_id, user_id, que_raw, ans_raw)
    await bot.send(ev, msg)

# 看问答，支持模糊搜索
@sv.on_rex(r'^看看(有人|我)问([\s\S]*)$')
async def show_question(bot, ev):
    que_type = ev['match'].group(1)
    search_str = ev['match'].group(2)
    group_id = str(ev.group_id)
    user_id = str(ev.user_id)
    if que_type == '有人':
        permission = await judge_permission(ev)
        if permission < 21:
            await bot.finish(ev, f'有人问只能群管理设置呢')
        user_id = 'all'
    msg = await show_que(group_id, user_id, search_str)
    await bot.send(ev, msg)

# 搜索某个成员的问题和回答，限群管理员
@sv.on_prefix('查问答')
async def search_question(bot, ev):
    permission = await judge_permission(ev)
    if permission < 21:
        await bot.finish(ev, f'搜索某个成员的问答只能群管理操作呢。个人查询问答请使用“看看我问”+搜索内容')
    text_raw = str(ev.message)
    search_match = re.match(r'\[CQ:at,qq=([0-9]+)\] ?(\S*)', text_raw)
    try:
        user_id = search_match.group(1)
        search_str = search_match.group(2)
    except:
        await bot.finish(ev, f'请输入正确的格式！详情参考“问答帮助”')
    group_id = str(ev.group_id)
    flag = await judge_ismember(bot, group_id, user_id)
    if not flag:
        await bot.finish(ev, f'该成员{user_id}不在该群')
    msg = f'QQ({user_id}) 的查询结果：\n'
    msg += await show_que(group_id, user_id, search_str)
    # 下面那行是查问题的同时查回答，默认注释掉了，感觉没必要
    # msg += '\n' + await show_que(group_id, user_id, search_str, is_keys=False)
    await bot.send(ev, msg)

# 不要回答，管理员可以@人删除回答
@sv.on_message('group')
async def delete_question(bot, ev):
    unque_match = re.match(r'^(\[CQ:at,qq=[0-9]+\])? ?不要回答([\s\S]*)$', str(ev.message))
    if not unque_match:
        return
    user = unque_match.group(1)
    unque_str = unque_match.group(2)
    group_id = str(ev.group_id)
    user_id = str(ev.user_id)
    if user:
        user_id = str(re.findall(r'[0-9]+', user)[0])
        flag = await judge_ismember(bot, group_id, user_id)
        if not flag:
            await bot.finish(ev, f'该成员{user_id}不在该群')
        permission = await judge_permission(ev)
        if permission < 21:
            await bot.finish(ev, f'删除他人问答仅限群管理员呢')
    image_list = re.findall(r'(\[CQ:image,file=(\S+)\.image,url=(https\S+,subType=[0-9])\])', unque_str)
    if image_list:
        for image in image_list:
            unque_str = unque_str.replace(image[0], f'[CQ:image,file={image[1]}.image]')
    msg = await del_que(group_id, user_id, unque_str)
    await bot.send(ev, msg)

# 回复问答
@sv.on_message('group')
async def xqa(bot, ev):
    group_id = str(ev.group_id)
    user_id = str(ev.user_id)
    message = str(ev.message)
    ans = ''
    db = await get_database()
    group_dict = db.get(group_id, {'all': {}})
    user_dict = group_dict.get(user_id, {})
    image_list = re.findall(r'(\[CQ:image,file=(\S+)\.image,url=(https\S+,subType=[0-9])\])', message)
    if image_list:
        for image in image_list:
            message = message.replace(image[0], f'[CQ:image,file={image[1]}.image]')
    # 优先回复自己的问答
    for que in list(user_dict.keys()):
        match_que = re.match(que, message)
        if match_que:
            ans = await replace_message(match_que, user_dict, que)
            break
    # 没有自己的问答才回复有人问
    if not ans:
        for que in list(group_dict['all'].keys()):
            print(que, message)
            match_que = re.match(que, message)
            if match_que:
                ans = await replace_message(match_que, group_dict['all'], que)
                break
    # 无匹配结果
    if not ans:
        return
    cq_list = re.findall(r'(\\\[CQ:(\S+)\\\])', ans)
    ans_end = ans
    if cq_list:
        for cq_msg in cq_list:
            new_msg = '[CQ:' + cq_msg[1] + ']'
            ans_end = ans_end.replace(cq_msg[0], new_msg)
    await bot.send(ev, ans_end)

# 复制艾琳佬数据至此插件
# 不会影响之前的数据，大概（
@sv.on_fullmatch('.xqa_move_data')
async def move_move(bot, ev):
    await bot.send(ev, await write_info())