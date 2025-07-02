FROM python:3.11-slim

# FFmpeg 설치
RUN apt-get update && apt-get install -y ffmpeg

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# 실행 명령어
CMD ["python", "main.py"]
