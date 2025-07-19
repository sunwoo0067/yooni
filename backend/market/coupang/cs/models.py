#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 데이터 모델
"""

import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .constants import (
    ANSWERED_TYPE, DEFAULT_PAGE_NUM, DEFAULT_PAGE_SIZE,
    CC_DEFAULT_PAGE_SIZE, PARTNER_COUNSELING_STATUS
)


@dataclass
class InquirySearchParams:
    """고객문의 검색 파라미터"""
    vendor_id: str
    answered_type: str  # ALL, ANSWERED, NOANSWER
    inquiry_start_at: str  # yyyy-MM-dd
    inquiry_end_at: str    # yyyy-MM-dd
    page_num: Optional[int] = DEFAULT_PAGE_NUM
    page_size: Optional[int] = DEFAULT_PAGE_SIZE
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열로 변환"""
        params = {
            'vendorId': self.vendor_id,
            'answeredType': self.answered_type,
            'inquiryStartAt': self.inquiry_start_at,
            'inquiryEndAt': self.inquiry_end_at
        }
        
        if self.page_num is not None:
            params['pageNum'] = str(self.page_num)
        if self.page_size is not None:
            params['pageSize'] = str(self.page_size)
            
        return urllib.parse.urlencode(params)


@dataclass
class InquiryComment:
    """문의 답변 정보"""
    inquiry_comment_id: int
    inquiry_id: int
    content: str
    inquiry_comment_at: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InquiryComment':
        """딕셔너리에서 InquiryComment 객체 생성"""
        return cls(
            inquiry_comment_id=data.get('inquiryCommentId', 0),
            inquiry_id=data.get('inquiryId', 0),
            content=data.get('content', ''),
            inquiry_comment_at=data.get('inquiryCommentAt', '')
        )


@dataclass
class CustomerInquiry:
    """고객 문의 정보"""
    inquiry_id: int
    product_id: int
    seller_product_id: int
    seller_item_id: int
    vendor_item_id: int
    content: str
    inquiry_at: str
    order_ids: List[int] = field(default_factory=list)
    buyer_email: str = ''
    comment_dto_list: List[InquiryComment] = field(default_factory=list)
    
    # 추가 정보
    is_answered: bool = False
    answer_count: int = 0
    latest_answer_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerInquiry':
        """딕셔너리에서 CustomerInquiry 객체 생성"""
        # 답변 목록 처리
        comments = []
        if 'commentDtoList' in data and data['commentDtoList']:
            comments = [
                InquiryComment.from_dict(comment) 
                for comment in data['commentDtoList']
            ]
        
        # 답변 관련 정보 계산
        is_answered = len(comments) > 0
        answer_count = len(comments)
        latest_answer_at = None
        if comments:
            # 가장 최근 답변 시간 찾기
            latest_answer_at = max(comment.inquiry_comment_at for comment in comments)
        
        return cls(
            inquiry_id=data.get('inquiryId', 0),
            product_id=data.get('productId', 0),
            seller_product_id=data.get('sellerProductId', 0),
            seller_item_id=data.get('sellerItemId', 0),
            vendor_item_id=data.get('vendorItemId', 0),
            content=data.get('content', ''),
            inquiry_at=data.get('inquiryAt', ''),
            order_ids=data.get('orderIds', []),
            buyer_email=data.get('buyerEmail', ''),
            comment_dto_list=comments,
            is_answered=is_answered,
            answer_count=answer_count,
            latest_answer_at=latest_answer_at
        )
    
    def get_answered_type(self) -> str:
        """답변 상태 반환"""
        return "ANSWERED" if self.is_answered else "NOANSWER"
    
    def get_inquiry_summary(self) -> Dict[str, Any]:
        """문의 요약 정보"""
        return {
            "inquiry_id": self.inquiry_id,
            "product_id": self.product_id,
            "content_preview": self.content[:50] + "..." if len(self.content) > 50 else self.content,
            "inquiry_at": self.inquiry_at,
            "answered_type": self.get_answered_type(),
            "answer_count": self.answer_count,
            "latest_answer_at": self.latest_answer_at,
            "has_order": len(self.order_ids) > 0,
            "order_count": len(self.order_ids)
        }
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """문의 상세 정보"""
        return {
            "basic_info": {
                "inquiry_id": self.inquiry_id,
                "inquiry_at": self.inquiry_at,
                "content": self.content
            },
            "product_info": {
                "product_id": self.product_id,
                "seller_product_id": self.seller_product_id,
                "seller_item_id": self.seller_item_id,
                "vendor_item_id": self.vendor_item_id
            },
            "customer_info": {
                "buyer_email": self.buyer_email,
                "order_ids": self.order_ids,
                "order_count": len(self.order_ids)
            },
            "answer_info": {
                "is_answered": self.is_answered,
                "answer_count": self.answer_count,
                "latest_answer_at": self.latest_answer_at,
                "answers": [
                    {
                        "comment_id": comment.inquiry_comment_id,
                        "content": comment.content,
                        "answered_at": comment.inquiry_comment_at
                    }
                    for comment in self.comment_dto_list
                ]
            }
        }


