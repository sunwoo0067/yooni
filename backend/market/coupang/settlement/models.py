#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 지급내역 조회 모듈 데이터 모델
"""

import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .constants import SETTLEMENT_TYPE, SETTLEMENT_STATUS


@dataclass
class SettlementSearchParams:
    """지급내역 검색 파라미터"""
    
    revenue_recognition_year_month: str    # 매출인식월 (YYYY-MM, 필수)
    
    def to_query_params(self) -> str:
        """쿼리 파라미터 문자열 생성"""
        params = {
            "revenueRecognitionYearMonth": self.revenue_recognition_year_month
        }
        
        return urllib.parse.urlencode(params)
    
    def get_year(self) -> int:
        """매출인식월에서 연도 추출"""
        return int(self.revenue_recognition_year_month.split('-')[0])
    
    def get_month(self) -> int:
        """매출인식월에서 월 추출"""
        return int(self.revenue_recognition_year_month.split('-')[1])
    
    def get_summary(self) -> Dict[str, Any]:
        """검색 파라미터 요약"""
        return {
            "revenue_recognition_year_month": self.revenue_recognition_year_month,
            "year": self.get_year(),
            "month": self.get_month()
        }


@dataclass
class SettlementHistory:
    """지급내역 정보"""
    
    settlement_type: str                           # 정산유형 (MONTHLY/WEEKLY/DAILY/ADDITIONAL/RESERVE)
    settlement_date: str                           # 정산(예정)일
    revenue_recognition_year_month: str            # 매출인식월
    revenue_recognition_date_from: str             # 매출인식시작일
    revenue_recognition_date_to: str               # 매출인식종료일
    total_sale: int                                # 총판매액
    service_fee: int                               # 판매수수료
    settlement_target_amount: int                  # 정산대상액
    settlement_amount: int                         # 지급액
    last_amount: int                              # 최종액 (유보성격의 금액)
    pending_released_amount: int                   # 보류(해제)금액
    seller_discount_coupon: int                    # 판매자 할인쿠폰 (즉시할인쿠폰)
    downloadable_coupon: int                       # 판매자 할인쿠폰 (다운로드쿠폰)
    dedicated_delivery_amount: int                 # 전담택배비
    seller_service_fee: int                        # 판매자서비스이용료(서버이용료)
    courantee_fee: int                            # 쿠런티이용료
    courantee_customer_reward: int                 # 쿠런티보상금
    deduction_amount: int                          # 정산차감
    debt_of_last_week: int                        # 전주채권
    final_amount: int                             # 최종지급액 or 지급예정액
    bank_account_holder: str                       # 예금주
    bank_name: str                                # 은행명
    bank_account: str                             # 정산대금 입금 계좌번호 (**뒤 4자리 마스킹)
    status: str                                   # 지급 상태 (DONE/SUBJECT)
    store_fee_discount: int = 0                   # 셀러 스토어 이용료 할인 금액
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SettlementHistory':
        """딕셔너리에서 지급내역 객체 생성"""
        return cls(
            settlement_type=data.get("settlementType", ""),
            settlement_date=data.get("settlementDate", ""),
            revenue_recognition_year_month=data.get("revenueRecognitionYearMonth", ""),
            revenue_recognition_date_from=data.get("revenueRecognitionDateFrom", ""),
            revenue_recognition_date_to=data.get("revenueRecognitionDateTo", ""),
            total_sale=data.get("totalSale", 0),
            service_fee=data.get("serviceFee", 0),
            settlement_target_amount=data.get("settlementTargetAmount", 0),
            settlement_amount=data.get("settlementAmount", 0),
            last_amount=data.get("lastAmount", 0),
            pending_released_amount=data.get("pendingReleasedAmount", 0),
            seller_discount_coupon=data.get("sellerDiscountCoupon", 0),
            downloadable_coupon=data.get("downloadableCoupon", 0),
            dedicated_delivery_amount=data.get("dedicatedDeliveryAmount", 0),
            seller_service_fee=data.get("sellerServiceFee", 0),
            courantee_fee=data.get("couranteeFee", 0),
            courantee_customer_reward=data.get("couranteeCustomerReward", 0),
            deduction_amount=data.get("deductionAmount", 0),
            debt_of_last_week=data.get("debtOfLastWeek", 0),
            final_amount=data.get("finalAmount", 0),
            bank_account_holder=data.get("bankAccountHolder", ""),
            bank_name=data.get("bankName", ""),
            bank_account=data.get("bankAccount", ""),
            status=data.get("status", ""),
            store_fee_discount=data.get("storeFeeDiscount", 0)
        )
    
    def get_settlement_type_name(self) -> str:
        """정산유형 한글명"""
        return SETTLEMENT_TYPE.get(self.settlement_type, self.settlement_type)
    
    def get_status_name(self) -> str:
        """지급 상태 한글명"""
        return SETTLEMENT_STATUS.get(self.status, self.status)
    
    def get_net_amount(self) -> int:
        """순 정산액 (정산대상액)"""
        return self.settlement_target_amount
    
    def get_total_deduction(self) -> int:
        """총 차감액"""
        return (
            self.dedicated_delivery_amount +
            self.seller_service_fee +
            self.courantee_fee +
            self.courantee_customer_reward +
            self.deduction_amount +
            self.debt_of_last_week +
            self.seller_discount_coupon +
            self.downloadable_coupon +
            self.store_fee_discount
        )
    
    def get_service_fee_ratio(self) -> float:
        """판매수수료 비율 (%)"""
        if self.total_sale == 0:
            return 0.0
        return (self.service_fee / self.total_sale) * 100
    
    def get_deduction_ratio(self) -> float:
        """차감액 비율 (%)"""
        if self.settlement_amount == 0:
            return 0.0
        return (self.get_total_deduction() / self.settlement_amount) * 100
    
    def is_settlement_completed(self) -> bool:
        """지급 완료 여부"""
        return self.status == "DONE"
    
    def is_settlement_pending(self) -> bool:
        """지급 예정 여부"""
        return self.status == "SUBJECT"
    
    def get_settlement_datetime(self) -> datetime:
        """정산일을 datetime 객체로 변환"""
        return datetime.strptime(self.settlement_date, '%Y-%m-%d')
    
    def get_masked_bank_info(self) -> Dict[str, str]:
        """마스킹된 은행 정보"""
        return {
            "bank_name": self.bank_name,
            "account_holder": self.bank_account_holder,
            "account_number": self.bank_account
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """지급내역 요약"""
        return {
            "settlement_type": self.get_settlement_type_name(),
            "settlement_date": self.settlement_date,
            "revenue_recognition_year_month": self.revenue_recognition_year_month,
            "total_sale": self.total_sale,
            "service_fee": self.service_fee,
            "settlement_target_amount": self.settlement_target_amount,
            "settlement_amount": self.settlement_amount,
            "final_amount": self.final_amount,
            "status": self.get_status_name(),
            "service_fee_ratio": round(self.get_service_fee_ratio(), 2),
            "deduction_ratio": round(self.get_deduction_ratio(), 2),
            "is_completed": self.is_settlement_completed()
        }
    
    def get_detailed_breakdown(self) -> Dict[str, Any]:
        """상세 지급내역 분석"""
        return {
            "revenue_breakdown": {
                "total_sale": self.total_sale,
                "service_fee": self.service_fee,
                "settlement_target_amount": self.settlement_target_amount,
                "service_fee_ratio": round(self.get_service_fee_ratio(), 2)
            },
            "settlement_breakdown": {
                "settlement_amount": self.settlement_amount,
                "pending_released_amount": self.pending_released_amount,
                "last_amount": self.last_amount,
                "final_amount": self.final_amount
            },
            "deduction_breakdown": {
                "seller_discount_coupon": self.seller_discount_coupon,
                "downloadable_coupon": self.downloadable_coupon,
                "dedicated_delivery_amount": self.dedicated_delivery_amount,
                "seller_service_fee": self.seller_service_fee,
                "courantee_fee": self.courantee_fee,
                "courantee_customer_reward": self.courantee_customer_reward,
                "deduction_amount": self.deduction_amount,
                "debt_of_last_week": self.debt_of_last_week,
                "store_fee_discount": self.store_fee_discount,
                "total_deduction": self.get_total_deduction()
            },
            "payment_info": {
                "bank_name": self.bank_name,
                "account_holder": self.bank_account_holder,
                "account_number": self.bank_account,
                "status": self.get_status_name(),
                "settlement_date": self.settlement_date
            }
        }


@dataclass
class SettlementHistoryResponse:
    """지급내역 조회 API 응답"""
    
    success: bool = True                                    # 성공 여부
    message: str = ""                                      # 응답 메시지
    data: List[SettlementHistory] = field(default_factory=list)  # 지급내역 목록
    search_params: Optional[SettlementSearchParams] = None  # 검색 파라미터
    timestamp: str = ""                                    # 응답 시간
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any], 
                  search_params: Optional[SettlementSearchParams] = None) -> 'SettlementHistoryResponse':
        """딕셔너리에서 응답 객체 생성"""
        settlements = []
        
        # 지급내역 리스트가 직접 반환되는 구조
        if isinstance(response_data, list):
            for settlement_data in response_data:
                settlements.append(SettlementHistory.from_dict(settlement_data))
        elif isinstance(response_data, dict) and "data" in response_data:
            # data 필드가 있는 경우
            settlement_list = response_data.get("data", [])
            for settlement_data in settlement_list:
                settlements.append(SettlementHistory.from_dict(settlement_data))
        
        return cls(
            success=True,
            message="지급내역 조회 성공",
            data=settlements,
            search_params=search_params,
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def create_error_response(cls, error_message: str, 
                            search_params: Optional[SettlementSearchParams] = None) -> 'SettlementHistoryResponse':
        """오류 응답 생성"""
        return cls(
            success=False,
            message=error_message,
            data=[],
            search_params=search_params,
            timestamp=datetime.now().isoformat()
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """응답 요약 통계"""
        if not self.data:
            return {
                "total_settlements": 0,
                "total_sale": 0,
                "total_service_fee": 0,
                "total_settlement_amount": 0,
                "total_final_amount": 0,
                "completed_count": 0,
                "pending_count": 0
            }
        
        total_sale = sum(settlement.total_sale for settlement in self.data)
        total_service_fee = sum(settlement.service_fee for settlement in self.data)
        total_settlement_amount = sum(settlement.settlement_amount for settlement in self.data)
        total_final_amount = sum(settlement.final_amount for settlement in self.data)
        
        completed_settlements = [s for s in self.data if s.is_settlement_completed()]
        pending_settlements = [s for s in self.data if s.is_settlement_pending()]
        
        # 평균 수수료 비율 계산
        avg_service_fee_ratio = 0
        if total_sale > 0:
            avg_service_fee_ratio = (total_service_fee / total_sale) * 100
        
        stats = {
            "total_settlements": len(self.data),
            "total_sale": total_sale,
            "total_service_fee": total_service_fee,
            "total_settlement_amount": total_settlement_amount,
            "total_final_amount": total_final_amount,
            "completed_count": len(completed_settlements),
            "pending_count": len(pending_settlements),
            "avg_service_fee_ratio": round(avg_service_fee_ratio, 2),
            "net_settlement_amount": total_settlement_amount - total_service_fee
        }
        
        # 검색 파라미터 정보 추가
        if self.search_params:
            stats.update({
                "search_year_month": self.search_params.revenue_recognition_year_month,
                "search_year": self.search_params.get_year(),
                "search_month": self.search_params.get_month()
            })
        
        return stats
    
    def get_settlements_by_type(self, settlement_type: str) -> List[SettlementHistory]:
        """특정 정산유형의 지급내역 조회"""
        return [settlement for settlement in self.data if settlement.settlement_type == settlement_type]
    
    def get_settlements_by_status(self, status: str) -> List[SettlementHistory]:
        """특정 상태의 지급내역 조회"""
        return [settlement for settlement in self.data if settlement.status == status]
    
    def get_completed_settlements(self) -> List[SettlementHistory]:
        """완료된 지급내역 조회"""
        return self.get_settlements_by_status("DONE")
    
    def get_pending_settlements(self) -> List[SettlementHistory]:
        """예정된 지급내역 조회"""
        return self.get_settlements_by_status("SUBJECT")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        result = {
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.data:
            result["data"] = {
                "settlements": [settlement.__dict__ for settlement in self.data],
                "summary_stats": self.get_summary_stats()
            }
        
        if self.search_params:
            result["search_params"] = self.search_params.get_summary()
        
        return result


@dataclass
class SettlementSummaryReport:
    """지급내역 요약 보고서"""
    
    period_summary: Dict[str, Any] = field(default_factory=dict)     # 기간별 요약
    monthly_breakdown: Dict[str, Any] = field(default_factory=dict)  # 월별 분석
    type_breakdown: Dict[str, Any] = field(default_factory=dict)     # 정산유형별 분석
    trends: Dict[str, Any] = field(default_factory=dict)             # 트렌드 분석
    recommendations: List[str] = field(default_factory=list)         # 추천사항
    
    @classmethod
    def create_from_settlement_data(cls, settlements: List[SettlementHistory],
                                  analysis_months: int = 3) -> 'SettlementSummaryReport':
        """지급내역 데이터로부터 요약 보고서 생성"""
        if not settlements:
            return cls()
        
        # 기간별 요약 계산
        total_sale = sum(s.total_sale for s in settlements)
        total_service_fee = sum(s.service_fee for s in settlements)
        total_final_amount = sum(s.final_amount for s in settlements)
        
        period_summary = {
            "total_settlements": len(settlements),
            "total_sale": total_sale,
            "total_service_fee": total_service_fee,
            "total_final_amount": total_final_amount,
            "analysis_months": analysis_months,
            "avg_monthly_sale": total_sale / analysis_months if analysis_months > 0 else 0,
            "avg_service_fee_ratio": (total_service_fee / total_sale * 100) if total_sale > 0 else 0
        }
        
        # 월별 분석
        monthly_data = {}
        for settlement in settlements:
            month_key = settlement.revenue_recognition_year_month
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "settlements": 0, "total_sale": 0, 
                    "service_fee": 0, "final_amount": 0
                }
            
            monthly_data[month_key]["settlements"] += 1
            monthly_data[month_key]["total_sale"] += settlement.total_sale
            monthly_data[month_key]["service_fee"] += settlement.service_fee
            monthly_data[month_key]["final_amount"] += settlement.final_amount
        
        # 정산유형별 분석
        type_data = {}
        for settlement in settlements:
            settlement_type = settlement.settlement_type
            if settlement_type not in type_data:
                type_data[settlement_type] = {
                    "count": 0, "total_amount": 0, "avg_amount": 0
                }
            
            type_data[settlement_type]["count"] += 1
            type_data[settlement_type]["total_amount"] += settlement.final_amount
        
        # 평균 계산
        for type_key in type_data:
            count = type_data[type_key]["count"]
            if count > 0:
                type_data[type_key]["avg_amount"] = type_data[type_key]["total_amount"] / count
        
        # 추천사항 생성
        recommendations = []
        avg_service_fee_ratio = period_summary["avg_service_fee_ratio"]
        
        if avg_service_fee_ratio > 20:
            recommendations.append(f"🔍 판매수수료 비율이 {avg_service_fee_ratio:.1f}%로 높습니다. 수수료 최적화를 검토하세요.")
        
        if len(settlements) < 5:
            recommendations.append("📈 지급내역이 적습니다. 매출 증대 방안을 검토하세요.")
        
        completed_settlements = [s for s in settlements if s.is_settlement_completed()]
        if len(completed_settlements) < len(settlements):
            pending_count = len(settlements) - len(completed_settlements)
            recommendations.append(f"⏳ {pending_count}건의 지급 예정 내역이 있습니다.")
        
        return cls(
            period_summary=period_summary,
            monthly_breakdown=monthly_data,
            type_breakdown=type_data,
            trends={},  # 추후 구현
            recommendations=recommendations
        )