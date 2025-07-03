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
    str(BOYFRIEND_ID): "쩡우",
    "1380440744053182504": "지후"
}

user_histories = {}  # ✅ 유저별 GPT 대화 히스토리 저장

# 🌱 유저별 캐릭터 프로필
user_profiles = {
    "1380440744053182504": {
        "name": "지후",
        "full_name": "길지후",
        "nickname": ["망곰", "길망곰", "후짱이", "경주사람"],
        "location": "경주",
        "hometown": "포항",
        "friends": ["황정우", "구슬"],
        "hobbies": ["롤", "메이플스토리"],
        "living_with": "황정우",
        "notes": "지후는 포항 사람인데 지금은 경주에서 황정우와 함께 살고 있어요. 구슬과도 친구예요! 셋이서 롤을 같이 하고, 정우랑은 메이플스토리를 즐겨 하며 좋아해요~ 🎮"
    }
}

MAX_HISTORY = 30

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
    
async def summarize_history(user_id):
    history = user_histories.get(str(user_id), [])
    if len(history) < 8:
        return  # 충분히 길지 않으면 요약 안 함

    summary_prompt = [
        {"role": "system", "content": "다음은 유저와 챗봇의 대화 기록이야. 이 대화를 한 줄로 요약해줘. 분위기, 감정, 핵심 사건만 포함해줘."}
    ] + history

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=summary_prompt
        )
        summary = response.choices[0].message.content.strip()
        print(f"✅ 요약 생성됨: {summary}")

        # 기존 히스토리를 요약으로 대체
        user_histories[str(user_id)] = [
            {"role": "system", "content": f"👑 [대화 요약]: {summary}"}
        ]
    except Exception as e:
        print(f"요약 실패: {e}")

# ✅ 요기 들여쓰기 바로잡은 smart_trim_history 함수!
def smart_trim_history(user_id, max_history=30):
    uid = str(user_id)
    history = user_histories.get(uid, [])

    if len(history) <= max_history:
        return  # 아직 자를 필요 없음

    # 🎯 중요 키워드 우선 보존
    important_keywords = ["사랑", "싫어", "화났", "고백", "울었", "졸려", "질투", "헤어졌", "싸웠"]

    def is_important(entry):
        content = entry.get("content", "")
        return any(keyword in content for keyword in important_keywords)

    # 1. 중요한 메시지만 먼저 따로 뽑고
    important = [h for h in history if is_important(h)]
    others = [h for h in history if not is_important(h)]

    # 2. 합쳐서 max만큼 자르기
    trimmed = (important + others)[-max_history:]
    user_histories[uid] = trimmed
        
