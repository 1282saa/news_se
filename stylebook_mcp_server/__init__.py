"""
서울경제신문 스타일북 MCP 서버

이 패키지는 서울경제신문 스타일북 데이터를 AI 모델에게 제공하는 
Model Context Protocol (MCP) 서버를 구현합니다.
"""

import os

__version__ = "0.1.0"

# API 키가 빈 문자열이면 API 키 검증을 건너뜁니다 (MVP 단계용)
API_KEY = os.getenv("API_KEY", "") 