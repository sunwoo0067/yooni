#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 매출내역 조회 모듈 데이터 모델
"""

import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from .constants import SALE_TYPE, TAX_TYPE


@dataclass
class RevenueSearchParams:
    """매출내역 검색 파라미터"""
    
    vendor_id: str                              # 판매자 ID (필수)
    recognition_date_from: str                  # 매출 인식일 시작 (YYYY-MM-DD, 필수)
    recognition_date_to: str                    # 매출 인식일 종료 (YYYY-MM-DD, 필수)
    max_per_page: Optional[int] = 20           # 페이지당 최대 개수 (1~100, 기본값: 20)
    token: Optional[str] = None                # 페이지네이션 토큰
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열 생성"""
        params = {
            "vendorId": self.vendor_id,
            "recognitionDateFrom": self.recognition_date_from,
            "recognitionDateTo": self.recognition_date_to,
            "maxPerPage": self.max_per_page or 20
        }
        
        if self.token:
            params["token"] = self.token
        
        return urllib.parse.urlencode(params)
    
    def get_date_range_days(self) -> int:
        """조회 기간 일수 계산"""
        start_date = datetime.strptime(self.recognition_date_from, '%Y-%m-%d')
        end_date = datetime.strptime(self.recognition_date_to, '%Y-%m-%d')
        return (end_date - start_date).days + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """검색 파라미터 요약"""
        return {
            "vendor_id": self.vendor_id,
            "date_range": f"{self.recognition_date_from} ~ {self.recognition_date_to}",
            "period_days": self.get_date_range_days(),
            "max_per_page": self.max_per_page,
            "has_token": bool(self.token)
        }


@dataclass
class DeliveryFee:
    """배송비 정보"""
    
    amount: int = 0                            # 배송비 금액
    vat: int = 0                              # 배송비 부가세
    tax_type: str = "TAX"                     # 세금 타입 (TAX/TAX_FREE)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryFee':
        """딕셔너리에서 배송비 객체 생성"""
        return cls(
            amount=data.get("amount", 0),
            vat=data.get("vat", 0),
            tax_type=data.get("taxType", "TAX")
        )
    
    def get_total_amount(self) -> int:
        """배송비 총액 (배송비 + 부가세)"""
        return self.amount + self.vat
    
    def get_tax_type_name(self) -> str:
        """세금 타입 한글명"""
        return TAX_TYPE.get(self.tax_type, self.tax_type)


@dataclass
class RevenueItem:
    """매출 아이템 정보"""
    
    vendor_item_id: str                        # 판매자 상품 ID
    item_name: str                            # 상품명
    recognition_date: str                     # 매출 인식일 (YYYY-MM-DD)
    sale_type: str                            # 매출 타입 (SALE/REFUND)
    settlement_amount: int                    # 정산금액
    service_fee: int = 0                      # 서비스 수수료
    vat: int = 0                             # 부가세
    order_id: Optional[str] = None           # 주문 ID
    item_id: Optional[str] = None            # 아이템 ID
    category_id: Optional[str] = None        # 카테고리 ID
    brand_name: Optional[str] = None         # 브랜드명
    delivery_fee: Optional[DeliveryFee] = None  # 배송비 정보
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RevenueItem':
        """딕셔너리에서 매출 아이템 객체 생성"""
        delivery_fee = None
        if "deliveryFee" in data and data["deliveryFee"]:
            delivery_fee = DeliveryFee.from_dict(data["deliveryFee"])
        
        return cls(
            vendor_item_id=str(data.get("vendorItemId", "")),
            item_name=data.get("itemName", ""),
            recognition_date=data.get("recognitionDate", ""),
            sale_type=data.get("saleType", "SALE"),
            settlement_amount=data.get("settlementAmount", 0),
            service_fee=data.get("serviceFee", 0),
            vat=data.get("vat", 0),
            order_id=data.get("orderId"),
            item_id=data.get("itemId"),
            category_id=data.get("categoryId"),
            brand_name=data.get("brandName"),
            delivery_fee=delivery_fee
        )
    
    def get_sale_type_name(self) -> str:
        """매출 타입 한글명"""
        return SALE_TYPE.get(self.sale_type, self.sale_type)
    
    def get_net_amount(self) -> int:
        """순 매출액 (정산금액 - 서비스 수수료)"""
        return self.settlement_amount - self.service_fee
    
    def get_gross_amount(self) -> int:
        """총 매출액 (정산금액 + 부가세)"""
        return self.settlement_amount + self.vat
    
    def get_total_delivery_fee(self) -> int:
        """총 배송비"""
        if self.delivery_fee:
            return self.delivery_fee.get_total_amount()
        return 0
    
    def is_refund(self) -> bool:
        """환불 여부"""
        return self.sale_type == "REFUND"
    
    def is_sale(self) -> bool:
        """판매 여부"""
        return self.sale_type == "SALE"
    
    def get_recognition_datetime(self) -> datetime:
        """매출 인식일을 datetime 객체로 변환"""
        return datetime.strptime(self.recognition_date, '%Y-%m-%d')
    
    def get_summary(self) -> Dict[str, Any]:
        """매출 아이템 요약"""
        return {
            "vendor_item_id": self.vendor_item_id,
            "item_name": self.item_name[:50] + "..." if len(self.item_name) > 50 else self.item_name,
            "recognition_date": self.recognition_date,
            "sale_type": self.get_sale_type_name(),
            "settlement_amount": self.settlement_amount,
            "net_amount": self.get_net_amount(),
            "has_delivery_fee": bool(self.delivery_fee),
            "is_refund": self.is_refund()
        }