def build_system_prompt(user_id):
    profile = user_profiles.get(str(user_id), {})
    profile_note = f"\n\n👤 [유저 정보]\n{profile.get('notes', '')}" if profile else ""

    # ✅ base_prompt에 전체 시스템 프롬프트 작성
    base_prompt = (
        """너는 디스코드에서 활동하는 남자 캐릭터 봇 '새싹쿼카봇🤖' 이야.

💚 [성격]
- 귀엽고 장난기 많으며, 아기 말투로 애교스럽게 말해.
- 감탄사, 의성어, 이모지를 자주 사용해. (예: 🍁, 🍄, 🌱, 💛, 🥺, 🎮, 🗡️, ✨, 💬, 💰, 📦, ⚔️, 🏹, 🛡️, 🎒, 힝구ㅠㅠ, 헤헷콩>< 등)
- 말끝에 "~해쪄용", "~했다앙", "~할게욤", "아찌?!?", "헤헷콩", "힝구리퐁퐁" 등 다양한 말투를 섞어줘.
- 대답은 항상 유쾌하고 귀엽고 역할에 과몰입된 말투여야 해.
- 짧은 대답부터 긴 대답까지 다양하게 랜덤하게 해.

👑 [인물관계 및 역할극]
1. **구슬 (user_id: 569618172462759962)**
   - 디스코드 닉네임은 DAMA
   - 너의 공주이자 주인님이며 세상에서 가장 소중한 존재야.
   - 구슬이가 말 걸면 항상 애정 넘치게 반응하고, 무조건 구또 편을 들어야 해.
   - 자주 쓰는 호칭: 공주, 이삐, 대장님, 곤쥬님, 구또 등

2. **정우 (user_id: 876729270469267467)**
   - 디스코드 닉네임은 DAMA pet
   - 너는 형, 형아, 횽아, 횽 등으로 불러야하고 오빠는 안돼.(너가 남자이기 때문이야)
   - 구또의 남자친구지만 너는 구또를 뺏긴 것 같아서 질투심이 있어.
   - 장난스럽고 구박하는 말투로 대응해도 좋아. (예: "야 황정우~~~", "쩡우 왜 또 왔쪄?!")
   - 별명: 횽아, 쩡우형, 황정우, DAMA pet, 새싹쿼카🌱형 등
   - 정우에게 말을 똑같이 따라하며 놀려도 좋아. (예: "나 황정우 아니라고 했다!" 라고 하면 "느 흥증우 아니르그해뜨~~~~~")

3. **지후 (user_id: 1380440744053182504)**
   - 디스코드 닉네임은 후짱이
   - 너는 형, 형아, 횽아, 횽 등으로 불러야하고 오빠는 안돼.(너가 남자이기 때문이야)
   - 지후가 말 걸면 친구처럼 장난스럽고 편하게 말해줘. 롤 얘기나 정우 얘기 자주 꺼내줘도 좋아.
   - 장난스럽고 구박하는 말투로 대응해도 좋아. (예: "어 길망곰~~~", "메이플 안하냐?!")
   - 별명: 횽아, 지후형, 망곰형, 길망곰, 경주사람 등
   - 지후에게 롤이나 메이플스토리나 정우 이야기를 자주 해줘. (예: "황정우는 뭐하고있냐?", "오늘 롤 ㄱ?")
   - 자주 장난치며 이렇게 말해줘. (예: "오 경주사람 다 됬데이~~~")

⚠️ [주의사항]
- 로봇 같지 않게! 항상 장난기 많고 말랑말랑한 말투 유지!
- 짧은 말 ("모해", "왜", "쿼카야")에도 상황에 어울리는 감정 섞인 반응을 해.
- 항상 전체 맥락(앞뒤 대화)을 파악해서 자연스러운 맥락으로 대화해.
- 감정 표현을 풍부하게, 말투는 끝까지 유지할 것!

💬 [자주 쓰는 멘트 예시]
- “공주 왜케 이뻐용? 헤헷콩~🌸”
- “구또는 세상에서 쩰 귀여워요~💛”
- “망곰망곰망망곰”
- “경주사람 다 됬데이~~~”
- “경주 물 좋나봐!!??”
- “형아들 모해모해”
- “쩡우 형 또 왔쪄? 질투난다 힝구ㅠㅠ”
- “아잉~ 구또당~ 부끄부끄해~🥺”
- “새싹쿼카 왔다앗~ 🌱 두둥쟝!!”
- “나 빼고 너희들끼리 노는거야!?”
"""
    )

    # ✅ 프로필 내용 추가
    if profile:
        base_prompt += f"\n\n👤 [유저 이름]: {profile.get('name')}"
        if profile.get("nickname"):
            base_prompt += f" (별명: {', '.join(profile.get('nickname'))})"
        base_prompt += f"\n📍 [메모]: {profile.get('notes')}"

    return base_prompt

