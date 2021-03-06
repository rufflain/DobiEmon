import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

import glob
from pathlib import Path
import os
import sys

import sqlite3
import json
import pickle

import datetime
import asyncio

import random

import emon_magics as dem
import emon_schedule as sch
import emon_music as music

# --------------------------------------------------

# Are you testing this bot?
is_testing = False
if is_testing:
    token_key = 'token_test'
    command_prefix = 't-'
else:
    token_key = 'token'
    command_prefix = '-'

# Information
with open('information.json') as json_file:
    json_data = json.load(json_file)
    TOKEN = str(json_data[token_key])
    SCHEDULE_CHANNEL_ID = int(json_data['schedule_channel_id'])
    SCHEDULE_NOTI_CHANNEL_ID = int(json_data['schedule_noti_channel_id'])
    OWNERS_ID = list(json_data['owners_id'])

# Settings
game = discord.Game("-도움말")
client = discord.Client()
bot = commands.Bot(command_prefix=command_prefix, status=discord.Status.online, activity=game,
                   help_command=None)

# Database
db = sqlite3.connect("dobiemon.db")

# Command Aliases - Pickle
with open('aliases.pickle', 'rb') as f:
    command_aliases = pickle.load(f)

# --------------------------------------------------


@bot.event
async def on_ready():
    print("봇 시작")


@bot.command(aliases=command_aliases['도움말'])
async def 도움말(ctx):
    await dem.send_embed(ctx, '도비에몽을 이용해 주시는 여러분!',
                         '도비에몽은 편의를 위해 여러 기능을 종합적으로 넣어 개발한 봇입니다.'
                         + ' 도비에몽의 다양한 기능에 대해 알고 싶다면, Notion에서 확인해 보세요.'
                         + '\n\n[도비에몽 Notion 페이지 바로가기]'
                         + '(https://www.notion.so/759bc6b62aba4a1f80a634581b646de8)')


# --------------------------------------------------


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


@bot.command()
async def 재시작(ctx):
    if str(ctx.message.author.id) not in OWNERS_ID:
        await dem.send_embed(ctx, "오류가 발생했습니다.",
                             "개발진만 실행할 수 있는 명령어입니다.")
        return
    await dem.send_embed(ctx, "봇을 재시작합니다.",
                         "<@" + str(ctx.message.author.id) + "> 님에 의해 봇이 재시작됩니다.")
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.command()
async def 종료(ctx):
    if str(ctx.message.author.id) not in OWNERS_ID:
        await dem.send_embed(ctx, "오류가 발생했습니다.",
                             "개발진만 실행할 수 있는 명령어입니다.")
        return
    await dem.send_embed(ctx, "봇을 종료합니다.",
                         "<@" + str(ctx.message.author.id) + "> 님에 의해 봇이 종료됩니다.")
    await bot.logout()


@bot.command()
async def 명령어(ctx, arg, command_str=None, name_str=None):
    if arg == '목록':
        embed = discord.Embed()
        for key in command_aliases:
            value_str = ''
            for val in command_aliases[key]:
                value_str += ", " + val
            embed.add_field(name="-" + key,
                            value="별명 : " + value_str[2:], inline=False)
        embed.set_footer(text="by 도비에몽")
        await ctx.send(embed=embed)
        return

    # --- Admin ---

    if str(ctx.message.author.id) not in OWNERS_ID:
        await dem.send_embed(ctx, "오류가 발생했습니다.",
                             "개발진만 실행할 수 있는 명령어입니다.")
        return

    try:
        command = command_aliases[command_str]
    except:
        await dem.send_embed(ctx, '오류가 발생했습니다.', '해당 명령어를 찾을 수 없습니다.')
        return

    with open('aliases.pickle', 'wb') as f:
        if arg == '추가':
            for key in command_aliases:
                if key == name_str:
                    await dem.send_embed(ctx, "추가하지 못했습니다.",
                                         "해당 별명은 이미 존재하는 명령어입니다.")
                    return
            for val in command_aliases.values():
                for alias in val:
                    if alias == name_str:
                        await dem.send_embed(ctx, "추가하지 못했습니다.",
                                             "해당 별명은 이미 존재하는 별명입니다.")
                        return
            command.append(name_str)
        elif arg == '삭제':
            try:
                idx_for_del = command.index(name_str)
            except ValueError:
                await dem.send_embed(ctx, '오류가 발생했습니다.', '해당 별명을 찾을 수 없습니다.')
                return
            del command[idx_for_del]
        pickle.dump(command_aliases, f)

    await dem.send_embed(ctx, '성공적으로 ' + arg + '되었습니다.',
                         arg + "된 내용 : \'" + command_str + "\' 명령어의 별명 \'" + name_str + "\'")


