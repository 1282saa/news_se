#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

# 서버 주소
SERVER_URL = "http://localhost:8000/rpc"

def call_rpc_method(method, params=None):
    """JSON-RPC 2.0 메서드 호출 함수"""
    if params is None:
        params = {}
        
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def print_json(json_data):
    """JSON 데이터를 예쁘게 출력"""
    print(json.dumps(json_data, indent=2, ensure_ascii=False))

# 테스트 1: 섹션 목록 가져오기
def test_get_sections():
    print("\n==== 전체 섹션 목록 가져오기 ====")
    result = call_rpc_method("get_sections")
    print_json(result)

# 테스트 2: 특정 문서 가져오기
def test_get_document():
    print("\n==== 특정 문서 가져오기 (file_id 사용) ====")
    result = call_rpc_method("get_document", {"file_id": "basic_principles"})
    
    # 내용이 길면 일부만 출력
    if "result" in result and "content" in result["result"]:
        content = result["result"]["content"]
        if len(content) > 200:
            result["result"]["content"] = content[:200] + "... (이하 생략)"
    
    print_json(result)

# 테스트 3: 키워드 검색
def test_search_documents():
    print("\n==== '문장' 키워드 검색 ====")
    result = call_rpc_method("search_documents", {"keyword": "문장"})
    print_json(result)
    
    print("\n==== '제목' 키워드 검색 ====")
    result = call_rpc_method("search_documents", {"keyword": "제목"})
    print_json(result)

# 테스트 4: 파일 경로로 문서 가져오기
def test_get_file_by_path():
    print("\n==== 파일 경로로 문서 가져오기 ====")
    result = call_rpc_method("get_file_by_path", 
                             {"filepath": "스타일북/1서론/1_1뉴스란 무엇인가.json"})
    
    # 내용이 길면 일부만 출력
    if "result" in result and "content" in result["result"]:
        content = result["result"]["content"]
        if len(content) > 200:
            result["result"]["content"] = content[:200] + "... (이하 생략)"
    
    print_json(result)

# 테스트 5: 존재하지 않는 메서드 호출
def test_invalid_method():
    print("\n==== 존재하지 않는 메서드 호출 ====")
    result = call_rpc_method("invalid_method")
    print_json(result)

# 모든 테스트 실행
def run_all_tests():
    print("===== 서울경제신문 스타일북 MCP 서버 테스트 =====")
    test_get_sections()
    test_get_document()
    test_search_documents()
    test_get_file_by_path()
    test_invalid_method()
    print("\n모든 테스트 완료!")

if __name__ == "__main__":
    run_all_tests() 