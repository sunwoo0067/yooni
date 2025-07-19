#!/usr/bin/env python3
"""
NLP 챗봇 사용 예제
"""
import asyncio
from nlp_chatbot import NLPChatbot, IntentType, ChatbotTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_chatbot_demo():
    """기본 챗봇 데모"""
    print("=== NLP 챗봇 데모 ===\n")
    
    # 챗봇 초기화
    chatbot = NLPChatbot()
    
    # 데이터베이스 연결 (선택사항)
    # await chatbot.initialize_database("postgresql://user:pass@localhost:5434/yoonni")
    
    # 테스트 대화
    test_messages = [
        ("안녕하세요!", "user1"),
        ("제품 검색하고 싶어요", "user1"),
        ("노트북 가격이 얼마인가요?", "user1"),
        ("주문번호 ORD-20240101-1234 배송 조회해주세요", "user1"),
        ("반품하고 싶어요", "user1"),
        ("감사합니다", "user1"),
        ("Hello, I need help", "user2"),
        ("What's the price of this laptop?", "user2"),
        ("I want to return my order", "user2"),
        ("Thank you", "user2")
    ]
    
    # 세션별 대화 처리
    for message, user_id in test_messages:
        print(f"\n사용자 ({user_id}): {message}")
        
        # 메시지 처리
        response = await chatbot.process_message(
            session_id=f"session_{user_id}",
            message=message,
            user_id=user_id
        )
        
        print(f"챗봇: {response['response']}")
        print(f"의도: {response['intent']}")
        print(f"추출된 개체: {response['entities']}")
        print(f"언어: {response['language']}")
        print("-" * 50)
    
    # 대화 요약
    print("\n=== 대화 요약 ===")
    for user_id in ["user1", "user2"]:
        summary = chatbot.get_conversation_summary(f"session_{user_id}")
        print(f"\n{user_id} 세션 요약:")
        print(f"- 메시지 수: {summary['message_count']}")
        print(f"- 대화 시간: {summary['duration']:.1f}초")
        print(f"- 의도 분포: {summary['intent_distribution']}")
        print(f"- 추출된 개체: {summary['extracted_entities']}")


async def faq_matching_demo():
    """FAQ 매칭 데모"""
    print("\n=== FAQ 매칭 데모 ===\n")
    
    chatbot = NLPChatbot()
    
    # FAQ 질문 테스트
    test_queries = [
        "배송은 얼마나 걸려요?",
        "언제쯤 도착하나요?",
        "반품 방법 알려주세요",
        "환불은 어떻게 받나요?",
        "회원가입하면 뭐가 좋아요?",
        "쿠폰 있나요?"
    ]
    
    for query in test_queries:
        print(f"\n질문: {query}")
        
        # FAQ 매칭
        faq_match = chatbot.find_similar_faq(query)
        
        if faq_match:
            print(f"매칭된 FAQ: {faq_match['question']}")
            print(f"답변: {faq_match['answer']}")
            print(f"의도: {faq_match['intent'].value}")
        else:
            print("매칭된 FAQ 없음")


async def entity_extraction_demo():
    """개체 추출 데모"""
    print("\n=== 개체 추출 데모 ===\n")
    
    chatbot = NLPChatbot()
    
    # 테스트 문장
    test_sentences = [
        "주문번호 ORD-20240115-5678의 상태를 확인하고 싶어요",
        "노트북 가격이 1,500,000원이라고 들었는데 맞나요?",
        "2024년 1월 20일에 주문한 제품이 언제 도착하나요?",
        "스마트폰 3개 주문하고 싶습니다",
        "어제 주문한 상품 내일까지 받을 수 있을까요?",
        "Order ORD-20240120-9999 needs to be cancelled",
        "The price is $1,200 or 1,500,000 KRW"
    ]
    
    for sentence in test_sentences:
        print(f"\n문장: {sentence}")
        
        # 개체 추출
        entities = chatbot.extract_entities(sentence)
        
        print("추출된 개체:")
        for entity_type, value in entities.items():
            print(f"  - {entity_type}: {value}")


async def multilingual_demo():
    """다국어 지원 데모"""
    print("\n=== 다국어 지원 데모 ===\n")
    
    chatbot = NLPChatbot()
    session_id = "multilingual_session"
    
    # 한국어/영어 혼용 대화
    mixed_messages = [
        "안녕하세요, I have a question",
        "제품 가격이 how much인가요?",
        "I want to 반품하고 싶어요",
        "Thank you 감사합니다"
    ]
    
    for message in mixed_messages:
        print(f"\n사용자: {message}")
        
        # 언어 감지
        detected_lang = chatbot.detect_language(message)
        print(f"감지된 언어: {detected_lang}")
        
        # 메시지 처리
        response = await chatbot.process_message(session_id, message)
        print(f"챗봇: {response['response']}")