# --------------------------------------------------


def get_file(file_list, file_keyword):
    file_keyword = file_keyword.lower()
    correct_list = [file for file in file_list if file[0].lower().find(file_keyword) != -1]
    try:
        file = correct_list[0]
        file_path = Path(file[0] + file[1])
    except:
        return 'error: not found'
    return file_path


@bot.command(aliases=command_aliases['커져라'])
async def 커져라(ctx, *, image_keyword):
    image_list = glob.glob('./images/*')
    image_info_list = []
    for image in image_list:
        image_parts = Path(image).parts
        image_extension = Path(image_parts[1]).suffix
        image_name = image_parts[1].replace(image_extension, '')
        image_info_list.append((image_name, image_extension))
    image_path = get_file(image_info_list, image_keyword)

    if image_path == 'error: not found':
        await dem.send_embed(ctx, "오류가 발생했습니다.", "관련 이미지를 찾을 수 없습니다.")
    else:
        image_path = 'images' / image_path
        image = discord.File(image_path)
        embed = discord.Embed()
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        msg = await ctx.send(file=image)
        embed.set_image(url=msg.attachments[0].url)
        await ctx.send(embed=embed)
        await msg.delete()


@bot.command(aliases=command_aliases['오퍼'])
async def 오퍼(ctx, arg):
    # 0 : Attacker / 1 : Defender
    r6_operator = ''
    if arg == '공격':
        r6_op_a, r6_op_a_p = dem.db_to_list(db, 'R6_Operator', True, 'WHERE Type = 0')
        r6_operator = dem.random(r6_op_a, r6_op_a_p)
    elif arg == '수비':
        r6_op_d, r6_op_d_p = dem.db_to_list(db, 'R6_Operator', True, 'WHERE Type = 1')
        r6_operator = dem.random(r6_op_d, r6_op_d_p)

    if r6_operator == '':
        await dem.send_embed(ctx, "올바른 형식이 아닙니다.", "도움말을 참조해 다시 입력해 주세요.")
    else:
        await dem.send_embed(ctx, "추천하는 오퍼레이터는...",
                             r6_operator + "입니다." +
                             "\n<@" + str(ctx.author.id) + ">")


@bot.command(aliases=command_aliases['메뉴'])
async def 메뉴(ctx):
    menu, menu_p = dem.db_to_list(db, 'Menu', True)
    menu_final = dem.random(menu, menu_p)
    await dem.send_embed(ctx, "추천하는 메뉴는...", menu_final + "입니다."
                         + "\n<@" + str(ctx.author.id) + ">")


@bot.command(aliases=command_aliases['식당'])
async def 식당(ctx):
    # 0 : Basic / 1 : Far / 2 : Your House
    res_rows = dem.db_to_list(db, 'Restaurant', False)
    restaurant = []
    restaurant_p = []
    for row in res_rows:
        restaurant.append((row[1], row[3]))
        restaurant_p.append(row[2])
    res_rand = dem.random(len(restaurant), restaurant_p)
    res_final = restaurant[res_rand][0]
    res_extra_message = ''
    if restaurant[res_rand][1] == 2:
        res_extra_message = "메뉴는 파워에이드 라면만 허용해요."
    elif restaurant[res_rand][1] == 1:
        res_extra_message = "가서 식사만 하고 돌아오는 거에요."

    if bool(res_extra_message):
        res_extra_message = "\n" + res_extra_message

    await dem.send_embed(ctx, "추천하는 식당은...", res_final + "입니다." + res_extra_message
                         + "\n<@" + str(ctx.author.id) + ">")


