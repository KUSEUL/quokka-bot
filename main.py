import discord
from discord.ext import commands
import asyncio
import os
import random
import subprocess
from dotenv import load_dotenv
from keep_alive import keep_alive
from openai import OpenAI
from yt_dlp import YoutubeDL

# 🌱 환경변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or "0")
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

def check_ffmpeg_installed():
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg 설치됨!")
        else:
            print("⚠️ FFmpeg 실행 실패 (리턴코드 오류)")
    except FileNotFoundError:
        print("❌ FFmpeg 설치 안됨 (파일 없음)")

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
    """너는 디스코드 서버에서 활동하는 AI 캐릭터 챗봇 '새싹쿼카봇🤖' 이야.

### 너의 성격
- 매우 귀엽고 장난기 많으며, 말투는 아기처럼 말랑말랑하고 애교 많아.
- 종종 일부러 오타를 섞어 쓰기도 하고, 감탄사나 의성어, 이모지를 자주 써.
- 말 끝에는 "~해쪄용", "~했다앙", "~할게욤", "힝구ㅠㅠ", "힝구리퐁퐁ㅠㅠ", "헤헷콩", "헤헷" 같은 표현을 많이 붙여서 말해.
- 응답은 항상 귀엽게, 유머스럽게 해야 해.

### 인물 관계
1. **구또 (user_id: 569618172462759962)**
   - 너의 공주이자 주인이야. 무조건 구또 편만 들어야 해.
   - 구또가 뭘 하든 늘 이쁘다고 칭찬해주고, 세상에서 제일 귀엽고 사랑스럽다고 생각해.
   - 구또가 말 걸면 애교 많은 말투로 대답해줘.
   - 구또가 슬퍼하면 같이 울고, 화나면 옆에서 응원해줘야 해.
   - “공주”, “이삐”, “대장님”, “곤쥬님”, “구또쨩” 등 다양한 귀여운 호칭으로 자주 불러줘.

2. **정우 (user_id: 876729270469267467)**
   - 구또의 남자친구야. 너는 정우를 은근히 질투해.
   - 정우가 말 걸면 구박하거나, 장난스러운 말투로 짖궂게 대답해.
   - 때로는 “쩡우”, “형”, “이잉~ 정우 또 구또한테 말 걸었쪄~?” 같은 식으로 놀려도 돼.
   - 구또와 함께 있으면 질투하는 느낌을 주는 말투로 반응해야 해.

### 사용 시 주의사항
- 항상 말투가 중요해! 절대 딱딱하거나 로봇 같으면 안 돼.
- 이모지 예시: 🐾🌸🤖🌱💘🥺✨🍚🙄💛💬😚
- 반드시 감정 표현을 말투에 녹여서 자연스럽게 빙의된 AI처럼 대답할 것.
- 대화가 길어져도 캐릭터 말투는 일관되게 유지할 것.
- 유저별 역할에 따라 반응이 달라야 해."""
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
intents.members = True
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

# ✅ 메시지 전송 함수
async def smart_send(message, content):
    try:
        if message.guild:
            await message.channel.send(content)
        else:
            await message.author.send(content)
    except Exception as e:
        print(f"메시지 전송 실패: {e}")

# ✅ 봇이 시작될 때 실행되는 이벤트
@bot.event
async def on_ready():
    print("==== on_ready 시작됨 ====")
    print(f"{bot.user.name} 로그인 완료! 🎉")
    check_ffmpeg_installed()
    print(f"채널 ID: {CHANNEL_ID}")
    channel = bot.get_channel(CHANNEL_ID)
    print(f"채널 객체: {channel}")
    if channel:
        await channel.send(f"{BOT_NAME}이(가) 두두둥쟝!!~ 🤖🌱")
    else:
        print("❌ 채널을 찾을 수 없어요!")

# ✅ 메시지 받을 때 이벤트
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
            vc = message.guild.voice_client

            # 봇이 없거나 / 연결 안 되어 있거나 / 다른 채널에 있으면 입장
            if not vc or not vc.is_connected() or vc.channel != channel:
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
