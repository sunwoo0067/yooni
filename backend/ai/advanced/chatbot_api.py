#!/usr/bin/env python3
"""
챗봇 API 엔드포인트
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
import logging

from nlp_chatbot import NLPChatbot, IntentType

# FastAPI 앱 초기화
app = FastAPI(title="NLP Chatbot API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 챗봇 인스턴스
chatbot = NLPChatbot()

# WebSocket 연결 관리
active_connections: Dict[str, WebSocket] = {}


# 요청/응답 모델
class ChatMessage(BaseModel):
    """채팅 메시지"""
    session_id: str
    message: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    session_id: str
    response: str
    intent: str
    entities: Dict[str, Any]
    language: str
    confidence: float
    timestamp: datetime
    suggestions: Optional[List[str]] = None


class SessionInfo(BaseModel):
    """세션 정보"""
    session_id: str
    user_id: Optional[str]
    message_count: int
    duration: float
    language: str
    last_activity: datetime


class FeedbackRequest(BaseModel):
    """사용자 피드백"""
    session_id: str
    message_id: str
    rating: int  # 1-5
    feedback_text: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("챗봇 API 서버 시작")
    
    # 데이터베이스 연결 (환경 변수에서 읽기)
    # db_url = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5434/yoonni")
    # await chatbot.initialize_database(db_url)
    
    # 정기적인 세션 정리 작업 시작
    asyncio.create_task(cleanup_old_sessions())


async def cleanup_old_sessions():
    """오래된 세션 정기 정리"""
    while True:
        await asyncio.sleep(3600)  # 1시간마다
        chatbot.clear_old_sessions(hours=24)
        logger.info("오래된 세션 정리 완료")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatMessage):
    """채팅 메시지 처리"""
    try:
        # 메시지 처리
        result = await chatbot.process_message(
            session_id=request.session_id,
            message=request.message,
            user_id=request.user_id
        )
        
        # 추천 응답 생성
        suggestions = generate_suggestions(result['intent'])
        
        return ChatResponse(
            session_id=request.session_id,
            response=result['response'],
            intent=result['intent'],
            entities=result['entities'],
            language=result['language'],
            confidence=result['confidence'],
            timestamp=datetime.now(),
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 채팅 연결"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # 환영 메시지
        welcome_msg = {
            "type": "system",
            "message": "챗봇에 연결되었습니다. 무엇을 도와드릴까요?",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(welcome_msg)
        
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 메시지 처리
            result = await chatbot.process_message(
                session_id=session_id,
                message=message_data['message'],
                user_id=message_data.get('user_id')
            )
            
            # 응답 전송
            response_data = {
                "type": "bot",
                "response": result['response'],
                "intent": result['intent'],
                "entities": result['entities'],
                "confidence": result['confidence'],
                "timestamp": datetime.now().isoformat(),
                "suggestions": generate_suggestions(result['intent'])
            }
            await websocket.send_json(response_data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 종료: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
    finally:
        if session_id in active_connections:
            del active_connections[session_id]


@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """세션 정보 조회"""
    summary = chatbot.get_conversation_summary(session_id)
    
    if "error" in summary:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    # 컨텍스트에서 추가 정보 가져오기
    context = chatbot.contexts.get(session_id)
    
    return SessionInfo(
        session_id=session_id,
        user_id=summary.get('user_id'),
        message_count=summary['message_count'],
        duration=summary['duration'],
        language=summary['language'],
        last_activity=context.last_activity if context else datetime.now()
    )


@app.get("/api/sessions")
async def list_active_sessions(user_id: Optional[str] = None):
    """활성 세션 목록"""
    sessions = []
    
    for session_id, context in chatbot.contexts.items():
        if user_id and context.user_id != user_id:
            continue
            
        sessions.append({
            "session_id": session_id,
            "user_id": context.user_id,
            "message_count": len(context.history),
            "last_activity": context.last_activity,
            "language": context.language
        })
    
    return {"sessions": sessions, "total": len(sessions)}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    if session_id not in chatbot.contexts:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    del chatbot.contexts[session_id]
    
    # WebSocket 연결도 종료
    if session_id in active_connections:
        await active_connections[session_id].close()
        del active_connections[session_id]
    
    return {"message": "세션이 삭제되었습니다"}


@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """사용자 피드백 제출"""
    # 피드백 저장 로직 (데이터베이스에 저장)
    logger.info(f"피드백 수신: {feedback.session_id} - 평점: {feedback.rating}")
    
    # 낮은 평점의 경우 로그에 기록
    if feedback.rating <= 2:
        logger.warning(f"낮은 평점 피드백: {feedback.feedback_text}")
    
    return {"message": "피드백이 저장되었습니다"}


@app.get("/api/faq")
async def get_faq_list():
    """FAQ 목록 조회"""
    return {
        "faqs": [
            {
                "id": i,
                "question": faq['question'],
                "answer": faq['answer'],
                "category": faq['intent'].value if hasattr(faq['intent'], 'value') else str(faq['intent'])
            }
            for i, faq in enumerate(chatbot.faq_database)
        ]
    }


@app.get("/api/intents")
async def get_supported_intents():
    """지원하는 의도 목록"""
    return {
        "intents": [
            {
                "value": intent.value,
                "name": intent.name,
                "description": get_intent_description(intent)
            }
            for intent in IntentType
        ]
    }


@app.get("/api/analytics/chat")
async def get_chat_analytics():
    """채팅 분석 데이터"""
    total_sessions = len(chatbot.contexts)
    total_messages = sum(len(ctx.history) for ctx in chatbot.contexts.values())
    
    # 의도별 통계
    intent_stats = {}
    language_stats = {"ko": 0, "en": 0}
    
    for context in chatbot.contexts.values():
        language_stats[context.language] = language_stats.get(context.language, 0) + 1
        
        for msg in context.history:
            if msg['intent']:
                intent_stats[msg['intent']] = intent_stats.get(msg['intent'], 0) + 1
    
    # 평균 대화 길이
    avg_conversation_length = total_messages / total_sessions if total_sessions > 0 else 0
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "active_websocket_connections": len(active_connections),
        "average_conversation_length": avg_conversation_length,
        "intent_distribution": intent_stats,
        "language_distribution": language_stats,
        "timestamp": datetime.now()
    }


def generate_suggestions(intent: str) -> List[str]:
    """의도에 따른 추천 응답 생성"""
    suggestions_map = {
        IntentType.GREETING.value: [
            "상품을 찾고 있어요",
            "주문 조회하기",
            "고객센터 연결"
        ],
        IntentType.PRODUCT_INQUIRY.value: [
            "가격 문의",
            "재고 확인",
            "비슷한 상품 보기"
        ],
        IntentType.ORDER_STATUS.value: [
            "배송 추적하기",
            "주문 취소",
            "배송지 변경"
        ],
        IntentType.RETURN_EXCHANGE.value: [
            "반품 신청하기",
            "교환 신청하기",
            "환불 정책 확인"
        ],
        IntentType.PRICE_INQUIRY.value: [
            "할인 쿠폰 확인",
            "대량 구매 문의",
            "가격 비교"
        ]
    }
    
    return suggestions_map.get(intent, ["처음으로", "상담원 연결", "도움말"])


def get_intent_description(intent: IntentType) -> str:
    """의도 설명"""
    descriptions = {
        IntentType.GREETING: "인사 및 대화 시작",
        IntentType.PRODUCT_INQUIRY: "제품 정보 문의",
        IntentType.ORDER_STATUS: "주문 상태 및 배송 조회",
        IntentType.RETURN_EXCHANGE: "반품 및 교환 요청",
        IntentType.PRICE_INQUIRY: "가격 정보 문의",
        IntentType.SHIPPING_INFO: "배송 정보 확인",
        IntentType.COMPLAINT: "불만 및 문제 제기",
        IntentType.GENERAL_QA: "일반 문의사항",
        IntentType.GOODBYE: "대화 종료",
        IntentType.UNKNOWN: "분류되지 않은 의도"
    }
    
    return descriptions.get(intent, "설명 없음")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_sessions": len(chatbot.contexts),
        "websocket_connections": len(active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    
    # 서버 실행
    uvicorn.run(
        "chatbot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )