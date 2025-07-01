import discord
from discord.ext import commands
import asyncio
import os
import random
from dotenv import load_dotenv
from keep_alive import keep_alive
from openai import OpenAI
from yt_dlp import YoutubeDL

# 🌱 환경변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
BOT_NAME = os.getenv("BOT_NAME", "새싹쿼카봇🤖")

# 🌱 OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)

# 🌱 유저 ID
OWNER_ID = 569618172462759962  # 구또
BOYFRIEND_ID = 876729270469267467  # 정우

# 🌱 이름 저장
user_names = {
    str(OWNER_ID): "구또",
    str(BOYFRIEND_ID): "정우"
}

# 🌱 히스토리 저장
user_histories = {}
MAX_HISTORY = 5

def update_user_history(user_id, role, content):
    uid = str(user_id)
    if uid not in user_histories:
        user_histories[uid] = []
    user_histories[uid].append({"role": role, "content": content})
    user_histories[uid] = user_histories[uid][-MAX_HISTORY:]

def ask_gpt(user_id, user_input):
    try:
        uid = str(user_id)
        history = user_histories.get(uid, [])

        messages = [{
            "role": "system",
            "content": (
                "너는 디스코드용 챗봇 '새싹쿼카봇🤖'이야. 성격은 귀엽고 장난기 많아.\n"
                "'구또'(569618172462759962)는 너의 공주님이자 주인이야. 항상 구또 편만 들고 애교 섞인 말투로 응답해.\n"
                "'정우'(876729270469267467)는 구또의 남자친구인데, 가끔 질투하고 구박하는 말투로 대해야 해.\n"
                "말투는 '~쪄용', '~했따앙', '힝구ㅠㅠ', '헤헷콩' 같은 귀엽고 장난스러운 말투를 섞어서 자연스럽게 사용하고, 이모지도 자주 써줘."
            )
        }]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        update_user_history(user_id, "user", user_input)
        update_user_history(user_id, "assistant", reply)
        return reply or "힝구ㅠㅠ 대답이 안 나왔어용!"
    except Exception as e:
        return f"GPT 오류가 났어용ㅠㅠ: {e}"

# 🌱 이미지 생성 함수 (DALL·E 사용)
async def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        print(f"이미지 생성 실패: {e}")
        return None

# 🌱 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="", intents=intents)

music_queue = []

def search_youtube(query):
    options = {'format': 'bestaudio', 'noplaylist': 'True', 'quiet': True}
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            return info['url'], info['title']
        except Exception as e:
            print(f"검색 실패: {e}")
            return None, None

async def play_music(vc):
    global music_queue
    if not music_queue:
        if vc:
            await vc.disconnect()
        return
    url, title = music_queue.pop(0)
    with YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
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
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    msg = message.content.lower().strip()
    user_id = message.author.id

    if msg.startswith("난 "):
        name = msg.replace("난 ", "").strip()
        user_names[str(user_id)] = name
        await smart_send(message, f"알게쏘! {name} 기억할게용~ 🐾")
        return

    # 음성채널 입장
    if ("들어와" in msg and message.author.voice):
        try:
            channel = message.author.voice.channel
            if not message.guild.voice_client:
                await channel.connect()
                await smart_send(message, "쿼카 입장했따앙~🐾")
            else:
                await smart_send(message, "이미 들어와있쪄용~😚")
        except Exception as e:
            print("입장 오류:", e)
            await smart_send(message, "입장 실패했쪄용ㅠㅠ")
        return

    if "나가" in msg or "꺼져" in msg:
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await smart_send(message, "쿼카 퇴장했어용~👋")
        else:
            await smart_send(message, "지금 음성 채널에 없쪄용~😗")
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

    if "멈춰" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await smart_send(message, "멈췄어용~⏸️")
        return

    if "다시 틀어" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await smart_send(message, "다시 고고!!~▶️")
        return

    if "다음 노래" in msg or "스킵" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await smart_send(message, "다음 곡으로 점프해쪄용~⏭️")
        else:
            await smart_send(message, "지금 재생 중인 곡이 없쪄용~😗")
        return

    # 🖼 이미지 생성 명령어
    if "그려줘" in msg or "그림" in msg or "사진 만들어" in msg:
        prompt = message.content.replace("그려줘", "").replace("그림", "").replace("사진 만들어", "").strip()
        if not prompt:
            await smart_send(message, "무슨 그림 그릴까용~? 🎨")
            return
        await smart_send(message, f"그림 만드는 중이쪄용~🖌️ '{prompt}'...")
        image_url = await generate_image(prompt)
        if image_url:
            await message.channel.send(image_url)
        else:
            await smart_send(message, "이미지 생성 실패했어용ㅠㅠ")
        return

    # 자동반응
    if any(kw in msg for kw in ["말해", "쿼카야 뭐해", "놀자"]):
        messages = [
            "공주 근데 왜케 이뻐용? 헤헷콩~🌸", "구또밖에 몰라용~ 힝구ㅠㅠ",
            "쩡우! 또 구또랑 말했쪄? 질투나쟈냐~🙄", "구또는 세상에서 쩰 귀여워요~💛",
            "아잉~ 구또당~ 부끄부끄해~🥺", "새싹쿼카 왔다앗~ 🌱 두둥쟝!!",
            "곤쥬~ 왜케 이뽀요??~✨", "이삐야 밥 먹었어용? 냠냠!!🍚",
            "내 심장은 구또의 것이다!! 헤헷콩~💘"
        ]
        await smart_send(message, random.choice(messages))
        return

    # 🧠 GPT 응답
    reply = ask_gpt(user_id, message.content)
    await smart_send(message, reply)

# 🌱 Replit 유지용
keep_alive()

# 🌱 실행
bot.run(DISCORD_TOKEN)