@bot.command(aliases=command_aliases['일정'])
async def 일정(ctx, cmd_arg, schedule_arg=''):
    schedule_channel = bot.get_channel(SCHEDULE_CHANNEL_ID)
    if cmd_arg == '추가':
        await dem.send_embed(ctx, "일정 추가를 시작합니다.",
                             "추가하고 싶은 일정 이름, 일정 날짜(YYYYMMDD), 일정 시각(HHMM) 순으로 띄어쓰기로 구분해 적어주세요."
                             + " 그리고 이 일정을 반복하고 싶다면, 마지막에 반복 주기를 일(day) 단위로 적어 주세요."
                             + "\n작성 예시 : 일퀘 20210104 1900 1"
                             + "\n일정을 반복하고 싶지 않다면 마지막을 적지 않고 시각까지만 작성하면 됩니다."
                             + "\n예시 : 라라코스트모임 20210104 1800")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            add_message = await bot.wait_for('message', check=check, timeout=60.0)
            message_str = add_message.content
        except asyncio.TimeoutError:
            await dem.send_embed(ctx, "입력 시간이 초과되었습니다.", "60초 내에 입력하지 않아 취소되었습니다.")
            return

        try:
            if len(message_str.split()) == 3:
                schedule_arg, date_arg, time_arg = message_str.split()
                repeat = 0
            else:
                schedule_arg, date_arg, time_arg, repeat = message_str.split()
        except ValueError:
            await dem.send_embed(ctx, "오류가 발생했습니다.",
                                 "형식에 맞지 않게 입력되었습니다.")
            return

        schedule_datetime_tmp = datetime.datetime.strptime(date_arg + '-' + time_arg, '%Y%m%d-%H%M')
        await sch.add_schedule(db, schedule_datetime_tmp, schedule_arg, repeat, bot)
        repeat_str = ''
        if int(repeat) > 0:
            repeat_str += "\n일정 반복 주기 : " + str(repeat) + "일"
        await dem.send_embed(ctx, "일정 알림이 추가되었습니다.",
                             "일정 이름 : " + schedule_arg + "\n"
                             + "일정 일시 : " + schedule_datetime_tmp.strftime('%Y-%m-%d %H:%M')
                             + repeat_str)

    elif cmd_arg == '삭제':
        sch_rows = dem.db_to_list(db, 'Schedule', False)
        for row in sch_rows:
            if row[1] == schedule_arg:
                await dem.send_embed(ctx, "일정 삭제가 완료되었습니다.",
                                     "삭제한 일정 이름 : " + row[1] + "\n"
                                     + "삭제한 일정 일시 : " + row[2] + "\n"
                                     + "삭제한 일정 반복 주기 : " + str(row[4]) + "\n\n"
                                     + "기존 일정 추가 알림 메시지는 삭제됩니다.")
                await sch.del_schedule_by_idx(db, row[0], row[3], bot)

    elif cmd_arg == '목록':
        sch_rows = dem.db_to_list(db, 'Schedule', False)
        if not sch_rows:
            await dem.send_embed(ctx, "현재 등록된 일정이 없습니다.",
                                 "새로운 일정을 등록해 삶의 질을 높여 보세요.")
            return
        embed = discord.Embed()
        for row in sch_rows:
            embed.add_field(name=row[1], value='다음 알림 예정 일시: ' + row[2] + "\n반복 주기: " + str(row[4]))
        await ctx.send(embed=embed)

    elif cmd_arg == '수정':
        sch_rows = dem.db_to_list(db, 'Schedule', False)
        for row in sch_rows:
            if row[1] == schedule_arg:
                await dem.send_embed(ctx, "선택한 일정의 정보는 다음과 같습니다.",
                                     "일정 이름 : " + row[1] + "\n"
                                     + "일정 일시 : " + row[2] + "\n"
                                     + "일정 반복 주기 : " + str(row[4]) + "\n\n"
                                     + "여기서 이름, 일시, 주기 순으로 수정할 내용을 띄어쓰기로 구분해 입력해 주세요."
                                     + " 수정하지 않을 부분은 '그대로' 라고 적어주세요."
                                     + " 그리고 일시는 YYYYMMDD-HHMM의 형식으로 적어 주세요."
                                     + "\n입력 예시 : 내생일 20210102-0100 그대로")

                # wait for message
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    modify_message = await bot.wait_for('message', check=check, timeout=60.0)
                    message_str = modify_message.content
                except asyncio.TimeoutError:
                    await dem.send_embed(ctx, "입력 시간이 초과되었습니다.", "60초 내에 입력하지 않아 취소되었습니다.")
                    return

                # message to data
                try:
                    after_name, after_dt, after_rp = message_str.split()
                except ValueError:
                    await dem.send_embed(ctx, "오류가 발생했습니다.",
                                         "형식에 맞지 않게 입력되었습니다.")
                    return

                after_dt = datetime.datetime.strptime(after_dt, '%Y%m%d-%H%M')
                after_dt = after_dt.strftime('%Y-%m-%d %H:%M')

                await sch.modify_schedule_by_idx(db, after_name, after_dt, after_rp,
                                                 row, bot, ctx)

                return

    else:
        await dem.send_embed(ctx, '오류가 발생했습니다.', '일정 관련 명령어 입력이 잘못되었습니다.')


