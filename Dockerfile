# Python 3.11 이미지를 기반으로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


# 프로젝트 파일 복사
COPY src ./src
COPY database.py ./database.py
COPY main.py ./main.py
COPY prompts ./prompts
COPY requirements.txt ./requirements.txt
# 의존성 설치
RUN pip install -r requirements.txt

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 설정
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
