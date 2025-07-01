import discord
from discord.ext import commands
import asyncio
import os
import json
import random
from dotenv import load_dotenv
from keep_alive import keep_alive
from openai import OpenAI
from yt_dlp import YoutubeDL

# 환경변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
BOT_NAME = os.getenv("BOT_NAME", "새싹쿼카봇🤖")

# OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)

# 사용자 데이터
USER_DATA_FILE = "users.json"
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({}, f)

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def remember_user(user_id, name):
    data = load_user_data()
    data[str(user_id)] = {"name": name}
    save_user_data(data)

def get_user_name(user_id):
    data = load_user_data()
    return data.get(str(user_id), {}).get("name")

# 역할 ID
OWNER_ID = 569618172462759962  # 구또
BOYFRIEND_ID = 876729270469267467  # 쩡우

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

music_queue = []
current_vc = None

def search_youtube(query):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True', 'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            return info['url'], info['title']
        except Exception as e:
            print(f"검색 실패: {e}")
            return None, None

async def play_music(vc):
    global music_queue
    if not music_queue:
        await vc.disconnect()
        return

    url, title = music_queue.pop(0)
    with YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2, options='-vn')
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_music(vc), bot.loop))

async def smart_send(message, content):
    try:
        if message.guild:
            await message.channel.send(content)
        else:
            await message.author.send(content)
    except Exception as e:
        print(f"메시지 전송 실패: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user.name} 로그인 완료! 🎉")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"{BOT_NAME}이(가) 두두둥쟝!!~ 🤖🌱")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower().strip()
    user_id = message.author.id
    user_name = get_user_name(user_id)

    if msg.startswith("난 "):
        new_name = msg.replace("난 ", "").strip()
        remember_user(user_id, new_name)
        await smart_send(message, f"알게쏘! {new_name}! 기억할게용~ 😊")
        return

    if ("들어와" in msg and message.author.voice):
        try:
            channel = message.author.voice.channel
            print(f"연결 시도 채널: {channel}")
            if not message.guild.voice_client:
                await channel.connect()
                await smart_send(message, "쿼카 입장했따앙~🐾")
            else:
                await smart_send(message, "이미 들어와있쪄용~😚")
        except Exception as e:
            print("입장 오류:", e)
            await smart_send(message, "입장 실패했쪄용ㅠㅠ")

    if "나가" in msg or "꺼져" in msg:
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await smart_send(message, "쿼카 퇴장했어용~👋")
        else:
            await smart_send(message, "지금은 음성 채널에 없쪄용~😗")
        return

    if "노래 틀어" in msg or "음악 틀어" in msg:
        query = msg.replace("노래 틀어줘", "").replace("음악 틀어줘", "").replace("노래 틀어", "").replace("음악 틀어", "").strip()
        if not query:
            await smart_send(message, "무슨 노래 틀까용~? 🎶")
            return
        if message.author.voice:
            channel = message.author.voice.channel
            vc = message.guild.voice_client or await channel.connect()
            url, title = search_youtube(query)
            if url:
                music_queue.append((url, title))
                await smart_send(message, f"대기열 추가했쪄용~ 🎶 {title}")
                if not vc.is_playing():
                    await play_music(vc)
            else:
                await smart_send(message, "노래 검색 실패했어용ㅠㅠ")
        else:
            await smart_send(message, "먼저 음성 채널에 들어가쏘~!")
        return

    if "멈춰" in msg and message.guild.voice_client and message.guild.voice_client.is_playing():
        message.guild.voice_client.pause()
        await smart_send(message, "멈췄어용~⏸️")
        return

    if "다시 틀어" in msg and message.guild.voice_client and message.guild.voice_client.is_paused():
        message.guild.voice_client.resume()
        await smart_send(message, "다시 고고!!~▶️")
        return

    if "다음 노래" in msg or "스킵" in msg:
        if message.guild.voice_client and message.guild.voice_client.is_playing():
            message.guild.voice_client.stop()
            await smart_send(message, "다음 곡으로 점프해쪄용~⏭️")
        else:
            await smart_send(message, "지금 재생 중인 곡이 없쪄용~😗")
        return

    if "말해" in msg or "쿼카야 뭐해" in msg or "놀자" in msg:
        messages = [
            "공주 근데 왜케 이뻐용? 헤헷콩~🌸", "구또밖에 몰라용~ 힝구ㅠㅠ",
            "쩡우! 또 구또랑 말했쪄? 질투나쟈냐~🙄", "구또는 세상에서 쩰 귀여워요~💛",
            "아잉~ 구또당~ 부끄부끄해~🥺", "새싹쿼카 왔다앗~ 🌱 두둥쟝!!",
            "곤쥬~ 왜케 이뽀요??~✨", "이삐야 밥 먹었어용? 냠냠!!🍚",
            "내 심장은 구또의 것이다!! 헤헷콩~💘"
        ]
        await smart_send(message, random.choice(messages))
        return

    # 기본 대화 처리 생략 가능 (GPT 응답 처리 등)

    await bot.process_commands(message)

keep_alive()
bot.run(DISCORD_TOKEN)