@dataclass
class InquiryPagination:
    """페이지네이션 정보"""
    current_page: int
    total_pages: int
    total_elements: int
    count_per_page: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InquiryPagination':
        """딕셔너리에서 InquiryPagination 객체 생성"""
        return cls(
            current_page=data.get('currentPage', 1),
            total_pages=data.get('totalPages', 0),
            total_elements=data.get('totalElements', 0),
            count_per_page=data.get('countPerPage', 0)
        )
    
    def has_next_page(self) -> bool:
        """다음 페이지 존재 여부"""
        return self.current_page < self.total_pages
    
    def has_previous_page(self) -> bool:
        """이전 페이지 존재 여부"""
        return self.current_page > 1
    
    def get_pagination_info(self) -> Dict[str, Any]:
        """페이지네이션 요약 정보"""
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "total_elements": self.total_elements,
            "count_per_page": self.count_per_page,
            "has_next": self.has_next_page(),
            "has_previous": self.has_previous_page(),
            "start_element": (self.current_page - 1) * self.count_per_page + 1,
            "end_element": min(self.current_page * self.count_per_page, self.total_elements)
        }


@dataclass
class InquiryListResponse:
    """고객문의 목록 응답"""
    code: int
    message: str
    content: List[CustomerInquiry] = field(default_factory=list)
    pagination: Optional[InquiryPagination] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'InquiryListResponse':
        """딕셔너리에서 InquiryListResponse 객체 생성"""
        inquiries = []
        pagination = None
        
        if 'data' in response_data and response_data['data']:
            data = response_data['data']
            
            # 문의 목록 처리
            if 'content' in data and data['content']:
                inquiries = [
                    CustomerInquiry.from_dict(inquiry)
                    for inquiry in data['content']
                ]
            
            # 페이지네이션 정보 처리
            if 'pagination' in data and data['pagination']:
                pagination = InquiryPagination.from_dict(data['pagination'])
        
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            content=inquiries,
            pagination=pagination
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """문의 요약 통계"""
        if not self.content:
            return {
                "total_count": 0,
                "answered_count": 0,
                "unanswered_count": 0,
                "answer_rate": 0.0,
                "with_order_count": 0,
                "order_rate": 0.0
            }
        
        total_count = len(self.content)
        answered_count = sum(1 for inquiry in self.content if inquiry.is_answered)
        unanswered_count = total_count - answered_count
        with_order_count = sum(1 for inquiry in self.content if len(inquiry.order_ids) > 0)
        
        return {
            "total_count": total_count,
            "answered_count": answered_count,
            "unanswered_count": unanswered_count,
            "answer_rate": answered_count / total_count * 100 if total_count > 0 else 0.0,
            "with_order_count": with_order_count,
            "order_rate": with_order_count / total_count * 100 if total_count > 0 else 0.0,
            "pagination_info": self.pagination.get_pagination_info() if self.pagination else None
        }
    
    def get_unanswered_inquiries(self) -> List[CustomerInquiry]:
        """미답변 문의 목록"""
        return [inquiry for inquiry in self.content if not inquiry.is_answered]
    
    def get_recent_inquiries(self, limit: int = 5) -> List[CustomerInquiry]:
        """최근 문의 목록"""
        sorted_inquiries = sorted(
            self.content, 
            key=lambda x: x.inquiry_at, 
            reverse=True
        )
        return sorted_inquiries[:limit]


@dataclass
class InquiryReplyRequest:
    """고객문의 답변 요청"""
    vendor_id: str
    inquiry_id: int
    content: str
    reply_by: str
    
    def to_json_data(self) -> Dict[str, Any]:
        """JSON 요청 데이터로 변환"""
        return {
            "vendorId": self.vendor_id,
            "content": self.content,
            "replyBy": self.reply_by
        }
    
    def validate_content(self) -> str:
        """답변 내용 JSON 형식 검증 및 정리"""
        if not self.content or not self.content.strip():
            raise ValueError("답변 내용을 입력해주세요")
        
        # 줄바꿈 문자 정리 (\r\n -> \n, \r -> \n)
        cleaned_content = self.content.replace('\r\n', '\n').replace('\r', '\n')
        
        # JSON에서 문제가 될 수 있는 특수 문자들 검증
        # 실제 JSON 인코딩 테스트
        import json
        try:
            json.dumps({"content": cleaned_content})
        except (TypeError, ValueError) as e:
            raise ValueError(f"답변 내용에 JSON에서 지원하지 않는 문자가 포함되어 있습니다: {str(e)}")
        
        return cleaned_content