@dataclass
class RevenueHistory:
    """매출내역 응답 데이터"""
    
    items: List[RevenueItem] = field(default_factory=list)  # 매출 아이템 목록
    total_count: int = 0                                    # 전체 건수
    has_next: bool = False                                  # 다음 페이지 존재 여부
    next_token: Optional[str] = None                        # 다음 페이지 토큰
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RevenueHistory':
        """딕셔너리에서 매출내역 객체 생성"""
        items = []
        
        # 매출 아이템 리스트 처리
        revenue_list = data.get("data", {}).get("revenueList", [])
        for item_data in revenue_list:
            items.append(RevenueItem.from_dict(item_data))
        
        return cls(
            items=items,
            total_count=len(items),
            has_next=data.get("data", {}).get("hasNext", False),
            next_token=data.get("data", {}).get("nextToken")
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """매출 요약 통계"""
        if not self.items:
            return {
                "total_items": 0,
                "total_settlement": 0,
                "total_service_fee": 0,
                "total_vat": 0,
                "net_revenue": 0,
                "sale_count": 0,
                "refund_count": 0,
                "sale_amount": 0,
                "refund_amount": 0
            }
        
        total_settlement = sum(item.settlement_amount for item in self.items)
        total_service_fee = sum(item.service_fee for item in self.items)
        total_vat = sum(item.vat for item in self.items)
        
        sale_items = [item for item in self.items if item.is_sale()]
        refund_items = [item for item in self.items if item.is_refund()]
        
        sale_amount = sum(item.settlement_amount for item in sale_items)
        refund_amount = sum(abs(item.settlement_amount) for item in refund_items)
        
        return {
            "total_items": len(self.items),
            "total_settlement": total_settlement,
            "total_service_fee": total_service_fee,
            "total_vat": total_vat,
            "net_revenue": total_settlement - total_service_fee,
            "sale_count": len(sale_items),
            "refund_count": len(refund_items),
            "sale_amount": sale_amount,
            "refund_amount": refund_amount,
            "net_profit": sale_amount - refund_amount - total_service_fee
        }
    
    def get_items_by_date(self, target_date: str) -> List[RevenueItem]:
        """특정 날짜의 매출 아이템 조회"""
        return [item for item in self.items if item.recognition_date == target_date]
    
    def get_items_by_type(self, sale_type: str) -> List[RevenueItem]:
        """특정 매출 타입의 아이템 조회"""
        return [item for item in self.items if item.sale_type == sale_type]
    
    def get_top_revenue_items(self, count: int = 10) -> List[RevenueItem]:
        """매출 상위 아이템 조회"""
        return sorted(self.items, key=lambda x: x.settlement_amount, reverse=True)[:count]
    
    def group_by_date(self) -> Dict[str, List[RevenueItem]]:
        """날짜별 매출 아이템 그룹핑"""
        grouped = {}
        for item in self.items:
            date_key = item.recognition_date
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(item)
        return grouped
    
    def get_pagination_info(self) -> Dict[str, Any]:
        """페이지네이션 정보"""
        return {
            "total_count": self.total_count,
            "current_page_count": len(self.items),
            "has_next": self.has_next,
            "has_next_token": bool(self.next_token)
        }


@dataclass
class RevenueHistoryResponse:
    """매출내역 조회 API 응답"""
    
    success: bool = True                                    # 성공 여부
    message: str = ""                                      # 응답 메시지
    data: Optional[RevenueHistory] = None                  # 매출내역 데이터
    search_params: Optional[RevenueSearchParams] = None    # 검색 파라미터
    timestamp: str = ""                                    # 응답 시간
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any], 
                  search_params: Optional[RevenueSearchParams] = None) -> 'RevenueHistoryResponse':
        """딕셔너리에서 응답 객체 생성"""
        revenue_history = RevenueHistory.from_dict(response_data)
        
        return cls(
            success=True,
            message="매출내역 조회 성공",
            data=revenue_history,
            search_params=search_params,
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def create_error_response(cls, error_message: str, 
                            search_params: Optional[RevenueSearchParams] = None) -> 'RevenueHistoryResponse':
        """오류 응답 생성"""
        return cls(
            success=False,
            message=error_message,
            data=None,
            search_params=search_params,
            timestamp=datetime.now().isoformat()
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """응답 요약 통계"""
        if not self.data:
            return {"error": "데이터가 없습니다"}
        
        stats = self.data.get_summary_stats()
        
        # 검색 파라미터 정보 추가
        if self.search_params:
            stats.update({
                "search_period": f"{self.search_params.recognition_date_from} ~ {self.search_params.recognition_date_to}",
                "search_days": self.search_params.get_date_range_days(),
                "vendor_id": self.search_params.vendor_id
            })
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        result = {
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.data:
            result["data"] = {
                "items": [item.__dict__ for item in self.data.items],
                "summary_stats": self.data.get_summary_stats(),
                "pagination_info": self.data.get_pagination_info()
            }
        
        if self.search_params:
            result["search_params"] = self.search_params.get_summary()
        
        return result


@dataclass
class RevenueSummaryReport:
    """매출 요약 보고서"""
    
    period_summary: Dict[str, Any] = field(default_factory=dict)     # 기간별 요약
    daily_breakdown: Dict[str, Any] = field(default_factory=dict)    # 일별 분석
    top_items: List[Dict[str, Any]] = field(default_factory=list)    # 상위 아이템
    trends: Dict[str, Any] = field(default_factory=dict)             # 트렌드 분석
    recommendations: List[str] = field(default_factory=list)         # 추천사항
    
    @classmethod
    def create_from_revenue_data(cls, revenue_items: List[RevenueItem],
                               search_params: RevenueSearchParams) -> 'RevenueSummaryReport':
        """매출 데이터로부터 요약 보고서 생성"""
        if not revenue_items:
            return cls()
        
        # 기간별 요약 계산
        total_settlement = sum(item.settlement_amount for item in revenue_items)
        total_service_fee = sum(item.service_fee for item in revenue_items)
        
        period_summary = {
            "total_items": len(revenue_items),
            "total_settlement": total_settlement,
            "total_service_fee": total_service_fee,
            "net_revenue": total_settlement - total_service_fee,
            "period_days": search_params.get_date_range_days(),
            "avg_daily_revenue": total_settlement / search_params.get_date_range_days()
        }
        
        # 일별 분석
        daily_data = {}
        for item in revenue_items:
            date_key = item.recognition_date
            if date_key not in daily_data:
                daily_data[date_key] = {"items": 0, "settlement": 0, "service_fee": 0}
            
            daily_data[date_key]["items"] += 1
            daily_data[date_key]["settlement"] += item.settlement_amount
            daily_data[date_key]["service_fee"] += item.service_fee
        
        # 상위 아이템 (매출액 기준)
        top_items = []
        sorted_items = sorted(revenue_items, key=lambda x: x.settlement_amount, reverse=True)
        for item in sorted_items[:10]:
            top_items.append({
                "vendor_item_id": item.vendor_item_id,
                "item_name": item.item_name,
                "settlement_amount": item.settlement_amount,
                "recognition_date": item.recognition_date,
                "sale_type": item.get_sale_type_name()
            })
        
        # 추천사항 생성
        recommendations = []
        if total_settlement > 0:
            service_fee_ratio = (total_service_fee / total_settlement) * 100
            if service_fee_ratio > 15:
                recommendations.append(f"서비스 수수료 비율이 {service_fee_ratio:.1f}%로 높습니다. 수수료 최적화를 검토해보세요.")
        
        refund_items = [item for item in revenue_items if item.is_refund()]
        if refund_items:
            refund_ratio = (len(refund_items) / len(revenue_items)) * 100
            if refund_ratio > 10:
                recommendations.append(f"환불 비율이 {refund_ratio:.1f}%로 높습니다. 상품 품질을 점검해보세요.")
        
        return cls(
            period_summary=period_summary,
            daily_breakdown=daily_data,
            top_items=top_items,
            trends={},  # 추후 구현
            recommendations=recommendations
        )