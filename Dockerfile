FROM python:3.9-slim

WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY mcp_server.py .
COPY test_mcp_client.py .
COPY stylebook_metadata.json .
COPY README.md .

# 스타일북 폴더 복사
COPY 스타일북/ ./스타일북/

# 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["python", "mcp_server.py"] 