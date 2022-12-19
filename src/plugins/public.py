from nonebot import on_command, on_notice
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from src.libraries.image import *


@event_preprocessor
async def preprocessor(bot, event, state):
    if hasattr(event, 'message_type') and event.message_type == "private" and event.sub_type != "friend":
        raise IgnoredException("not reply group temp message")

        
getHelp = on_command('help')

@getHelp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    help_str = '''可用命令如下：
查歌<乐曲标题的一部分> 查询符合条件的乐曲
[绿黄红紫白]id<歌曲编号> 查询乐曲信息或谱面信息
<歌曲别名>是什么歌 查询乐曲别名对应的乐曲
定数查歌 <定数>  查询定数对应的乐曲
定数查歌 <定数下限> <定数上限>
sb40 简洁版的B40查询
b40 正常B40查询
分数线 <难度+歌曲id> <分数线> 详情请输入“分数线 帮助”查看'''
    await getHelp.send(Message([
        MessageSegment("image", {
            "file": f"base64://{str(image_to_base64(text_to_image(help_str)), encoding='utf-8')}"
        })
    ]))


async def _group_poke(bot: Bot, event: Event) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and event.target_id == int(bot.self_id))
    return value


poke = on_notice(rule=_group_poke, priority=10, block=True)


@poke.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if event.__getattribute__('group_id') is None:
        event.__delattr__('group_id')
    await poke.send(Message([
        MessageSegment("poke",  {
           "qq": f"{event.sender_id}"
       })
    ]))