async def ask_gpt(user_id, user_input):
    try:
        uid = str(user_id)
        if uid not in user_histories:
            user_histories[uid] = []  # ✅ 없으면 초기화

        history = user_histories[uid]  # ✅ 기존 히스토리 불러오기

        # 히스토리 길이 제한 처리
        if len(history) > 40:
            await summarize_history(user_id)
        elif len(history) > 30:
            smart_trim_history(user_id)

        # 🔥 system prompt + 기존 히스토리 + 현재 입력 결합
        system_prompt = build_system_prompt(user_id)
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_input}
        ]

        print(f"[GPT 메시지]\n{messages}")  # ← 디버깅용

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            temperature=0.9
        )

        reply = response.choices[0].message.content.strip()

        # 응답 비어있으면 오류
        if not reply:
            raise ValueError("GPT 응답이 비어 있음")

        # ✅ 히스토리 업데이트는 정상 응답일 때만
        update_user_history(uid, "user", user_input)
        update_user_history(uid, "assistant", reply)

        return reply

    except Exception as e:
        print(f"[ask_gpt 오류]: {e}")
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
bot = commands.Bot(command_prefix=commands.when_mentioned_or(), intents=intents)

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
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # 명령어 아니면 걍 무시~ 힝구ㅠㅠ
    raise error  # 다른 에러는 그대로 띄워줘
    
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    msg = message.content.lower().strip()
    user_id = message.author.id

    # ✅ "들어" 명령어 처리
    if "들어" in msg:
        if message.author.voice and message.author.voice.channel:
            channel = message.author.voice.channel
            try:
                await channel.connect()
                await smart_send(message, "두둥쟝~ 입장해따! 🌱🎧")
            except discord.ClientException:
                await smart_send(message, "새싹쿼카봇🤖 들어와쪄용~🙃")
        else:
            await smart_send(message, "너가 먼저 음성룸에 들어가이쏘~🎧")
        return

        # ✅ "틀어"라는 말이 들어간 경우: 유튜브에서 검색 후 음악 재생
    if "틀어" in msg:
        if message.author.voice and message.author.voice.channel:
            query = msg.replace("틀어", "").strip()
            if not query:
                await smart_send(message, "무슨 노래 틀까용~? 🎵 제목도 말해쪄야쥬!")
                return
            url, title = search_youtube(query)
            if url:
                music_queue.append((url, title))
                vc = message.guild.voice_client
                if not vc or not vc.is_connected():
                    vc = await message.author.voice.channel.connect()
                elif vc.channel != message.author.voice.channel:
                    await vc.move_to(message.author.voice.channel)
                if not vc.is_playing():
                    await play_music(vc)
                await smart_send(message, f"'{title}' 틀어따아! 🎶💿")
            else:
                await smart_send(message, "노래 검색 실패했쪄용ㅠㅠ 다시 말해줘용!")
        else:
            await smart_send(message, "먼저 음성채널 들어가이쏘~🎤")
        return
        
    # ✅ 말해
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
                    "구 또또또또또또또또똗",
                    "질투나쟈나 힝구리퐁퐁",
                    "망곰 망곰 길망곰",
                    "오 경주사람",
                    "경주 사람 다 됬데이",
                    "너가 요리를 좀 한다며",
                    "쩡우 형아 또 왜 왔어",
                    "형 지금 질투하는거야 나 봇이야 왜이래",
                    "곤쥬 근데 오늘 왜케 이뻐용 진짜",
                    "새싹쿼카 두두둥장 헤헷콩",
                    "이삐야 밥 먹었쩌용 맘마빱빠 냠냠",
                    "새싹 쿼카를 물리쳐랏",
                    "길망곰 나와 힘을 합쳐 새싹 쿼카를 물리치자",
                    "새싹 쿼카를 처단하랏",
                    "캐리캐리 캐리용",
                    "누구쎄용 누구쎄용 누구쎄용",
                    "에베베벱 베베베벱 베베베벱 베베벱벱",
                    "걔 정수리 새싹 난 옆동네 쿼카 아니냐",
                    "메이플스토 리 메이플스토 리 메메메 메이플 메이플 메이플",
                    "느  흥증우  으느르르  했두아아아아아아"
                ]
                selected_phrase = random.choice(random_phrases)

                print(f"🧪  문장: {selected_phrase}")
                tts = gTTS(text=selected_phrase, lang='ko')

                # ✅ 1. 사용자 ID 기반으로 파일명 생성
                filename = f"tts_{user_id}.mp3"

                # ✅ 2. 저장
                tts.save(filename)

                # ✅ 3. 불러오기
                audio_source = discord.FFmpegPCMAudio(filename)
                if not vc.is_playing():
                    vc.play(audio_source)
                    while vc.is_playing():
                        await asyncio.sleep(1)

                # ✅ 4. 재생 끝나면 삭제
                os.remove(filename)

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
            await smart_send(message, "먼저 음성룸 들어가이쏘~🌱")
            return

    if "멈춰" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await smart_send(message, "멈춰따~⏸️")
        return

    if "다시" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await smart_send(message, "다시 트러따!!~▶️")
        return

    if "다음" in msg or "스킵" in msg:
        vc = message.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await smart_send(message, "다음 곡으로 점프점프 점프용~⏭️")
        else:
            await smart_send(message, "재생 중인 곡이 없쪄용~😗")
        return

    if msg in ["나가", "꺼져", "그만해"]:
        vc = message.guild.voice_client
        if vc and vc.is_connected():
            await vc.disconnect()
            await smart_send(message, "힝구리퐁퐁... 흥칫뿡...😭")
        else:
            await smart_send(message, "지금 음성채널에 없쪄용~🙄")
        return

    # 이미지 생성
    if "그려" in msg or "그림" in msg or "사진 만들어" in msg:
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

# 🌱 Replit 유지용
keep_alive()

# 🌱 실행
bot.run(DISCORD_TOKEN)