@dataclass
class InquiryReplyResponse:
    """고객문의 답변 응답"""
    code: int
    message: str
    inquiry_id: Optional[int] = None
    vendor_id: Optional[str] = None
    reply_content: Optional[str] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any], 
                  inquiry_id: Optional[int] = None,
                  vendor_id: Optional[str] = None,
                  reply_content: Optional[str] = None) -> 'InquiryReplyResponse':
        """딕셔너리에서 InquiryReplyResponse 객체 생성"""
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            inquiry_id=inquiry_id,
            vendor_id=vendor_id,
            reply_content=reply_content
        )
    
    def is_success(self) -> bool:
        """성공 여부 확인"""
        return self.code == 200
    
    def get_summary(self) -> Dict[str, Any]:
        """답변 요약 정보"""
        return {
            "inquiry_id": self.inquiry_id,
            "vendor_id": self.vendor_id,
            "success": self.is_success(),
            "code": self.code,
            "message": self.message,
            "reply_content_length": len(self.reply_content) if self.reply_content else 0
        }


@dataclass
class CallCenterInquirySearchParams:
    """고객센터 문의 검색 파라미터"""
    vendor_id: str
    partner_counseling_status: str  # NONE, ANSWER, NO_ANSWER, TRANSFER
    inquiry_start_at: Optional[str] = None  # yyyy-MM-dd
    inquiry_end_at: Optional[str] = None    # yyyy-MM-dd
    order_id: Optional[int] = None
    vendor_item_id: Optional[str] = None
    page_num: Optional[int] = DEFAULT_PAGE_NUM
    page_size: Optional[int] = CC_DEFAULT_PAGE_SIZE
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열로 변환"""
        params = {
            'vendorId': self.vendor_id,
            'partnerCounselingStatus': self.partner_counseling_status
        }
        
        if self.inquiry_start_at:
            params['inquiryStartAt'] = self.inquiry_start_at
        if self.inquiry_end_at:
            params['inquiryEndAt'] = self.inquiry_end_at
        if self.order_id:
            params['orderId'] = str(self.order_id)
        if self.vendor_item_id:
            params['vendorItemId'] = self.vendor_item_id
        if self.page_num is not None:
            params['pageNum'] = str(self.page_num)
        if self.page_size is not None:
            params['pageSize'] = str(self.page_size)
            
        return urllib.parse.urlencode(params)


@dataclass
class CallCenterReply:
    """고객센터 문의 답변 정보"""
    answer_id: int
    parent_answer_id: Optional[int]
    partner_transfer_status: Optional[str]
    partner_transfer_complete_reason: str
    answer_type: str  # csAgent 또는 vendor
    need_answer: bool
    receptionist_name: str
    receptionist: str
    reply_at: str
    content: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallCenterReply':
        """딕셔너리에서 CallCenterReply 객체 생성"""
        return cls(
            answer_id=data.get('answerId', 0),
            parent_answer_id=data.get('parentAnswerId'),
            partner_transfer_status=data.get('partnerTransferStatus'),
            partner_transfer_complete_reason=data.get('partnerTransferCompleteReason', ''),
            answer_type=data.get('answerType', ''),
            need_answer=data.get('needAnswer', False),
            receptionist_name=data.get('receptionistName', ''),
            receptionist=data.get('receptionist', ''),
            reply_at=data.get('replyAt', ''),
            content=data.get('content', '')
        )


@dataclass
class CallCenterInquiry:
    """고객센터 문의 정보"""
    inquiry_id: int
    inquiry_status: str  # progress 또는 complete
    cs_partner_counseling_status: str  # requestAnswer 또는 answered
    vendor_item_id: List[int]
    item_name: str
    content: str
    answered_at: Optional[str]
    replies: List[CallCenterReply] = field(default_factory=list)
    inquiry_at: str = ''
    buyer_email: str = ''
    buyer_phone: str = ''
    order_id: Optional[int] = None
    order_date: Optional[str] = None
    receipt_category: str = ''
    sale_started_at: Optional[str] = None
    sale_ended_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallCenterInquiry':
        """딕셔너리에서 CallCenterInquiry 객체 생성"""
        # 답변 목록 처리
        replies = []
        if 'replies' in data and data['replies']:
            replies = [
                CallCenterReply.from_dict(reply) 
                for reply in data['replies']
            ]
        
        return cls(
            inquiry_id=data.get('inquiryId', 0),
            inquiry_status=data.get('inquiryStatus', ''),
            cs_partner_counseling_status=data.get('csPartnerCounselingStatus', ''),
            vendor_item_id=data.get('vendorItemId', []),
            item_name=data.get('itemName', ''),
            content=data.get('content', ''),
            answered_at=data.get('answeredAt'),
            replies=replies,
            inquiry_at=data.get('inquiryAt', ''),
            buyer_email=data.get('buyerEmail', ''),
            buyer_phone=data.get('buyerPhone', ''),
            order_id=data.get('orderId'),
            order_date=data.get('orderDate'),
            receipt_category=data.get('receiptCategory', ''),
            sale_started_at=data.get('saleStartedAt'),
            sale_ended_at=data.get('saleEndedAt')
        )
    
    def has_pending_answer(self) -> bool:
        """답변 대기 중인지 확인"""
        return any(reply.need_answer for reply in self.replies)
    
    def get_latest_reply(self) -> Optional[CallCenterReply]:
        """최신 답변 가져오기"""
        if not self.replies:
            return None
        return max(self.replies, key=lambda x: x.reply_at)
    
    def is_transfer_status(self) -> bool:
        """이관 상태인지 확인"""
        return self.cs_partner_counseling_status == "requestAnswer"
    
    def get_summary(self) -> Dict[str, Any]:
        """문의 요약 정보"""
        return {
            "inquiry_id": self.inquiry_id,
            "inquiry_status": self.inquiry_status,
            "counseling_status": self.cs_partner_counseling_status,
            "item_name": self.item_name,
            "inquiry_at": self.inquiry_at,
            "has_pending_answer": self.has_pending_answer(),
            "reply_count": len(self.replies),
            "order_id": self.order_id,
            "receipt_category": self.receipt_category
        }


@dataclass
class CallCenterInquiryListResponse:
    """고객센터 문의 목록 응답"""
    code: int
    message: str
    content: List[CallCenterInquiry] = field(default_factory=list)
    pagination: Optional[InquiryPagination] = None
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'CallCenterInquiryListResponse':
        """딕셔너리에서 CallCenterInquiryListResponse 객체 생성"""
        inquiries = []
        pagination = None
        
        if 'data' in response_data and response_data['data']:
            data = response_data['data']
            
            # 문의 목록 처리
            if 'content' in data and data['content']:
                inquiries = [
                    CallCenterInquiry.from_dict(inquiry)
                    for inquiry in data['content']
                ]
            
            # 페이지네이션 정보 처리
            if 'pagination' in data and data['pagination']:
                pagination = InquiryPagination.from_dict(data['pagination'])
        
        return cls(
            code=response_data.get('code', 0),
            message=response_data.get('message', ''),
            content=inquiries,
            pagination=pagination
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """문의 요약 통계"""
        if not self.content:
            return {
                "total_count": 0,
                "answered_count": 0,
                "pending_count": 0,
                "transfer_count": 0
            }
        
        total_count = len(self.content)
        answered_count = sum(1 for inquiry in self.content 
                           if inquiry.cs_partner_counseling_status == "answered")
        pending_count = sum(1 for inquiry in self.content 
                          if inquiry.has_pending_answer())
        transfer_count = sum(1 for inquiry in self.content 
                           if inquiry.is_transfer_status())
        
        return {
            "total_count": total_count,
            "answered_count": answered_count,
            "pending_count": pending_count,
            "transfer_count": transfer_count,
            "answer_rate": answered_count / total_count * 100 if total_count > 0 else 0.0,
            "pagination_info": self.pagination.get_pagination_info() if self.pagination else None
        }


@dataclass
class CallCenterInquiryReplyRequest:
    """고객센터 문의 답변 요청"""
    vendor_id: str
    inquiry_id: int
    content: str
    reply_by: str
    parent_answer_id: int
    
    def to_json_data(self) -> Dict[str, Any]:
        """JSON 요청 데이터로 변환"""
        return {
            "vendorId": self.vendor_id,
            "inquiryId": str(self.inquiry_id),
            "content": self.content,
            "replyBy": self.reply_by,
            "parentAnswerId": self.parent_answer_id
        }
    
    def validate_content_length(self) -> bool:
        """답변 내용 길이 검증 (2~1000자)"""
        return 2 <= len(self.content) <= 1000


@dataclass
class CallCenterInquiryConfirmRequest:
    """고객센터 문의 확인 요청"""
    confirm_by: str
    
    def to_json_data(self) -> Dict[str, Any]:
        """JSON 요청 데이터로 변환"""
        return {
            "confirmBy": self.confirm_by
        }