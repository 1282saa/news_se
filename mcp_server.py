from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import re
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import logging
import time

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "False").lower() in ("true", "1") else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

app = FastAPI(title="서울경제신문 스타일북 MCP 서버")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영환경에서는 특정 도메인만 허용하도록 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경 변수에서 설정 로드
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
API_KEY = os.getenv("API_KEY", None)
METADATA_FILE = os.getenv("METADATA_FILE", "stylebook_metadata.json")
STYLEBOOK_DIR = os.getenv("STYLEBOOK_DIR", "스타일북")

# 스타일북 메타데이터 로드
try:
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        stylebook_meta = json.load(f)
    logger.info(f"메타데이터 로드 완료: {METADATA_FILE}")
except Exception as e:
    logger.error(f"메타데이터 로드 에러: {e}")
    stylebook_meta = {"stylebook_metadata": {"sections": []}}

# API 키 검증 의존성
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        logger.warning(f"잘못된 API 키 시도: {x_api_key[:5]}...")
        raise HTTPException(status_code=401, detail="유효하지 않은 API 키")
    return x_api_key

# JSON-RPC 오류 응답 생성 함수
def create_error_response(code: int, message: str, request_id: Any = None, data: Dict = None) -> Dict:
    response = {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": request_id
    }
    if data:
        response["error"]["data"] = data
    return response

# JSON-RPC 성공 응답 생성 함수
def create_success_response(result: Any, request_id: Any) -> Dict:
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    }

# 실행 시간 측정 데코레이터
def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} 실행 시간: {end_time - start_time:.4f}초")
        return result
    return wrapper

# JSON-RPC 2.0 엔드포인트
@app.post("/rpc", dependencies=[Depends(verify_api_key)] if API_KEY else [])
async def mcp_rpc_endpoint(request: Request):
    """
    MCP 서버의 메인 JSON-RPC 엔드포인트
    """
    try:
        req_json = await request.json()
    except Exception as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return JSONResponse(content=create_error_response(-32700, "잘못된 JSON 형식입니다", None))

    # JSON-RPC 기본 필드 파싱
    jsonrpc = req_json.get("jsonrpc")
    method = req_json.get("method")
    params = req_json.get("params", {})
    request_id = req_json.get("id")

    # 로깅
    logger.info(f"요청 받음: method={method}, id={request_id}")
    logger.debug(f"파라미터: {params}")

    # JSON-RPC 버전 체크
    if jsonrpc != "2.0":
        return JSONResponse(content=create_error_response(-32600, "잘못된 JSON-RPC 버전입니다 (2.0 필요)", request_id))

    # 메서드에 따른 함수 실행
    try:
        if method == "get_sections":
            result = get_sections()
        elif method == "get_document":
            result = get_document(params)
        elif method == "search_documents":
            result = search_documents(params)
        elif method == "get_file_by_path":
            result = get_file_by_path(params)
        else:
            return JSONResponse(content=create_error_response(-32601, f"존재하지 않는 메서드: {method}", request_id))
    except Exception as e:
        logger.error(f"메서드 {method} 실행 중 오류: {e}")
        return JSONResponse(content=create_error_response(-32000, f"서버 내부 오류: {str(e)}", request_id))

    # 정상 응답
    return JSONResponse(content=create_success_response(result, request_id))

# 전체 섹션 목록 가져오기
@measure_time
def get_sections():
    """
    스타일북의 모든 섹션 목록을 반환합니다.
    """
    sections = []
    for section in stylebook_meta["stylebook_metadata"]["sections"]:
        sections.append({
            "id": section["id"],
            "title": section["title"],
            "path": section["path"],
            "file_count": len(section["files"])
        })
    return sections

# 문서 하나 가져오기
@measure_time
def get_document(params: dict):
    """
    file_id로 특정 문서를 가져옵니다.
    
    params: {
        "file_id": "basic_principles"
    }
    """
    file_id = params.get("file_id")
    if not file_id:
        return {"error": "file_id가 필요합니다"}

    # 메타데이터에서 file_id에 해당하는 파일 정보 찾기
    file_info = None
    file_path = None
    
    for section in stylebook_meta["stylebook_metadata"]["sections"]:
        for f in section["files"]:
            if f["file_id"] == file_id:
                file_info = f
                file_path = os.path.join(section["path"], f["filename"])
                break
        if file_info:
            break
    
    if not file_info:
        # 유사한 file_id 찾기 (스마트 폴백)
        similar_files = find_similar_file_ids(file_id)
        if similar_files:
            return {
                "error": f"file_id에 해당하는 파일을 찾을 수 없습니다: {file_id}",
                "suggestions": similar_files
            }
        return {"error": f"file_id에 해당하는 파일을 찾을 수 없습니다: {file_id}"}

    # 파일 로드
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}"}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
    except Exception as e:
        return {"error": f"파일 로드 오류: {str(e)}"}
    
    # 결과 반환
    return {
        "file_id": file_id,
        "title": file_info["title"],
        "tags": file_info.get("tags", []),
        "content": doc_data.get("content", ""),
        "sections": doc_data.get("sections", [])
    }

