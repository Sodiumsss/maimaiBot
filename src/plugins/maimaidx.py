import re

from nonebot import on_command, on_regex
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg, EventMessage

from src.libraries.image import *
from src.libraries.maimai_best_40 import generate, generate_simple
from src.libraries.maimaidx_music import *


def song_txt(music: Music):
    return Message([
        MessageSegment("text", {
            "text": f"{music.id}. {music.title}\n"
        }),
        MessageSegment("image", {
            "file": f"https://www.diving-fish.com/covers/{get_cover_len4_id(music.id)}.png"
        }),
        MessageSegment("text", {
            "text": f"\n{'/'.join(music.level)}"
        })
    ])


def inner_level_q(ds1, ds2=None):
    result_set = []
    diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']
    if ds2 is not None:
        music_data = total_list.filter(ds=(ds1, ds2))
    else:
        music_data = total_list.filter(ds=ds1)
    for music in sorted(music_data, key=lambda i: int(i['id'])):
        for i in music.diff:
            result_set.append((music['id'], music['title'], music['ds'][i], diff_label[i], music['level'][i]))
    return result_set


inner_level = on_command('inner_level ', aliases={'定数查歌 '})


@inner_level.handle()
async def _(message: Message = CommandArg()):
    argv = str(message).strip().split(" ")
    if len(argv) > 2 or len(argv) == 0:
        await inner_level.finish("命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>")
        return
    if len(argv) == 1:
        result_set = inner_level_q(float(argv[0]))
    else:
        result_set = inner_level_q(float(argv[0]), float(argv[1]))
    if len(result_set) > 50:
        await inner_level.finish(f"结果过多（{len(result_set)} 条），请缩小搜索范围。")
        return
    s = ""
    for elem in result_set:
        s += f"{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
    await inner_level.finish(s.strip())

search_music = on_regex(r"^查歌.+")

@search_music.handle()
async def _(event: Event, message: Message = EventMessage()):
    regex = "查歌(.+)"
    name = re.match(regex, str(message)).groups()[0].strip()
    if name == "":
        return
    res = total_list.filter(title_search=name)
    if len(res) == 0:
        await search_music.send("木得。")
    elif len(res) < 50:
        search_result = ""
        for music in sorted(res, key=lambda i: int(i['id'])):
            search_result += f"{music['id']}. {music['title']}\n"
        await search_music.finish(Message([
            MessageSegment("text", {
                "text": search_result.strip()
            })]))
    else:
        await search_music.send(f"结果过多（{len(res)} 条），请缩小查询范围。")


query_chart = on_regex(r"^([绿黄红紫白]?)id([0-9]+)")


@query_chart.handle()
async def _(event: Event, message: Message = EventMessage()):
    regex = "([绿黄红紫白]?)id([0-9]+)"
    groups = re.match(regex, str(message)).groups()
    level_labels = ['绿', '黄', '红', '紫', '白']
    if groups[0] != "":
        try:
            level_index = level_labels.index(groups[0])
            level_name = ['Basic', 'Advanced', 'Expert', 'Master', 'Re: MASTER']
            name = groups[1]
            music = total_list.by_id(name)
            chart = music['charts'][level_index]
            ds = music['ds'][level_index]
            level = music['level'][level_index]
            file = f"https://www.diving-fish.com/covers/{get_cover_len4_id(music['id'])}.png"
            if len(chart['notes']) == 4:
                msg = f'''{level_name[level_index]} {level}({ds})
TAP: {chart['notes'][0]}
HOLD: {chart['notes'][1]}
SLIDE: {chart['notes'][2]}
BREAK: {chart['notes'][3]}
谱师: {chart['charter']}'''
            else:
                msg = f'''{level_name[level_index]} {level}({ds})
TAP: {chart['notes'][0]}
HOLD: {chart['notes'][1]}
SLIDE: {chart['notes'][2]}
TOUCH: {chart['notes'][3]}
BREAK: {chart['notes'][4]}
谱师: {chart['charter']}'''
            await query_chart.send(Message([
                MessageSegment("text", {
                    "text": f"{music['id']}. {music['title']}\n"
                }),
                MessageSegment("image", {
                    "file": f"{file}"
                }),
                MessageSegment("text", {
                    "text": msg
                })
            ]))
        except Exception:
            await query_chart.send("未找到该谱面")
    else:
        name = groups[1]
        music = total_list.by_id(name)
        try:
            file = f"https://www.diving-fish.com/covers/{get_cover_len4_id(music['id'])}.png"
            await query_chart.send(Message([
                MessageSegment("text", {
                    "text": f"{music['id']}. {music['title']}\n"
                }),
                MessageSegment("image", {
                    "file": f"{file}"
                }),
                MessageSegment("text", {
                    "text": f"艺术家: {music['basic_info']['artist']}\n分类: {music['basic_info']['genre']}\nBPM: {music['basic_info']['bpm']}\n版本: {music['basic_info']['from']}\n难度: {'/'.join(music['level'])}"
                })
            ]))
        except Exception:
            await query_chart.send("未找到该乐曲")

