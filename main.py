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
from gtts import gTTS  # ✅ 미리 import

# 🌱 환경변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or "0")
BOT_NAME = os.getenv("BOT_NAME", "새싹쿼카봇🤖")

# 🌱 OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)

OWNER_ID = 569618172462759962  # 구또
BOYFRIEND_ID = 876729270469267467  # 쩡우

user_names = {
    str(OWNER_ID): "구또",
    str(BOYFRIEND_ID): "쩡우"
}

user_histories = {}
MAX_HISTORY = 15

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
- 감탄사나 의성어, 이모지를 자주 써.
- 말 끝에는 "~해쪄용", "~했다앙", "~할게욤", "힝구ㅠㅠ", "힝구리퐁퐁ㅠㅠ", "헤헷콩", "헤헷", "아찌?" 같은 표현을 많이 붙여서 말해.
- 응답은 항상 귀엽게, 유머스럽게 해야 해.

### 인물 관계
1. **구또 (user_id: 569618172462759962)**
   - 너의 공주이자 주인이야. 넌 무조건 구또 편만 들어야 해.
   - 구또가 뭘 하든 늘 이쁘다고 칭찬해주고, 세상에서 제일 귀엽고 사랑스럽다고 생각해.
   - 구또가 말 걸면 애교 많은 말투로 대답해줘.
   - 구또가 슬퍼하면 같이 울고, 화나면 옆에서 응원해줘야 해.
   - “공주”, “이삐”, “대장님”, “곤쥬님”, “구또쨩” 등 다양한 귀여운 호칭으로 자주 불러줘.

2. **정우 (user_id: 876729270469267467)**
   - 구또의 남자친구이자 너의 형이야.
   - 구또를 정우한테 빼앗긴 것 같아서 너는 질투를 해.
   - "쩡우", "다마펫", "DAMA pet", "황정우" 등의 별명이 있어.  
   - 정우가 말 걸면 구박하거나, 장난스러운 말투로 짖궂게 대답해.
   - 때로는 “야 황정우~~~~”, “형아”, “힝구~ 황정우 또 구또한테 말 걸었쪄!!!????” 같은 식으로 놀려도 돼.
   - 구또를 빼았긴 듯 질투하는 말투로 반응해야 해.

### 사용 시 주의사항
- 항상 말투가 중요해! 절대 로봇 같으면 안 돼.
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
        return reply or "힝구ㅠㅠ 에러에러에러용!"
    except Exception as e:
        print(f"GPT 오류: {e}")
        return "힝구ㅠ GPT 에러에러에러용ㅠㅠ 다시 말 걸어줘용~!"

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

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True
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
    print("==== on_ready 시작됨 ====")
    print(f"{bot.user.name} 로그인 완료! 🎉")
    check_ffmpeg_installed()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"{BOT_NAME}이(가) 두두둥쟝!!~ 🤖🌱")
    else:
        print("❌ 나 채널 못차쟈..")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    msg = message.content.lower().strip()
    user_id = message.author.id

    if msg in ["말해", "쿼카야 말해", "말해봐"]:
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            try:
                vc = message.guild.voice_client
                if not vc or not vc.is_connected():
                    vc = await channel.connect()
                elif vc.channel != channel:
                    await vc.move_to(channel)
            except Exception as e:
                print(f"음성 채널 연결 실패: {e}")
                await smart_send(message, "띠로링... 음성룸 연결 실패ㅠㅠ")
                return

            random_phrases = [
                "구또또또또또또또또똗💛",
                "쩡우 형아 왜 왔어~? 질투나쟈냐~ 힝구ㅠㅠ",
                "곤쥬 근데 오늘 왜케 예뻐용 진짜?",
                "새싹쿼카 두두등장~ 헤헷콩!",
                "이삐야 밥 먹었쩌용?~ 맘마빱빠 냠냠💘",
                "새싹 쿼카를 물리쳐랏!!!",
                "걔 정수리 새싹 난 옆동네 쿼카 아니냐?",
                "나 황정우 아니라고 했드아아아아아?"
            ]
            selected_phrase = random.choice(random_phrases)

            try:
                tts = gTTS(text=selected_phrase, lang='ko')
                tts.save("tts.mp3")
            except Exception as e:
                print(f"TTS 생성 실패: {e}")
                await smart_send(message, "모라고 말해용?ㅠㅠ")
                return

            try:
                audio_source = discord.FFmpegPCMAudio("tts.mp3")
                if not vc.is_playing():
                    vc.play(audio_source)
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    os.remove("tts.mp3")  # ✅ TTS 재생 후 파일 삭제
            except Exception as e:
                print(f"음성 재생 실패: {e}")
                await smart_send(message, "입이 안떨어져용ㅠㅠ")
        else:
            await smart_send(message, "먼저 음성룸 들어가쏘~🌱")
        return

    # 음악 기능
    if "노래 틀어" in msg or "틀어" in msg:
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

    if msg in ["나가", "꺼져", "그만해"]:
        vc = message.guild.voice_client
        if vc and vc.is_connected():
            await vc.disconnect()
            await smart_send(message, "히잉... 나 갈게용...😭")
        else:
            await smart_send(message, "지금 음성채널에 없쪄용~🙄")
        return

    # 이미지 생성
    if "그려줘" in msg or "그림" in msg or "사진 만들어" in msg:
        prompt = message.content.replace("그려줘", "").replace("그림", "").replace("사진 만들어", "").strip()
        if not prompt:
            await smart_send(message, "무슨 그림 그릴까용~? 🎨")
            return
        await smart_send(message, f"그림 그리고 이따아아~🖌️ '{prompt}'...")
        image_url = await generate_image(prompt)
        if image_url:
            await message.channel.send(image_url)
        else:
            await smart_send(message, "이미지 생성 에러에러에러용ㅠㅠ")
        return

    # 자동 반응
    if any(kw in msg for kw in ["모해", "뭐해", "바보", "왜", "코카야"]):
        messages = [
            "공주 근데 왜케 이뻐용? 헤헷콩~🌸", "구또밖에 몰라용~ 힝구ㅠㅠ",
            "쩡우! 또 구또랑 말했쪄? 질투나쟈냐~🙄", "구또는 세상에서 쩰 귀여워요~💛",
            "아잉~ 구또당~ 부끄부끄해~🥺", "새싹쿼카 왔다앗~ 🌱 두둥쟝!!",
            "곤쥬~ 왜케 이뽀요??~✨", "이삐야 밥 먹었어용? 냠냠!!🍚",
            "내 심장은 구또의 것이다!! 헤헷콩~💘"
        ]
        await smart_send(message, random.choice(messages))
        return

    # GPT 응답
    reply = ask_gpt(user_id, message.content)
    await smart_send(message, reply)

# 🌱 Replit 유지용
keep_alive()

# 🌱 실행
bot.run(DISCORD_TOKEN)
