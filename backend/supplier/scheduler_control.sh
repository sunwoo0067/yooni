#!/bin/bash
# 스케줄러 제어 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/../venv"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LOG_FILE="$SCRIPT_DIR/scheduler_daemon.log"

# 가상환경 활성화
source "$VENV_PATH/bin/activate"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "스케줄러가 이미 실행 중입니다 (PID: $PID)"
                exit 1
            fi
        fi
        
        echo "스케줄러 시작 중..."
        cd "$SCRIPT_DIR"
        nohup python run_scheduler.py > "$LOG_FILE" 2>&1 &
        sleep 2
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "스케줄러 시작됨 (PID: $PID)"
            echo "로그 파일: $LOG_FILE"
        else
            echo "스케줄러 시작 실패"
            exit 1
        fi
        ;;
        
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "스케줄러 종료 중 (PID: $PID)..."
            kill -TERM $PID
            sleep 2
            
            if ps -p $PID > /dev/null 2>&1; then
                echo "강제 종료..."
                kill -KILL $PID
            fi
            
            rm -f "$PID_FILE"
            echo "스케줄러 종료됨"
        else
            echo "스케줄러가 실행 중이 아닙니다"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "스케줄러 실행 중 (PID: $PID)"
                echo "최근 로그:"
                tail -n 10 "$LOG_FILE"
            else
                echo "스케줄러가 종료됨 (PID 파일 있음)"
                rm -f "$PID_FILE"
            fi
        else
            echo "스케줄러가 실행 중이 아닙니다"
        fi
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "로그 파일이 없습니다"
        fi
        ;;
        
    collect)
        echo "수동 수집 실행..."
        cd "$SCRIPT_DIR"
        if [ -z "$2" ]; then
            python scheduler.py --collect-all
        else
            python scheduler.py --collect "$2"
        fi
        ;;
        
    *)
        echo "사용법: $0 {start|stop|restart|status|logs|collect [supplier_name]}"
        exit 1
        ;;
esac