# 파일 경로로 문서 가져오기 
@measure_time
def get_file_by_path(params: dict):
    """
    파일 경로로 문서를 가져옵니다.
    
    params: {
        "filepath": "스타일북/1서론/1_1뉴스란 무엇인가.json"
    }
    """
    filepath = params.get("filepath")
    if not filepath:
        return {"error": "filepath가 필요합니다"}

    if not os.path.exists(filepath):
        # 유사한 경로 찾기 (스마트 폴백)
        similar_paths = find_similar_filepaths(filepath)
        if similar_paths:
            return {
                "error": f"파일을 찾을 수 없습니다: {filepath}",
                "suggestions": similar_paths
            }
        return {"error": f"파일을 찾을 수 없습니다: {filepath}"}
    
    # 파일 확장자 확인
    if filepath.endswith('.json'):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
                
            # 메타데이터에서 관련 정보 찾기
            file_info = None
            filename = os.path.basename(filepath)
            
            for section in stylebook_meta["stylebook_metadata"]["sections"]:
                for f in section["files"]:
                    if f["filename"] == filename:
                        file_info = f
                        break
                if file_info:
                    break
            
            if file_info:
                return {
                    "file_id": file_info.get("file_id", "unknown"),
                    "title": file_info.get("title", filename),
                    "tags": file_info.get("tags", []),
                    "content": doc_data.get("content", ""),
                    "sections": doc_data.get("sections", [])
                }
            else:
                # 메타데이터에 없는 경우 파일 자체 정보만 반환
                return {
                    "file_id": "unknown",
                    "title": doc_data.get("title", filename),
                    "tags": doc_data.get("tags", []),
                    "content": doc_data.get("content", ""),
                    "sections": doc_data.get("sections", [])
                }
                
        except Exception as e:
            return {"error": f"JSON 파일 로드 오류: {str(e)}"}
    
    # 텍스트 파일인 경우
    elif filepath.endswith('.txt'):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            filename = os.path.basename(filepath)
            return {
                "file_id": "unknown",
                "title": filename,
                "tags": [],
                "content": content,
                "sections": []
            }
        except Exception as e:
            return {"error": f"텍스트 파일 로드 오류: {str(e)}"}
    
    else:
        return {"error": "지원하지 않는 파일 형식입니다"}

# 키워드 검색
@measure_time
def search_documents(params: dict):
    """
    키워드로 문서를 검색합니다.
    
    params: {
        "keyword": "문장부호",
        "limit": 10,
        "offset": 0
    }
    """
    keyword = params.get("keyword", "")
    limit = int(params.get("limit", 10))
    offset = int(params.get("offset", 0))
    
    if not keyword:
        return {"error": "keyword가 필요합니다"}

    results = []
    
    # 메타데이터 검색 (제목, 태그)
    for section in stylebook_meta["stylebook_metadata"]["sections"]:
        for f in section["files"]:
            title = f["title"]
            tags = f.get("tags", [])
            
            if (keyword.lower() in title.lower()) or any(keyword.lower() in tag.lower() for tag in tags):
                results.append({
                    "file_id": f["file_id"],
                    "title": f["title"],
                    "path": os.path.join(section["path"], f["filename"]),
                    "tags": tags,
                    "section": section["title"],
                    "match_type": "metadata"
                })
    
    # 파일 내용 검색 (메타데이터 검색 결과가 적을 경우)
    if len(results) < 3:
        for section in stylebook_meta["stylebook_metadata"]["sections"]:
            for f in section["files"]:
                filepath = os.path.join(section["path"], f["filename"])
                
                if not os.path.exists(filepath):
                    continue
                    
                try:
                    if filepath.endswith('.json'):
                        with open(filepath, "r", encoding="utf-8") as file:
                            doc_data = json.load(file)
                            content = doc_data.get("content", "")
                            
                        if keyword.lower() in content.lower():
                            # 이미 메타데이터에서 찾은 결과와 중복 방지
                            if not any(r["file_id"] == f["file_id"] for r in results):
                                results.append({
                                    "file_id": f["file_id"],
                                    "title": f["title"],
                                    "path": filepath,
                                    "tags": f.get("tags", []),
                                    "section": section["title"],
                                    "match_type": "content",
                                    "excerpt": extract_context(content, keyword, 150)
                                })
                except Exception:
                    # 파일 처리 오류는 무시하고 다음 파일 진행
                    continue
    
    # 검색 결과가 없는 경우 유사 키워드 제안
    if not results:
        return {
            "results": [],
            "total": 0,
            "suggestions": suggest_similar_keywords(keyword)
        }
    
    # 페이지네이션 적용
    total_results = len(results)
    paginated_results = results[offset:offset + limit]
    
    return {
        "results": paginated_results,
        "total": total_results,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total_results
    }