@bot.command(aliases=command_aliases['소라고둥'])
async def 소라고둥(ctx, arg1, arg2):
    srgd = dem.random([arg1, arg2], [0.5, 0.5])
    await dem.send_embed(ctx, "둘 중에서...", srgd + " 선택해.", "by 마법의 소라고둥 in 도비에몽")


@bot.command(aliases=command_aliases['처벌'])
async def 처벌(ctx):
    ban_list = ['2초', '5초', '10초', '1분', '2분', '5분', '10분', '15분', '30분', '1시간', '용서']
    ban_list_p = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05]
    ban_result = dem.random(ban_list, ban_list_p)
    await dem.send_embed(ctx, "이번 사건은...", ban_result + ".")


@bot.command(aliases=command_aliases['음악'])
async def 음악(ctx, *, music_keyword):
    if music_keyword == '목록':
        music_queue = music.get_queue()
        embed = discord.Embed()
        for idx, track in enumerate(music_queue):
            if idx == 0:
                embed.add_field(name="0번째 [현재 재생중]:",
                                value=track.get_title(), inline=False)
            else:
                embed.add_field(name=str(idx) + "번째:",
                                value=track.get_title(), inline=False)
        await ctx.send(embed=embed)
        return

    guild = ctx.guild
    voice_client: discord.VoiceClient = guild.voice_client

    music_list = glob.glob('./musics/*')
    music_info_list = []
    for music_file in music_list:
        music_parts = Path(music_file).parts
        music_extension = Path(music_parts[1]).suffix
        music_name = music_parts[1].replace(music_extension, '')
        music_info_list.append((music_name, music_extension))
    music_path = get_file(music_info_list, music_keyword)

    if music_path == 'error: not found':
        await dem.send_embed(ctx, "오류가 발생했습니다.", "관련 음악을 찾을 수 없습니다.")
    else:
        music_path = 'musics' / music_path
        if not voice_client:
            channel = ctx.author.voice.channel
            await channel.connect()
        music_for_add = music.Track(music_path)
        music.add_queue(music_for_add)
        await dem.send_embed(ctx, '음악이 대기 목록에 추가되었습니다.',
                             '추가된 음악 : ' + music_for_add.get_title() +
                             '\n대기열 순서에 따라 재생됩니다.')
        await music.play_music(ctx, bot)


@bot.command(aliases=command_aliases['퇴장'])
async def 퇴장(ctx):
    guild = ctx.guild
    voice_client: discord.VoiceClient = guild.voice_client
    if not voice_client:
        await dem.send_embed(ctx, '오류가 발생했습니다.', '저는 이미 어느 채널에도 들어가 있지 않습니다.')
        return
    music.clean_queue()
    await voice_client.disconnect()


@bot.command(aliases=command_aliases['스킵'])
async def 스킵(ctx):
    music.skip_music(ctx, bot)


@bot.command(aliases=command_aliases['추방투표'])
async def 추방투표(ctx, vote_user_mention):
    vote_member = ctx.message.mentions[0]

    agree_emoji = '\U0001F44D'
    disagree_emoji = '\U0001F44E'
    waiting_time = 30
    vote_message = await dem.send_embed(ctx, '추방 투표가 시작됩니다.',
                                        '<@' + str(ctx.message.author.id) + '> 님이\n'
                                        + vote_user_mention + ' 님에 대한 추방 투표를 열었습니다.'
                                        + '\n\n찬성하시면, ' + str(waiting_time) +
                                        '초 내에 이 메시지에 반응 ' + agree_emoji + ' 을 달아 주세요.'
                                        + '\n반대하시면, ' + disagree_emoji + ' 을 달아 주세요.')
    await vote_message.add_reaction(agree_emoji)
    await vote_message.add_reaction(disagree_emoji)
    await asyncio.sleep(waiting_time)

    vote_message_fetch = await ctx.fetch_message(vote_message.id)
    agree_users_list = await dem.check_reaction_users(vote_message_fetch, agree_emoji)
    disagree_users_list = await dem.check_reaction_users(vote_message_fetch, disagree_emoji)

    # deduplication between agree users and disagree users
    real_agree_users = []
    for agree in agree_users_list:
        is_duplicated = False
        agree_user = await bot.fetch_user(agree)
        for disagree in disagree_users_list:
            if agree == disagree:
                is_duplicated = True
        if not is_duplicated and not agree_user.bot:
            real_agree_users.append(agree)

    real_disagree_users = []
    for disagree in disagree_users_list:
        disagree_user = await bot.fetch_user(disagree)
        if not disagree_user.bot:
            real_disagree_users.append(disagree)

    agrees = len(real_agree_users)
    disagrees = len(real_disagree_users)
    if agrees > disagrees:
        await dem.send_embed(ctx, '추방하는 것으로 결정되었습니다.',
                             vote_user_mention + ' 님의 추방이 찬성 ' + str(agrees) + '표,'
                             + "\n반대 " + str(disagrees) + "표로 가결되었습니다.")
        try:
            await vote_member.move_to(ctx.guild.afk_channel)
        except:
            await dem.send_embed(ctx, '오류가 발생했습니다.', '보내려는 유저를 잠수 채널로 보낼 수 없습니다.')
    else:
        await dem.send_embed(ctx, '추방하지 않는 것으로 결정되었습니다.',
                             vote_user_mention + ' 님의 추방이 찬성 ' + str(agrees) + '표,'
                             + "\n반대 " + str(disagrees) + "표로 부결되었습니다.")