async def training_demo():
    """챗봇 학습 데모"""
    print("\n=== 챗봇 학습 데모 ===\n")
    
    chatbot = NLPChatbot()
    trainer = ChatbotTrainer(chatbot)
    
    # 학습 데이터 준비
    training_conversations = [
        {
            "input": "안녕하세요",
            "intent": IntentType.GREETING.value,
            "entities": {},
            "language": "ko"
        },
        {
            "input": "상품 찾고 있어요",
            "intent": IntentType.PRODUCT_INQUIRY.value,
            "entities": {},
            "language": "ko"
        },
        {
            "input": "주문 상태 확인",
            "intent": IntentType.ORDER_STATUS.value,
            "entities": {},
            "language": "ko"
        },
        {
            "input": "반품하려고 해요",
            "intent": IntentType.RETURN_EXCHANGE.value,
            "entities": {},
            "language": "ko"
        },
        {
            "input": "가격 문의",
            "intent": IntentType.PRICE_INQUIRY.value,
            "entities": {},
            "language": "ko"
        }
    ]
    
    # 학습 데이터 수집
    trainer.collect_training_data(training_conversations)
    
    # 데이터셋 준비
    texts, labels = trainer.prepare_intent_dataset()
    print(f"학습 데이터 수: {len(texts)}")
    print(f"의도 유형: {set(labels)}")
    
    # 모델 학습 (실제 구현 필요)
    # trainer.train_intent_classifier(texts, labels)
    
    # 평가
    test_conversations = [
        {"input": "안녕", "expected_intent": IntentType.GREETING.value},
        {"input": "제품 정보", "expected_intent": IntentType.PRODUCT_INQUIRY.value},
        {"input": "배송 조회", "expected_intent": IntentType.ORDER_STATUS.value}
    ]
    
    evaluation = trainer.evaluate_chatbot(test_conversations)
    print(f"\n평가 결과:")
    print(f"의도 정확도: {evaluation['intent_accuracy']:.2%}")
    print(f"테스트 샘플 수: {evaluation['total_tested']}")


async def context_management_demo():
    """컨텍스트 관리 데모"""
    print("\n=== 컨텍스트 관리 데모 ===\n")
    
    chatbot = NLPChatbot()
    session_id = "context_demo"
    
    # 연속 대화
    conversation_flow = [
        "노트북 찾고 있어요",
        "가격이 얼마인가요?",  # 컨텍스트에서 노트북 참조
        "재고 있나요?",  # 여전히 노트북에 대한 질문
        "주문하고 싶어요",
        "배송은 언제쯤?"
    ]
    
    for message in conversation_flow:
        print(f"\n사용자: {message}")
        
        response = await chatbot.process_message(session_id, message)
        print(f"챗봇: {response['response']}")
        print(f"현재 의도: {response['intent']}")
        
        # 컨텍스트 상태 확인
        if session_id in chatbot.contexts:
            context = chatbot.contexts[session_id]
            print(f"저장된 개체: {context.entities}")
            print(f"대화 히스토리 길이: {len(context.history)}")


async def error_handling_demo():
    """오류 처리 데모"""
    print("\n=== 오류 처리 데모 ===\n")
    
    chatbot = NLPChatbot()
    
    # 이해할 수 없는 메시지
    unclear_messages = [
        "ㅁㄴㅇㄹ",
        "!@#$%^&*()",
        "",
        "askdjfhaskjdfhaskjdfh",
        "..." 
    ]
    
    for message in unclear_messages:
        print(f"\n사용자: '{message}'")
        
        response = await chatbot.process_message("error_session", message)
        print(f"챗봇: {response['response']}")
        print(f"의도: {response['intent']}")


async def main():
    """메인 함수"""
    # 기본 챗봇 데모
    await basic_chatbot_demo()
    
    # FAQ 매칭 데모
    await faq_matching_demo()
    
    # 개체 추출 데모
    await entity_extraction_demo()
    
    # 다국어 지원 데모
    await multilingual_demo()
    
    # 학습 데모
    await training_demo()
    
    # 컨텍스트 관리 데모
    await context_management_demo()
    
    # 오류 처리 데모
    await error_handling_demo()


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main())