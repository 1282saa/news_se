#!/bin/bash

# 스타일북 MCP 서버 빌드 및 배포 스크립트
set -e

# 기본 설정
IMAGE_NAME="stylebook-mcp-server"
VERSION=$(date "+%Y%m%d%H%M")
PORT=8000

# 도움말 표시
show_help() {
  echo "서울경제신문 스타일북 MCP 서버 배포 스크립트"
  echo ""
  echo "사용법: ./deploy.sh [옵션]"
  echo ""
  echo "옵션:"
  echo "  -h, --help        도움말 표시"
  echo "  -b, --build       도커 이미지 빌드"
  echo "  -r, --run         도커 컨테이너 실행"
  echo "  -s, --stop        실행 중인 컨테이너 중지"
  echo "  -t, --tag TAG     이미지 태그 지정 (기본값: 현재 날짜시간)"
  echo "  -p, --port PORT   포트 지정 (기본값: 8000)"
  echo ""
  echo "예시:"
  echo "  ./deploy.sh -b -r      # 이미지 빌드 후 컨테이너 실행"
  echo "  ./deploy.sh -s -b -r   # 기존 컨테이너 중지, 새로 빌드 및 실행"
  echo "  ./deploy.sh -t v1.0 -p 9000 -b -r  # 태그와 포트 지정하여 빌드 및 실행"
}

# 도커 이미지 빌드
build_image() {
  echo "도커 이미지 빌드 중... ($IMAGE_NAME:$VERSION)"
  docker build -t $IMAGE_NAME:$VERSION -t $IMAGE_NAME:latest .
  echo "이미지 빌드 완료: $IMAGE_NAME:$VERSION"
}

# 도커 컨테이너 실행
run_container() {
  echo "도커 컨테이너 실행 중... (포트: $PORT)"
  
  # .env 파일 존재 여부 확인
  if [ -f .env ]; then
    ENV_FILE="--env-file .env"
  else
    ENV_FILE=""
    echo "경고: .env 파일이 없습니다. 기본 설정으로 실행합니다."
  fi
  
  # 컨테이너 실행
  docker run -d --name $IMAGE_NAME \
    -p $PORT:8000 \
    $ENV_FILE \
    -v "$(pwd)/스타일북:/app/스타일북" \
    $IMAGE_NAME:$VERSION
  
  echo "컨테이너가 백그라운드에서 실행 중입니다."
  echo "서버 URL: http://localhost:$PORT"
  echo "로그 확인: docker logs $IMAGE_NAME"
}

# 실행 중인 컨테이너 중지
stop_container() {
  echo "실행 중인 컨테이너 확인 중..."
  if docker ps -q --filter "name=$IMAGE_NAME" | grep -q .; then
    echo "컨테이너 중지 중: $IMAGE_NAME"
    docker stop $IMAGE_NAME
    docker rm $IMAGE_NAME
    echo "컨테이너가 중지되었습니다."
  else
    echo "실행 중인 컨테이너가 없습니다."
  fi
}

# 명령행 인자 파싱
BUILD=false
RUN=false
STOP=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -b|--build)
      BUILD=true
      shift
      ;;
    -r|--run)
      RUN=true
      shift
      ;;
    -s|--stop)
      STOP=true
      shift
      ;;
    -t|--tag)
      VERSION="$2"
      shift 2
      ;;
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    *)
      echo "알 수 없는 옵션: $1"
      show_help
      exit 1
      ;;
  esac
done

# 명령 실행
if [ "$STOP" = true ]; then
  stop_container
fi

if [ "$BUILD" = true ]; then
  build_image
fi

if [ "$RUN" = true ]; then
  run_container
fi

# 아무 옵션도 지정되지 않은 경우 도움말 표시
if [ "$BUILD" = false ] && [ "$RUN" = false ] && [ "$STOP" = false ]; then
  show_help
fi

echo "스크립트 실행 완료" 