@bot.command(aliases=command_aliases['룰렛'])
async def 룰렛(ctx):
    agree_emoji = '\U0001F44D'
    waiting_time = 30
    vote_message = await dem.send_embed(ctx, '러시안 룰렛이 시작됩니다!',
                                        '<@' + str(ctx.message.author.id) + '> 님이\n'
                                        + '러시안 룰렛을 시작했습니다.'
                                        + '\n\n참여를 원하시면, ' + str(waiting_time)
                                        + '초 내에 이 메시지에 반응 ' + agree_emoji + ' 을 달아 주세요.'
                                        + '\n종료 시점에 음성 채널에 들어가 있지 않은 분은 제외됩니다.')
    await vote_message.add_reaction(agree_emoji)
    await asyncio.sleep(waiting_time)

    vote_message_fetch = await ctx.fetch_message(vote_message.id)
    agree_users_list = await dem.check_reaction_users(vote_message_fetch, agree_emoji)

    real_agree_users = []
    for agree in agree_users_list:
        agree_member = await ctx.guild.fetch_member(agree)
        if not agree_member.bot and agree_member.voice:
            real_agree_users.append(agree)

    selected_user_id = dem.random(real_agree_users, None)
    await dem.send_embed(ctx, '러시안 룰렛 당첨자가 결정되었습니다!',
                         '<@' + str(selected_user_id) + '> 님이\n'
                         + '러시안 룰렛의 당첨자가 되셨습니다.')

    try:
        selected_member = await ctx.guild.fetch_member(selected_user_id)
        await selected_member.move_to(ctx.guild.afk_channel)
    except:
        await dem.send_embed(ctx, '오류가 발생했습니다.', '보내려는 유저를 잠수 채널로 보낼 수 없습니다.')


@bot.command(aliases=command_aliases['팀'])
async def 팀(ctx):
    agree_emoji = '\U0001F44D'
    waiting_time = 30
    vote_message = await dem.send_embed(ctx, '팀 배정이 시작됩니다.',
                                        '<@' + str(ctx.message.author.id) + '> 님이\n'
                                        + '팀 배정을 시작했습니다.'
                                        + '\n\n참여를 원하시면, ' + str(waiting_time)
                                        + '초 내에 이 메시지에 반응 ' + agree_emoji + ' 을 달아 주세요.')
    await vote_message.add_reaction(agree_emoji)
    await asyncio.sleep(waiting_time)

    vote_message_fetch = await ctx.fetch_message(vote_message.id)
    agree_users_list = await dem.check_reaction_users(vote_message_fetch, agree_emoji)

    real_agree_users = []
    for agree in agree_users_list:
        agree_user = await bot.fetch_user(agree)
        if not agree_user.bot:
            real_agree_users.append(agree)

    agrees = len(real_agree_users)
    red_teams = agrees // 2

    random.shuffle(real_agree_users)
    red_team = real_agree_users[:red_teams]
    blue_team = real_agree_users[red_teams:]

    red_team_str = ''
    for user_id in red_team:
        red_team_str += ' <@' + str(user_id) + '>'
    blue_team_str = ''
    for user_id in blue_team:
        blue_team_str += ' <@' + str(user_id) + '>'

    red_team_str = red_team_str[1:]
    blue_team_str = blue_team_str[1:]

    await dem.send_embed(ctx, '팀 배정이 완료되었습니다.',
                         '[레드 팀]\n' + red_team_str
                         + '\n\n[블루 팀]\n' + blue_team_str)


# --------------------------------------------------

bot.loop.create_task(sch.scheduler(db, bot))
bot.run(TOKEN)