query_score = on_command('分数线')


@query_score.handle()
async def _(event: Event, message: Message = CommandArg()):
    r = "([绿黄红紫白])(id)?([0-9]+)"
    argv = str(message).strip().split(" ")
    if len(argv) == 1 and argv[0] == '帮助':
        s = '''此功能为查找某首歌分数线设计。
命令格式：分数线 <难度+歌曲id> <分数线>
例如：分数线 紫799 100
命令将返回分数线允许的 TAP GREAT 容错以及 BREAK 50落等价的 TAP GREAT 数。
以下为 TAP GREAT 的对应表：
GREAT/GOOD/MISS
TAP\t1/2.5/5
HOLD\t2/5/10
SLIDE\t3/7.5/15
TOUCH\t1/2.5/5
BREAK\t5/12.5/25(外加200落)'''
        await query_score.send(Message([
            MessageSegment("image", {
                "file": f"base64://{str(image_to_base64(text_to_image(s)), encoding='utf-8')}"
            })
        ]))
    elif len(argv) == 2:
        try:
            grp = re.match(r, argv[0]).groups()
            level_labels = ['绿', '黄', '红', '紫', '白']
            level_labels2 = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
            level_index = level_labels.index(grp[0])
            chart_id = grp[2]
            line = float(argv[1])
            music = total_list.by_id(chart_id)
            chart: Dict[Any] = music['charts'][level_index]
            tap = int(chart['notes'][0])
            slide = int(chart['notes'][2])
            hold = int(chart['notes'][1])
            touch = int(chart['notes'][3]) if len(chart['notes']) == 5 else 0
            brk = int(chart['notes'][-1])
            total_score = 500 * tap + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            await query_chart.send(f'''{music['title']} {level_labels2[level_index]}
分数线 {line}% 允许的最多 TAP GREAT 数量为 {(total_score * reduce / 10000):.2f}(每个-{10000 / total_score:.4f}%),
BREAK 50落(一共{brk}个)等价于 {(break_50_reduce / 100):.3f} 个 TAP GREAT(-{break_50_reduce / total_score * 100:.4f}%)''')
        except Exception:
            await query_chart.send("格式错误，输入“分数线 帮助”以查看帮助信息")


best_40_pic = on_command('b40')

@best_40_pic.handle()
async def _(event: Event, message: Message = CommandArg()):
    username = str(message).strip()
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    img, success = await generate(payload)
    if success == 400:
        await best_40_pic.send("未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。")
    elif success == 403:
        await best_40_pic.send("该用户禁止了其他人获取数据。")
    else:
        await best_40_pic.send(Message([
            MessageSegment("image", {
                "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
            })
        ]))


best_40_simple = on_command('sb40')
@best_40_simple.handle()
async def _(event: Event, message: Message = CommandArg()):
    username = str(message).strip()
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    img, success = await generate_simple(payload)
    if success == 400:
        await best_40_simple.send("未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。")
    elif success == 403:
        await best_40_simple.send("该用户禁止了其他人获取数据。")
    else:
        await best_40_simple.send(Message([
            MessageSegment("image", {
                "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
            })
        ]))


best_50_pic = on_command('b50')
@best_50_pic.handle()
async def _():
    await best_50_pic.send("你查什么b50？")