# 유사한 파일 ID 찾기 (스마트 폴백)
def find_similar_file_ids(file_id: str, max_results: int = 3) -> List[Dict]:
    """
    주어진 file_id와 유사한 파일 ID를 찾습니다.
    """
    all_file_ids = []
    for section in stylebook_meta["stylebook_metadata"]["sections"]:
        for f in section["files"]:
            all_file_ids.append({
                "file_id": f["file_id"],
                "title": f["title"]
            })
    
    # 간단한 유사도 측정 (부분 문자열 포함 여부)
    similar_ids = []
    for item in all_file_ids:
        current_id = item["file_id"]
        # file_id가 서로의 부분 문자열인 경우 또는 공통 부분이 있는 경우
        if file_id in current_id or current_id in file_id:
            similar_ids.append(item)
            if len(similar_ids) >= max_results:
                break
    
    return similar_ids

# 유사한 파일 경로 찾기 (스마트 폴백)
def find_similar_filepaths(filepath: str, max_results: int = 3) -> List[str]:
    """
    주어진 파일 경로와 유사한 파일 경로를 찾습니다.
    """
    basename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)
    
    # 같은 디렉토리에 있는 파일 찾기
    similar_paths = []
    if os.path.exists(dirname):
        for file in os.listdir(dirname):
            if file.startswith(basename[:3]) or basename.startswith(file[:3]):
                similar_path = os.path.join(dirname, file)
                if os.path.isfile(similar_path):
                    similar_paths.append(similar_path)
                    if len(similar_paths) >= max_results:
                        break
    
    return similar_paths

# 유사한 키워드 제안
def suggest_similar_keywords(keyword: str, max_suggestions: int = 3) -> List[str]:
    """
    검색 키워드와 유사한 키워드를 제안합니다.
    """
    # 모든 태그와 제목 수집
    all_terms = set()
    for section in stylebook_meta["stylebook_metadata"]["sections"]:
        for f in section["files"]:
            all_terms.add(f["title"].lower())
            for tag in f.get("tags", []):
                all_terms.add(tag.lower())
    
    # 유사한 용어 찾기
    keyword_lower = keyword.lower()
    suggestions = []
    
    for term in all_terms:
        # 부분 문자열 포함 여부 확인
        if keyword_lower in term or any(kw in term for kw in keyword_lower.split()):
            suggestions.append(term)
            if len(suggestions) >= max_suggestions:
                break
    
    return suggestions

# 컨텍스트 추출 함수 (검색 결과에 일부 문맥 제공)
def extract_context(text: str, keyword: str, context_size: int = 150) -> str:
    """
    텍스트에서 키워드 주변의 컨텍스트를 추출합니다.
    """
    keyword_lower = keyword.lower()
    text_lower = text.lower()
    
    # 키워드 위치 찾기
    pos = text_lower.find(keyword_lower)
    if pos == -1:
        return ""
    
    # 컨텍스트 범위 계산
    start = max(0, pos - context_size // 2)
    end = min(len(text), pos + len(keyword) + context_size // 2)
    
    # 컨텍스트 추출 및 마크업
    context = text[start:end]
    
    # 앞뒤가 잘린 경우 표시
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
    
    return context

# 기본 정보 엔드포인트
@app.get("/")
async def root():
    """
    서버 기본 정보를 제공합니다.
    """
    return {
        "message": "서울경제신문 스타일북 MCP 서버", 
        "version": "1.0",
        "endpoints": {
            "rpc": "/rpc (JSON-RPC 2.0)"
        },
        "documentation": "/docs"
    }

# 서버 실행
if __name__ == "__main__":
    import uvicorn
    logger.info(f"서버 시작 중: {HOST}:{PORT}")
    uvicorn.run("mcp_server:app", host=HOST, port=PORT, reload=True)
