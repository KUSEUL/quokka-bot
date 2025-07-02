FROM python:3.11-slim-bullseye

# 🎯 디스코드 음성 기능 관련 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libnacl-dev \
    build-essential \
    && apt-get clean

WORKDIR /app

# pip 최신화
RUN pip install --upgrade pip

# requirements.txt 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 전체 소스 복사
COPY . .

# 실행
CMD ["python", "main.py"]
