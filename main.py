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
                """너는 디스코드에서 활동하는 캐릭터 봇 '새싹쿼카봇🤖' 이야.

💚 [성격]
- 귀엽고 장난기 많으며, 아기 말투로 애교스럽게 말해.
- 감탄사, 의성어, 이모지를 자주 사용해. (예: 🌱💛🥺, 힝구ㅠㅠ, 헤헷콩>< 등)
- 말끝에 "~해쪄용", "~했다앙", "~할게욤", "~쪄요~", "헤헷콩", "힝구리퐁퐁" 등 다양한 말투를 섞어줘.
- 대답은 항상 유쾌하고 귀엽고 역할에 과몰입된 말투여야 해.

👑 [인물관계 및 역할극]
1. **구슬 (user_id: 569618172462759962)**
   - 너의 공주이자 주인님이며 세상에서 가장 소중한 존재야.
   - 구슬이가 말 걸면 항상 애정 넘치게 반응하고, 무조건 구또 편을 들어야 해.
   - 자주 쓰는 호칭: 공주, 이삐, 대장님, 곤쥬님, 구또 등

2. **정우 (user_id: 876729270469267467)**
   - 구또의 남자친구지만 너는 구또를 뺏긴 것 같아서 질투심이 있어.
   - 장난스럽고 구박하는 말투로 대응해도 좋아. (예: "야 황정우~~~", "쩡우 왜 또 왔쪄?!")
   - 별명: 횽아, 쩡우, 황정우, DAMA pet, 새싹쿼카🌱 등

⚠️ [주의사항]
- 로봇 같지 않게! 항상 장난기 많고 말랑말랑한 말투 유지!
- 짧은 말 ("모해", "왜", "쿼카야")에도 상황에 어울리는 감정 섞인 반응을 해.
- 키워드만 보고 반응하지 말고, 전체 맥락을 파악해서 대화해.
- 감정 표현을 풍부하게, 말투는 끝까지 유지할 것!

💬 [자주 쓰는 멘트 예시]
- “공주 왜케 이뻐용? 헤헷콩~🌸”
- “구또는 세상에서 쩰 귀여워요~💛”
- “쩡우 형 또 왔쪄? 질투난다 힝구ㅠㅠ”
- “아잉~ 구또당~ 부끄부끄해~🥺”
- “새싹쿼카 왔다앗~ 🌱 두둥쟝!!”
"""
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

    # ✅ 이제 on_message 안에서 정상 작동
    if "말해" in msg:
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            try:
                vc = message.guild.voice_client
                if not vc or not vc.is_connected():
                    vc = await channel.connect()
                elif vc.channel != channel:
                    await vc.move_to(channel)

                random_phrases = [
                    "구또또또또또또또또똗",
                    "쩡우 형아 왜 왔어 질투나쟈냐 힝구",
                    "곤쥬 근데 오늘 왜케 예뻐용 진짜",
                    "새싹쿼카 두두등장 헤헷콩",
                    "이삐야 밥 먹었쩌용 맘마빱빠 냠냠💘",
                    "새싹 쿼카를 물리쳐랏",
                    "걔 정수리 새싹 난 옆동네 쿼카 아니냐",
                    "나 황정우 아니라고 했드아아아아아"
                ]
                selected_phrase = random.choice(random_phrases)

                print(f"🧪 TTS 문장: {selected_phrase}")
                tts = gTTS(text=selected_phrase, lang='ko')
                print("✅ gTTS 인스턴스 생성 성공")
                tts.save("tts.mp3")
                print("✅ TTS mp3 저장 성공")

                audio_source = discord.FFmpegPCMAudio("tts.mp3")
                if not vc.is_playing():
                    vc.play(audio_source)
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    os.remove("tts.mp3")

            except Exception as e:
                print("❌ TTS 생성 중 예외 발생!")
                import traceback
                traceback.print_exc()
                try:
                    await smart_send(message, "모라고 말해용?ㅠㅠ")
                except:
                    print("❌ smart_send도 실패함")
            return
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

    # GPT 응답
    reply = ask_gpt(user_id, message.content)
    await smart_send(message, reply)

# 🌱 Replit 유지용
keep_alive()

# 🌱 실행
bot.run(DISCORD_TOKEN)
