#!/usr/bin/env python3
"""
자연어 처리 기반 고객 서비스 챗봇
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum
import numpy as np

# NLP 라이브러리
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering,
    pipeline
)
import torch
from konlpy.tag import Okt
from sentence_transformers import SentenceTransformer

# 데이터베이스
import asyncio
import asyncpg

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """대화 의도 유형"""
    GREETING = "greeting"
    PRODUCT_INQUIRY = "product_inquiry"
    ORDER_STATUS = "order_status"
    RETURN_EXCHANGE = "return_exchange"
    PRICE_INQUIRY = "price_inquiry"
    SHIPPING_INFO = "shipping_info"
    COMPLAINT = "complaint"
    GENERAL_QA = "general_qa"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


class EntityType(Enum):
    """개체 유형"""
    PRODUCT_NAME = "product_name"
    ORDER_NUMBER = "order_number"
    CUSTOMER_NAME = "customer_name"
    DATE = "date"
    PRICE = "price"
    QUANTITY = "quantity"
    LOCATION = "location"


class ConversationContext:
    """대화 컨텍스트 관리"""
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.history: List[Dict[str, Any]] = []
        self.entities: Dict[str, Any] = {}
        self.current_intent: Optional[IntentType] = None
        self.language: str = "ko"  # 기본 한국어
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    def add_message(self, role: str, content: str, intent: Optional[IntentType] = None):
        """메시지 추가"""
        self.history.append({
            'role': role,
            'content': content,
            'intent': intent.value if intent else None,
            'timestamp': datetime.now()
        })
        self.last_activity = datetime.now()
        
    def update_entities(self, entities: Dict[str, Any]):
        """개체 정보 업데이트"""
        self.entities.update(entities)
        
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, Any]]:
        """최근 메시지 반환"""
        return self.history[-n:]
        
    def clear_old_messages(self, keep_last: int = 10):
        """오래된 메시지 정리"""
        if len(self.history) > keep_last:
            self.history = self.history[-keep_last:]


class NLPChatbot:
    """자연어 처리 기반 챗봇"""
    
    def __init__(self, model_name: str = "klue/bert-base"):
        # 모델 초기화
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.intent_classifier = None
        self.qa_model = None
        self.sentence_encoder = SentenceTransformer('sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens')
        
        # 한국어 형태소 분석기
        self.okt = Okt()
        
        # 의도 분류 파이프라인
        self.intent_pipeline = None
        
        # 대화 컨텍스트 저장소
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 응답 템플릿
        self.response_templates = self._load_response_templates()
        
        # FAQ 데이터베이스
        self.faq_database = self._load_faq_database()
        
        # 데이터베이스 연결
        self.db_pool = None
        
    def _load_response_templates(self) -> Dict[str, Dict[str, str]]:
        """응답 템플릿 로드"""
        return {
            IntentType.GREETING.value: {
                "ko": "안녕하세요! 무엇을 도와드릴까요?",
                "en": "Hello! How can I help you today?"
            },
            IntentType.PRODUCT_INQUIRY.value: {
                "ko": "{product_name}에 대해 알려드리겠습니다. 어떤 정보가 필요하신가요?",
                "en": "I'll help you with information about {product_name}. What would you like to know?"
            },
            IntentType.ORDER_STATUS.value: {
                "ko": "주문번호 {order_number}의 상태를 확인해드리겠습니다.",
                "en": "Let me check the status of order {order_number} for you."
            },
            IntentType.RETURN_EXCHANGE.value: {
                "ko": "반품/교환 도움이 필요하시군요. 주문번호를 알려주시겠어요?",
                "en": "I understand you need help with a return or exchange. Could you provide your order number?"
            },
            IntentType.PRICE_INQUIRY.value: {
                "ko": "{product_name}의 가격은 {price}원입니다.",
                "en": "The price of {product_name} is {price} KRW."
            },
            IntentType.SHIPPING_INFO.value: {
                "ko": "배송 정보를 확인해드리겠습니다. 주문번호나 상품명을 알려주세요.",
                "en": "I'll check the shipping information for you. Please provide your order number or product name."
            },
            IntentType.COMPLAINT.value: {
                "ko": "불편을 드려 죄송합니다. 자세한 내용을 들려주시면 최선을 다해 해결하겠습니다.",
                "en": "I'm sorry for the inconvenience. Please tell me more about the issue so I can help resolve it."
            },
            IntentType.GOODBYE.value: {
                "ko": "감사합니다. 좋은 하루 되세요!",
                "en": "Thank you! Have a great day!"
            },
            IntentType.UNKNOWN.value: {
                "ko": "죄송합니다. 이해하지 못했습니다. 다시 한 번 말씀해주시겠어요?",
                "en": "I'm sorry, I didn't understand that. Could you please rephrase?"
            }
        }
        
    def _load_faq_database(self) -> List[Dict[str, Any]]:
        """FAQ 데이터베이스 로드"""
        return [
            {
                "question": "배송은 얼마나 걸리나요?",
                "answer": "일반적으로 주문 후 2-3일 내에 배송됩니다. 도서산간 지역은 1-2일 추가될 수 있습니다.",
                "keywords": ["배송", "기간", "며칠", "언제"],
                "intent": IntentType.SHIPPING_INFO
            },
            {
                "question": "반품은 어떻게 하나요?",
                "answer": "상품 수령 후 7일 이내에 마이페이지에서 반품 신청이 가능합니다. 단순 변심의 경우 왕복 배송비가 부과됩니다.",
                "keywords": ["반품", "환불", "교환"],
                "intent": IntentType.RETURN_EXCHANGE
            },
            {
                "question": "회원가입 혜택이 있나요?",
                "answer": "신규 회원가입 시 5,000원 할인 쿠폰과 무료배송 쿠폰을 드립니다.",
                "keywords": ["회원가입", "혜택", "쿠폰", "할인"],
                "intent": IntentType.GENERAL_QA
            }
        ]
        
    async def initialize_database(self, db_url: str):
        """데이터베이스 초기화"""
        self.db_pool = await asyncpg.create_pool(db_url)
        
    def detect_language(self, text: str) -> str:
        """언어 감지"""
        korean_pattern = re.compile('[가-힣]+')
        english_pattern = re.compile('[a-zA-Z]+')
        
        korean_count = len(korean_pattern.findall(text))
        english_count = len(english_pattern.findall(text))
        
        return "ko" if korean_count > english_count else "en"
        
    def preprocess_text(self, text: str, language: str = "ko") -> str:
        """텍스트 전처리"""
        # 소문자 변환
        text = text.lower().strip()
        
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text
        
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """개체 추출"""
        entities = {}
        
        # 주문번호 추출 (예: ORD-20240101-1234)
        order_pattern = r'(ORD-\d{8}-\d+)'
        order_matches = re.findall(order_pattern, text.upper())
        if order_matches:
            entities[EntityType.ORDER_NUMBER.value] = order_matches[0]
            
        # 가격 추출
        price_pattern = r'(\d{1,3}(?:,\d{3})*|\d+)(?:원|₩|\s*KRW)?'
        price_matches = re.findall(price_pattern, text)
        if price_matches:
            entities[EntityType.PRICE.value] = price_matches[0].replace(',', '')
            
        # 날짜 추출
        date_patterns = [
            r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})',
            r'(\d{1,2}월\s*\d{1,2}일)',
            r'(오늘|내일|어제|이번\s*주|다음\s*주)'
        ]
        for pattern in date_patterns:
            date_matches = re.findall(pattern, text)
            if date_matches:
                entities[EntityType.DATE.value] = date_matches[0]
                break
                
        # 수량 추출
        quantity_pattern = r'(\d+)\s*(?:개|박스|세트|장)'
        quantity_matches = re.findall(quantity_pattern, text)
        if quantity_matches:
            entities[EntityType.QUANTITY.value] = int(quantity_matches[0])
            
        return entities
        
    def classify_intent(self, text: str, context: ConversationContext) -> IntentType:
        """의도 분류"""
        # 전처리
        processed_text = self.preprocess_text(text, context.language)
        
        # 키워드 기반 규칙
        intent_keywords = {
            IntentType.GREETING: ["안녕", "hello", "hi", "반가", "처음"],
            IntentType.PRODUCT_INQUIRY: ["상품", "제품", "product", "아이템", "물건"],
            IntentType.ORDER_STATUS: ["주문", "배송", "order", "tracking", "언제"],
            IntentType.RETURN_EXCHANGE: ["반품", "교환", "환불", "return", "exchange"],
            IntentType.PRICE_INQUIRY: ["가격", "얼마", "비용", "price", "cost"],
            IntentType.SHIPPING_INFO: ["배송", "택배", "shipping", "delivery"],
            IntentType.COMPLAINT: ["불만", "문제", "complaint", "issue", "잘못"],
            IntentType.GOODBYE: ["감사", "고마워", "bye", "종료", "끝"]
        }
        
        # 키워드 매칭
        for intent, keywords in intent_keywords.items():
            if any(keyword in processed_text for keyword in keywords):
                return intent
                
        # 컨텍스트 기반 의도 추론
        if context.current_intent:
            # 이전 대화 맥락 고려
            if context.current_intent == IntentType.PRODUCT_INQUIRY:
                if any(word in processed_text for word in ["가격", "얼마", "price"]):
                    return IntentType.PRICE_INQUIRY
                    
        # ML 모델 사용 (구현 시)
        # if self.intent_classifier:
        #     predicted_intent = self.intent_classifier.predict(processed_text)
        #     return IntentType(predicted_intent)
        
        return IntentType.UNKNOWN
        
    def find_similar_faq(self, query: str, threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """유사한 FAQ 찾기"""
        # 쿼리 임베딩
        query_embedding = self.sentence_encoder.encode([query])[0]
        
        best_match = None
        best_score = 0
        
        for faq in self.faq_database:
            # FAQ 질문 임베딩
            faq_embedding = self.sentence_encoder.encode([faq['question']])[0]
            
            # 코사인 유사도 계산
            similarity = np.dot(query_embedding, faq_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(faq_embedding)
            )
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = faq
                
        return best_match
        
    async def get_product_info(self, product_name: str) -> Dict[str, Any]:
        """제품 정보 조회"""
        if not self.db_pool:
            return {
                "name": product_name,
                "price": "가격 정보 없음",
                "stock": "재고 정보 없음",
                "description": "상품 정보를 찾을 수 없습니다."
            }
            
        query = """
        SELECT name, price, stock_quantity, description
        FROM products
        WHERE name ILIKE $1
        LIMIT 1
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(query, f'%{product_name}%')
            
        if result:
            return dict(result)
        else:
            return {
                "name": product_name,
                "price": "가격 정보 없음",
                "stock": "재고 정보 없음",
                "description": "상품 정보를 찾을 수 없습니다."
            }
            
    async def get_order_status(self, order_number: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        if not self.db_pool:
            return {
                "order_number": order_number,
                "status": "주문 정보를 찾을 수 없습니다.",
                "tracking_number": None
            }
            
        query = """
        SELECT order_number, status, tracking_number, 
               created_at, expected_delivery
        FROM orders
        WHERE order_number = $1
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(query, order_number)
            
        if result:
            return dict(result)
        else:
            return {
                "order_number": order_number,
                "status": "주문 정보를 찾을 수 없습니다.",
                "tracking_number": None
            }
            
    def generate_response(self, intent: IntentType, entities: Dict[str, Any], 
                         context: ConversationContext) -> str:
        """응답 생성"""
        # 템플릿 기반 응답
        template = self.response_templates.get(
            intent.value, {}
        ).get(context.language, "")
        
        # 엔티티 치환
        response = template
        for key, value in entities.items():
            placeholder = f"{{{key}}}"
            if placeholder in response:
                response = response.replace(placeholder, str(value))
                
        # 의도별 추가 처리
        if intent == IntentType.PRODUCT_INQUIRY and EntityType.PRODUCT_NAME.value in entities:
            # 제품 정보 추가
            product_info = asyncio.run(
                self.get_product_info(entities[EntityType.PRODUCT_NAME.value])
            )
            if product_info:
                response += f"\n가격: {product_info.get('price')}원"
                response += f"\n재고: {product_info.get('stock_quantity', '확인 필요')}"
                
        elif intent == IntentType.ORDER_STATUS and EntityType.ORDER_NUMBER.value in entities:
            # 주문 상태 추가
            order_info = asyncio.run(
                self.get_order_status(entities[EntityType.ORDER_NUMBER.value])
            )
            if order_info:
                response += f"\n상태: {order_info.get('status')}"
                if order_info.get('tracking_number'):
                    response += f"\n운송장번호: {order_info.get('tracking_number')}"
                    
        return response
        
    async def process_message(self, session_id: str, message: str, 
                            user_id: Optional[str] = None) -> Dict[str, Any]:
        """메시지 처리"""
        # 컨텍스트 가져오기 또는 생성
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id, user_id)
        context = self.contexts[session_id]
        
        # 언어 감지
        language = self.detect_language(message)
        context.language = language
        
        # 사용자 메시지 저장
        context.add_message("user", message)
        
        # 개체 추출
        entities = self.extract_entities(message)
        context.update_entities(entities)
        
        # 의도 분류
        intent = self.classify_intent(message, context)
        context.current_intent = intent
        
        # FAQ 검색
        faq_match = self.find_similar_faq(message)
        
        # 응답 생성
        if faq_match and intent == IntentType.UNKNOWN:
            response = faq_match['answer']
            intent = faq_match['intent']
        else:
            response = self.generate_response(intent, entities, context)
            
        # 봇 응답 저장
        context.add_message("assistant", response, intent)
        
        # 오래된 메시지 정리
        context.clear_old_messages()
        
        return {
            "session_id": session_id,
            "response": response,
            "intent": intent.value,
            "entities": entities,
            "language": language,
            "confidence": 0.85  # 신뢰도
        }
        
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """대화 요약"""
        if session_id not in self.contexts:
            return {"error": "Session not found"}
            
        context = self.contexts[session_id]
        
        # 의도 통계
        intent_counts = {}
        for msg in context.history:
            if msg['intent']:
                intent_counts[msg['intent']] = intent_counts.get(msg['intent'], 0) + 1
                
        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "message_count": len(context.history),
            "duration": (datetime.now() - context.created_at).total_seconds(),
            "intent_distribution": intent_counts,
            "extracted_entities": context.entities,
            "language": context.language
        }
        
    def export_training_data(self) -> List[Dict[str, Any]]:
        """학습 데이터 추출"""
        training_data = []
        
        for session_id, context in self.contexts.items():
            for i, msg in enumerate(context.history):
                if msg['role'] == 'user' and i + 1 < len(context.history):
                    next_msg = context.history[i + 1]
                    if next_msg['role'] == 'assistant':
                        training_data.append({
                            'input': msg['content'],
                            'intent': msg['intent'],
                            'response': next_msg['content'],
                            'entities': context.entities,
                            'language': context.language
                        })
                        
        return training_data
        
    def clear_old_sessions(self, hours: int = 24):
        """오래된 세션 정리"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        sessions_to_remove = []
        
        for session_id, context in self.contexts.items():
            if context.last_activity < cutoff_time:
                sessions_to_remove.append(session_id)
                
        for session_id in sessions_to_remove:
            del self.contexts[session_id]
            
        logger.info(f"Cleared {len(sessions_to_remove)} old sessions")


class ChatbotTrainer:
    """챗봇 학습 모듈"""
    
    def __init__(self, chatbot: NLPChatbot):
        self.chatbot = chatbot
        self.training_data = []
        
    def collect_training_data(self, conversations: List[Dict[str, Any]]):
        """학습 데이터 수집"""
        for conv in conversations:
            processed = {
                'text': conv['input'],
                'intent': conv['intent'],
                'entities': conv.get('entities', {}),
                'language': conv.get('language', 'ko')
            }
            self.training_data.append(processed)
            
    def prepare_intent_dataset(self) -> Tuple[List[str], List[str]]:
        """의도 분류 데이터셋 준비"""
        texts = []
        labels = []
        
        for data in self.training_data:
            texts.append(data['text'])
            labels.append(data['intent'])
            
        return texts, labels
        
    def train_intent_classifier(self, texts: List[str], labels: List[str]):
        """의도 분류기 학습"""
        # 간단한 예시 - 실제로는 BERT 파인튜닝 등 수행
        logger.info(f"Training intent classifier with {len(texts)} examples")
        
        # 토크나이징
        inputs = self.chatbot.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            return_tensors="pt"
        )
        
        # 레이블 인코딩
        unique_labels = list(set(labels))
        label_to_id = {label: i for i, label in enumerate(unique_labels)}
        encoded_labels = [label_to_id[label] for label in labels]
        
        # 모델 학습 (실제 구현 필요)
        # model = AutoModelForSequenceClassification.from_pretrained(
        #     "klue/bert-base", num_labels=len(unique_labels)
        # )
        # ... 학습 코드 ...
        
    def evaluate_chatbot(self, test_conversations: List[Dict[str, Any]]) -> Dict[str, float]:
        """챗봇 평가"""
        correct_intents = 0
        total = len(test_conversations)
        
        for conv in test_conversations:
            # 의도 예측
            context = ConversationContext("test_session")
            predicted_intent = self.chatbot.classify_intent(conv['input'], context)
            
            if predicted_intent.value == conv['expected_intent']:
                correct_intents += 1
                
        return {
            'intent_accuracy': correct_intents / total if total > 0 else 0,
            'total_tested': total
        }