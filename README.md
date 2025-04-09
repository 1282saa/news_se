# 서울경제신문 스타일북 MCP 서버

스타일북 데이터를 Claude나 다른 AI 모델에 연결하기 위한 MCP(Model Calling Protocol) 서버입니다.

## 개요

이 프로젝트는 서울경제신문 스타일북 데이터를 JSON-RPC 2.0 프로토콜을 통해 제공하는 서버를 구현합니다. Claude와 같은 LLM이 스타일북 내용을 정확하게 참조할 수 있도록 실시간 연결을 제공합니다.

## 주요 기능

- 스타일북의 섹션 목록 제공
- 특정 문서(file_id 기반) 검색 및 내용 제공
- 파일 경로 기반 문서 조회
- 키워드 기반 문서 검색 (페이지네이션 지원)
- 스마트 폴백 메커니즘 (유사 문서 추천)
- JSON-RPC 2.0 프로토콜 지원
- 환경 변수 설정 지원
- API 키 인증 (선택적)
- 로깅 및 성능 측정

## 필요 조건

- Python 3.7 이상
- FastAPI
- Uvicorn
- Requests (테스트용)
- Python-dotenv (환경 변수)

## 설치 방법

### 1. 직접 설치

필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

### 2. Docker 사용 (권장)

Docker를 사용하면 환경 설정 없이 간편하게 서버를 실행할 수 있습니다:

```bash
# 이미지 빌드
docker build -t stylebook-mcp-server .

# 서버 실행
docker run -p 8000:8000 --env-file .env -v $(pwd)/스타일북:/app/스타일북 stylebook-mcp-server
```

## 프로젝트 구조

```
.
├── mcp_server.py            # MCP 서버 구현
├── test_mcp_client.py       # 테스트용 클라이언트
├── stylebook_metadata.json  # 스타일북 메타데이터
├── requirements.txt         # 의존성 패키지 목록
├── .env.example             # 환경 변수 예제 파일
├── smithery.yaml            # MCP 도구 명세 (Claude용)
├── Dockerfile               # Docker 이미지 설정
└── 스타일북/                 # 스타일북 원본 파일들
```

## 실행 방법

### 환경 변수 설정 (선택사항)

`.env.example` 파일을 `.env`로 복사하여 필요한 설정을 조정합니다:

```bash
cp .env.example .env
```

### 서버 실행

```bash
python mcp_server.py
```

서버는 기본적으로 http://localhost:8000 에서 실행됩니다.

### 테스트 클라이언트 실행

```bash
python test_mcp_client.py
```

## API 명세

### 1. GET /

기본 정보 확인용 엔드포인트

### 2. POST /rpc

JSON-RPC 2.0 요청을 처리하는 메인 엔드포인트. 지원하는 메서드는 다음과 같습니다:

#### 2.1 get_sections

모든 스타일북 섹션 목록을 반환합니다.

```json
{
  "jsonrpc": "2.0",
  "method": "get_sections",
  "params": {},
  "id": 1
}
```

#### 2.2 get_document

file_id로 특정 문서를 조회합니다.

```json
{
  "jsonrpc": "2.0",
  "method": "get_document",
  "params": {
    "file_id": "basic_principles"
  },
  "id": 1
}
```

#### 2.3 get_file_by_path

파일 경로로 문서를 조회합니다.

```json
{
  "jsonrpc": "2.0",
  "method": "get_file_by_path",
  "params": {
    "filepath": "스타일북/1서론/1_1뉴스란 무엇인가.json"
  },
  "id": 1
}
```

#### 2.4 search_documents

키워드로 문서를 검색합니다. 페이지네이션을 지원합니다.

```json
{
  "jsonrpc": "2.0",
  "method": "search_documents",
  "params": {
    "keyword": "문장",
    "limit": 10,
    "offset": 0
  },
  "id": 1
}
```

## 도커 사용의 장점

도커를 사용하면 다음과 같은 장점이 있습니다:

1. **환경 일관성**: 개발, 테스트, 운영 환경에서 동일한 환경을 보장합니다.
2. **간편한 배포**: 복잡한 설치 과정 없이 컨테이너 실행만으로 서버를 구동할 수 있습니다.
3. **격리성**: 다른 애플리케이션과 충돌 없이 독립적으로 실행됩니다.
4. **확장성**: 쉽게 여러 인스턴스를 실행할 수 있습니다.
5. **버전 관리**: 이미지 태그를 통해 버전을 관리할 수 있습니다.
6. **보안**: 컨테이너 내부와 외부 시스템 간의 경계를 명확히 할 수 있습니다.

## Claude와 연동하기

### Claude Desktop에서 설정

Claude Desktop의 `claude_desktop_config.json` 파일에 다음을 추가합니다:

```json
{
  "mcpServers": {
    "stylebook-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-p", "8000:8000", "stylebook-mcp-server"]
    }
  }
}
```

### Cursor에서 설정

Cursor 설정에서 MCP 서버를 추가합니다:

- URL: `http://localhost:8000/rpc`
- (선택적) API 키: `.env` 파일에 설정한 API 키

이후 Claude에게 다음과 같이 물어볼 수 있습니다:

- "서울경제신문 스타일북에서 문장부호 사용법을 알려줘"
- "기사 작성시 피해야 할 표현들은 무엇인가요?"

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 참고 자료

- [JSON-RPC 2.0 명세](https://www.jsonrpc.org/specification)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Model Calling Protocol (MCP) 가이드](https://docs.anthropic.com/claude/docs/model-calling-protocol)
- [Docker 문서](https://docs.docker.com/)
