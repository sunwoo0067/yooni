#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 반품/취소 요청 관리 클라이언트
반품/취소 요청 목록 조회 기능
"""

import urllib.parse
from typing import Dict, Any, Optional, List

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import BaseCoupangClient, error_handler
from .models import (
    ReturnRequestSearchParams, ReturnRequestListResponse, ReturnRequestDetailResponse, ReturnRequest,
    ReturnWithdrawRequest, ReturnWithdrawListResponse, ReturnInvoiceCreateResponse
)
from .constants import (
    RETURN_REQUESTS_API_PATH, RETURN_REQUEST_DETAIL_API_PATH, RETURN_STATUS, CANCEL_TYPE,
    RETURN_RECEIVE_CONFIRMATION_API_PATH, RETURN_APPROVAL_API_PATH, RETURN_WITHDRAW_REQUESTS_API_PATH,
    RETURN_WITHDRAW_BY_IDS_API_PATH, RETURN_EXCHANGE_INVOICE_API_PATH, RECEIPT_STATUS_FOR_RECEIVE_CONFIRMATION,
    RECEIPT_STATUS_FOR_APPROVAL, MAX_WITHDRAW_DATE_RANGE_DAYS, MAX_CANCEL_IDS_PER_REQUEST
)
from .validators import validate_search_params
from .utils import (
    create_return_summary_report, generate_date_range_for_recent_days,
    generate_timeframe_range_for_recent_hours
)


class ReturnClient(BaseCoupangClient):
    """쿠팡 반품/취소 요청 관리 API 클라이언트"""
    
    def get_api_name(self) -> str:
        """API 이름 반환"""
        return "반품/취소 요청 관리 API"
    
    def get_return_requests(self, search_params: ReturnRequestSearchParams) -> Dict[str, Any]:
        """
        반품/취소 요청 목록 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 반품/취소 요청 목록 조회 결과
            
        Raises:
            ValueError: 잘못된 검색 파라미터
        """
        # 검색 파라미터 검증
        validate_search_params(search_params)
        
        # API 경로 생성
        api_path = RETURN_REQUESTS_API_PATH.format(search_params.vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = search_params.to_query_params()
        api_path_with_params = f"{api_path}?{query_params}"
        
        try:
            # API 호출
            response = self.execute_api_request("GET", api_path_with_params, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                return_response = ReturnRequestListResponse.from_dict(response)
                
                # 요약 통계 계산
                summary_stats = return_response.get_summary_stats()
                
                return error_handler.handle_api_success(
                    response,
                    default_message="반품/취소 요청 목록 조회 성공",
                    vendor_id=search_params.vendor_id,
                    search_type=search_params.search_type,
                    date_range=f"{search_params.created_at_from} ~ {search_params.created_at_to}",
                    total_count=summary_stats["total_count"],
                    summary_stats=summary_stats,
                    next_token=return_response.next_token
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 412:
                    return error_handler.handle_api_error(response, "조회 시간이 초과되었습니다. 조회 기간을 줄여서 재시도해주세요.")
                elif response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "검색기간" in error_message:
                        return error_handler.handle_api_error(response, "조회 기간이 31일을 초과했습니다. 기간을 줄여서 다시 시도해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품/취소 요청 목록 조회 API 호출")
    
    def get_return_request_detail(self, vendor_id: str, receipt_id) -> Dict[str, Any]:
        """
        반품/취소 요청 단건 조회
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 취소(반품)접수번호
            
        Returns:
            Dict[str, Any]: 반품/취소 요청 단건 조회 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        validated_receipt_id = self.validate_receipt_id(receipt_id)
        
        # API 경로 생성
        api_path = RETURN_REQUEST_DETAIL_API_PATH.format(vendor_id, validated_receipt_id)
        
        try:
            # API 호출
            response = self.execute_api_request("GET", api_path, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                detail_response = ReturnRequestDetailResponse.from_dict(response)
                
                # 단건 조회 결과 확인
                return_request = detail_response.get_return_request()
                if not return_request:
                    return error_handler.handle_api_error({"code": 404, "message": "반품 요청을 찾을 수 없습니다."})
                
                # 상세 정보 추가
                detailed_info = detail_response.get_detailed_info()
                
                # 처리 우선순위 판정
                priority_level = self._get_processing_priority(return_request)
                
                # 출고중지 필요 여부 확인
                stop_release_required = return_request.is_stop_release_required()
                stop_release_items = return_request.get_stop_release_items()
                
                return error_handler.handle_api_success(
                    response,
                    default_message="반품/취소 요청 단건 조회 성공",
                    vendor_id=vendor_id,
                    receipt_id=validated_receipt_id,
                    return_request=return_request.to_dict(),
                    detailed_info=detailed_info,
                    priority_level=priority_level,
                    stop_release_required=stop_release_required,
                    stop_release_items_count=len(stop_release_items),
                    processing_recommendations=self._get_processing_recommendations(return_request)
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "doesn't belong to the vendorId" in error_message or "cannot find the Receipt" in error_message:
                        return error_handler.handle_api_error(response, "해당 접수번호를 찾을 수 없거나 철회된 반품 요청입니다. 반품철회 이력을 확인해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품/취소 요청 단건 조회 API 호출")
    
    def get_return_request_with_analysis(self, vendor_id: str, receipt_id) -> Dict[str, Any]:
        """
        반품/취소 요청 단건 조회 (상세 분석 포함)
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 취소(반품)접수번호
            
        Returns:
            Dict[str, Any]: 분석 정보가 포함된 단건 조회 결과
        """
        result = self.get_return_request_detail(vendor_id, receipt_id)
        
        if not result.get("success"):
            return result
        
        return_request_data = result.get("return_request", {})
        return_request = ReturnRequest.from_dict(return_request_data)
        
        # 추가 분석 정보
        analysis = {
            "timeline_analysis": self._analyze_processing_timeline(return_request),
            "risk_assessment": self._assess_return_risk(return_request),
            "action_items": self._generate_action_items(return_request),
            "similar_cases_insight": self._get_similar_cases_insight(return_request)
        }
        
        result["analysis"] = analysis
        return result
    
    def _get_processing_priority(self, return_request: ReturnRequest) -> str:
        """처리 우선순위 판정"""
        # 출고중지 요청이고 미처리인 경우 최고 우선순위
        if return_request.is_stop_release_required():
            return "URGENT"
        
        # 쿠팡 또는 협력사 과실인 경우 높은 우선순위
        if return_request.fault_by_type in ["COUPANG", "VENDOR"]:
            return "HIGH"
        
        # 빠른환불 대상인 경우 중간 우선순위
        if return_request.pre_refund:
            return "MEDIUM"
        
        # 그 외는 일반 우선순위
        return "NORMAL"
    
    def _get_processing_recommendations(self, return_request: ReturnRequest) -> List[str]:
        """처리 권장사항 생성"""
        recommendations = []
        
        if return_request.is_stop_release_required():
            recommendations.append("🚨 즉시 출고중지 처리 필요")
            recommendations.append("📦 해당 상품의 발송을 중단해주세요")
        
        if return_request.fault_by_type == "VENDOR":
            recommendations.append("⚠️ 협력사 과실로 분류됨 - 프로세스 개선 검토 필요")
        
        if return_request.pre_refund:
            recommendations.append("💰 빠른환불 대상 - 신속한 처리 필요")
        
        if return_request.return_delivery_type == "":
            recommendations.append("📮 회수 상품 없음 - 환불 처리만 진행")
        
        if return_request.complete_confirm_type == "UNDEFINED":
            recommendations.append("✅ 처리 완료 후 확인 상태 업데이트 필요")
        
        if not recommendations:
            recommendations.append("📋 표준 프로세스에 따라 처리")
        
        return recommendations
    
    def _analyze_processing_timeline(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """처리 타임라인 분석"""
        from datetime import datetime
        
        try:
            created_at = datetime.fromisoformat(return_request.created_at.replace('T', ' '))
            modified_at = datetime.fromisoformat(return_request.modified_at.replace('T', ' ')) if return_request.modified_at else created_at
            now = datetime.now()
            
            hours_since_created = (now - created_at).total_seconds() / 3600
            hours_since_modified = (now - modified_at).total_seconds() / 3600
            
            return {
                "created_hours_ago": round(hours_since_created, 1),
                "last_modified_hours_ago": round(hours_since_modified, 1),
                "processing_status": "진행중" if return_request.receipt_status != "RETURNS_COMPLETED" else "완료",
                "urgency_level": "높음" if hours_since_created > 24 else "보통"
            }
        except:
            return {"error": "타임라인 분석 실패"}
    
    def _assess_return_risk(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """반품 리스크 평가"""
        risk_factors = []
        risk_score = 0
        
        # 귀책 타입별 리스크
        if return_request.fault_by_type == "VENDOR":
            risk_factors.append("협력사 과실")
            risk_score += 3
        elif return_request.fault_by_type == "COUPANG":
            risk_factors.append("쿠팡 과실")
            risk_score += 2
        
        # 반품 사유별 리스크
        if "불량" in return_request.reason_code_text:
            risk_factors.append("상품 불량")
            risk_score += 2
        elif "변심" in return_request.reason_code_text:
            risk_factors.append("단순 변심")
            risk_score += 1
        
        # 금액별 리스크
        if abs(return_request.return_shipping_charge) > 5000:
            risk_factors.append("높은 배송비")
            risk_score += 1
        
        # 리스크 레벨 결정
        if risk_score >= 5:
            risk_level = "높음"
        elif risk_score >= 3:
            risk_level = "중간"
        else:
            risk_level = "낮음"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors
        }
    
    def _generate_action_items(self, return_request: ReturnRequest) -> List[Dict[str, Any]]:
        """액션 아이템 생성"""
        action_items = []
        
        if return_request.is_stop_release_required():
            action_items.append({
                "priority": "URGENT",
                "action": "출고중지 처리",
                "description": "해당 상품의 발송을 즉시 중단",
                "estimated_time": "즉시"
            })
        
        if return_request.receipt_status == "RETURNS_UNCHECKED":
            action_items.append({
                "priority": "HIGH",
                "action": "반품 접수 확인",
                "description": "반품 사유 및 상태 검토",
                "estimated_time": "1시간"
            })
        
        if return_request.return_delivery_type and return_request.return_delivery_type != "":
            action_items.append({
                "priority": "MEDIUM",
                "action": "회수 배송 준비",
                "description": f"{return_request.return_delivery_type} 회수 준비",
                "estimated_time": "2-4시간"
            })
        
        return action_items
    
    def _get_similar_cases_insight(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """유사 사례 인사이트"""
        return {
            "reason_category": return_request.cancel_reason_category1,
            "common_pattern": f"{return_request.reason_code_text} 사유는 일반적인 반품 사유입니다",
            "prevention_tip": "상품 설명 개선 및 품질 관리 강화를 통해 유사 반품을 예방할 수 있습니다" if "불량" in return_request.reason_code_text else "정확한 상품 정보 제공으로 변심 반품을 줄일 수 있습니다"
        }
    
    def get_return_requests_all_pages(self, search_params: ReturnRequestSearchParams) -> Dict[str, Any]:
        """
        반품/취소 요청 목록 전체 페이지 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            Dict[str, Any]: 전체 페이지 조회 결과
        """
        if search_params.search_type == "timeFrame":
            # timeFrame은 페이징을 지원하지 않으므로 단일 호출
            return self.get_return_requests(search_params)
        
        all_requests = []
        page_count = 0
        current_params = search_params
        
        try:
            while True:
                page_count += 1
                print(f"🔄 {page_count}페이지 조회 중...")
                
                result = self.get_return_requests(current_params)
                
                if not result.get("success"):
                    return result
                
                page_data = result.get("data", [])
                all_requests.extend(page_data)
                
                # 다음 페이지 확인
                next_token = result.get("next_token")
                if not next_token:
                    break
                
                # 다음 페이지 파라미터 설정
                current_params.next_token = next_token
                
                # 안전장치: 최대 100페이지까지만
                if page_count >= 100:
                    print("⚠️ 최대 페이지 수(100)에 도달했습니다.")
                    break
            
            # 전체 결과 요약
            summary_report = create_return_summary_report(
                [ReturnRequest.from_dict(item) for item in all_requests]
            )
            
            return handle_api_success(
                {"data": all_requests},
                default_message=f"반품/취소 요청 목록 전체 조회 완료 ({page_count}페이지)",
                vendor_id=search_params.vendor_id,
                total_count=len(all_requests),
                page_count=page_count,
                summary_report=summary_report
            )
            
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품/취소 요청 목록 전체 페이지 조회")
    
    def get_return_requests_by_status(self, vendor_id: str, created_at_from: str, 
                                    created_at_to: str, status: str, 
                                    search_type: str = "daily",
                                    max_per_page: int = 50) -> Dict[str, Any]:
        """
        특정 상태의 반품/취소 요청 조회 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일
            created_at_to: 검색 종료일
            status: 반품 상태 (RU, UC, CC, PR)
            search_type: 검색 타입
            max_per_page: 페이지당 최대 조회 수
            
        Returns:
            Dict[str, Any]: 상태별 반품/취소 요청 조회 결과
        """
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type=search_type,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status=status,
            max_per_page=max_per_page
        )
        
        return self.get_return_requests_all_pages(params)
    
    def get_cancel_requests(self, vendor_id: str, created_at_from: str, 
                          created_at_to: str, search_type: str = "daily") -> Dict[str, Any]:
        """
        취소 요청 목록 조회 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일
            created_at_to: 검색 종료일
            search_type: 검색 타입
            
        Returns:
            Dict[str, Any]: 취소 요청 목록 조회 결과
        """
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type=search_type,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            cancel_type="CANCEL"
        )
        
        return self.get_return_requests_all_pages(params)
    
    def get_stop_release_requests(self, vendor_id: str, created_at_from: str, 
                                created_at_to: str) -> Dict[str, Any]:
        """
        출고중지 요청 목록 조회 (편의 메서드)
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일
            created_at_to: 검색 종료일
            
        Returns:
            Dict[str, Any]: 출고중지 요청 목록 조회 결과
        """
        return self.get_return_requests_by_status(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            status="RU"  # 출고중지요청
        )
    
    def get_recent_return_requests(self, vendor_id: str, days: int = 7) -> Dict[str, Any]:
        """
        최근 N일간 반품/취소 요청 조회
        
        Args:
            vendor_id: 판매자 ID
            days: 조회할 일수 (기본 7일)
            
        Returns:
            Dict[str, Any]: 최근 반품/취소 요청 조회 결과
        """
        created_at_from, created_at_to = generate_date_range_for_recent_days(days)
        
        params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type="daily",
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            cancel_type="RETURN"
        )
        
        result = self.get_return_requests_all_pages(params)
        
        if result.get("success"):
            result["date_range_description"] = f"최근 {days}일간"
        
        return result
    
    def get_return_summary_by_date_range(self, vendor_id: str, created_at_from: str, 
                                       created_at_to: str) -> Dict[str, Any]:
        """
        날짜 범위별 반품/취소 요약 정보 조회
        
        Args:
            vendor_id: 판매자 ID
            created_at_from: 검색 시작일
            created_at_to: 검색 종료일
            
        Returns:
            Dict[str, Any]: 반품/취소 요약 정보
        """
        # 반품 요청 조회
        return_params = ReturnRequestSearchParams(
            vendor_id=vendor_id,
            search_type="daily",
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            cancel_type="RETURN"
        )
        
        return_result = self.get_return_requests_all_pages(return_params)
        
        # 취소 요청 조회
        cancel_result = self.get_cancel_requests(
            vendor_id=vendor_id,
            created_at_from=created_at_from,
            created_at_to=created_at_to
        )
        
        if not return_result.get("success") or not cancel_result.get("success"):
            return {
                "success": False,
                "error": "반품/취소 요약 정보 조회 실패",
                "return_result": return_result,
                "cancel_result": cancel_result
            }
        
        # 통합 요약 정보 생성
        return_requests = [ReturnRequest.from_dict(item) for item in return_result.get("data", [])]
        cancel_requests = [ReturnRequest.from_dict(item) for item in cancel_result.get("data", [])]
        
        return_summary = create_return_summary_report(return_requests)
        cancel_summary = create_return_summary_report(cancel_requests)
        
        total_summary = {
            "date_range": f"{created_at_from} ~ {created_at_to}",
            "return_requests": {
                "count": return_summary["total_count"],
                "cancel_items": return_summary["total_cancel_items"],
                "stop_release_required": return_summary["stop_release_required"],
                "status_summary": return_summary["status_summary"]
            },
            "cancel_requests": {
                "count": cancel_summary["total_count"],
                "cancel_items": cancel_summary["total_cancel_items"]
            },
            "total_requests": return_summary["total_count"] + cancel_summary["total_count"],
            "total_cancel_items": return_summary["total_cancel_items"] + cancel_summary["total_cancel_items"],
            "urgent_action_required": return_summary.get("urgent_action_required", False)
        }
        
        return handle_api_success(
            {"return_requests": return_result["data"], "cancel_requests": cancel_result["data"]},
            default_message="반품/취소 요약 정보 조회 성공",
            total_summary=total_summary
        )
    
    def confirm_return_receive(self, vendor_id: str, receipt_id) -> Dict[str, Any]:
        """
        반품상품 입고 확인 처리
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 취소(반품)접수번호
            
        Returns:
            Dict[str, Any]: 반품상품 입고 확인 처리 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        validated_receipt_id = self.validate_receipt_id(receipt_id)
        
        # API 경로 생성
        api_path = RETURN_RECEIVE_CONFIRMATION_API_PATH.format(vendor_id, validated_receipt_id)
        
        # 요청 데이터
        request_data = {
            "vendorId": vendor_id,
            "receiptId": validated_receipt_id
        }
        
        try:
            # API 호출
            response = self.execute_api_request("PATCH", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == 200:
                return error_handler.handle_api_success(
                    response,
                    default_message="반품상품 입고 확인 처리 성공",
                    vendor_id=vendor_id,
                    receipt_id=validated_receipt_id,
                    action="receive_confirmation"
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "취소반품접수내역이 존재하지 않습니다" in error_message:
                        return error_handler.handle_api_error(response, "접수된 반품내역이 고객 또는 상담사에 의해 철회되었거나 잘못된 접수번호입니다. 반품철회 이력을 확인해주세요.")
                    elif "이미 반품이 완료" in error_message:
                        return error_handler.handle_api_error(response, "이미 반품이 완료된 건입니다. 중복 처리를 방지해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품상품 입고 확인 처리 API 호출")
    
    def approve_return_request(self, vendor_id: str, receipt_id, cancel_count: int) -> Dict[str, Any]:
        """
        반품요청 승인 처리
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 취소(반품)접수번호
            cancel_count: 반품접수 수량
            
        Returns:
            Dict[str, Any]: 반품요청 승인 처리 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        validated_receipt_id = self.validate_receipt_id(receipt_id)
        
        if not isinstance(cancel_count, int) or cancel_count <= 0:
            raise ValueError("반품접수 수량은 1 이상의 정수여야 합니다.")
        
        # API 경로 생성
        api_path = RETURN_APPROVAL_API_PATH.format(vendor_id, validated_receipt_id)
        
        # 요청 데이터
        request_data = {
            "vendorId": vendor_id,
            "receiptId": validated_receipt_id,
            "cancelCount": cancel_count
        }
        
        try:
            # API 호출
            response = self.execute_api_request("PATCH", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == 200:
                return error_handler.handle_api_success(
                    response,
                    default_message="반품요청 승인 처리 성공",
                    vendor_id=vendor_id,
                    receipt_id=validated_receipt_id,
                    cancel_count=cancel_count,
                    action="approval"
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "취소반품접수내역이 존재하지 않습니다" in error_message:
                        return error_handler.handle_api_error(response, "접수된 반품내역이 고객 또는 상담사에 의해 철회되었거나 잘못된 접수번호입니다.")
                    elif "이미 반품이 완료" in error_message:
                        return error_handler.handle_api_error(response, "이미 반품이 완료된 건입니다.")
                    elif "cancelCount가 일치하지 않습니다" in error_message:
                        return error_handler.handle_api_error(response, "반품접수 수량과 입력한 cancelCount가 일치하지 않습니다. 올바른 수량을 입력해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품요청 승인 처리 API 호출")
    
    def get_return_withdraw_requests(self, vendor_id: str, date_from: str, date_to: str, 
                                   page_index: int = 1, size_per_page: int = 10) -> Dict[str, Any]:
        """
        반품철회 이력 기간별 조회
        
        Args:
            vendor_id: 판매자 ID
            date_from: 조회 시작일 (yyyy-MM-dd)
            date_to: 조회 종료일 (yyyy-MM-dd)
            page_index: 페이지 인덱스 (기본값: 1)
            size_per_page: 페이지당 조회 수 (기본값: 10, 최대: 100)
            
        Returns:
            Dict[str, Any]: 반품철회 이력 조회 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        
        # 날짜 형식 검증 (간단한 형태)
        if not date_from or not date_to:
            raise ValueError("조회 시작일과 종료일을 입력해주세요.")
        
        if size_per_page > 100 or size_per_page < 1:
            raise ValueError("페이지당 조회 수는 1-100 사이여야 합니다.")
        
        if page_index < 1:
            raise ValueError("페이지 인덱스는 1 이상이어야 합니다.")
        
        # API 경로 생성
        api_path = RETURN_WITHDRAW_REQUESTS_API_PATH.format(vendor_id)
        
        # 쿼리 파라미터 추가
        query_params = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'pageIndex': str(page_index),
            'sizePerPage': str(size_per_page)
        }
        query_string = urllib.parse.urlencode(query_params)
        api_path_with_params = f"{api_path}?{query_string}"
        
        try:
            # API 호출
            response = self.execute_api_request("GET", api_path_with_params, {})
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                withdraw_response = ReturnWithdrawListResponse.from_dict(response)
                
                return error_handler.handle_api_success(
                    response,
                    default_message="반품철회 이력 조회 성공",
                    vendor_id=vendor_id,
                    date_range=f"{date_from} ~ {date_to}",
                    total_count=len(withdraw_response.data),
                    page_index=page_index,
                    size_per_page=size_per_page,
                    next_page_index=withdraw_response.next_page_index,
                    withdraw_requests=[req.to_dict() for req in withdraw_response.data]
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "최대 조회 기간은 7 일" in error_message:
                        return error_handler.handle_api_error(response, "조회 기간은 최대 7일까지만 가능합니다.")
                    elif "종료일자는 시작일자보다" in error_message:
                        return error_handler.handle_api_error(response, "조회 시작일과 종료일을 올바르게 입력해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품철회 이력 조회 API 호출")
    
    def get_return_withdraw_by_cancel_ids(self, vendor_id: str, cancel_ids: List[int]) -> Dict[str, Any]:
        """
        반품철회 이력 접수번호로 조회
        
        Args:
            vendor_id: 판매자 ID
            cancel_ids: 취소(반품)접수번호 목록 (최대 50개)
            
        Returns:
            Dict[str, Any]: 반품철회 이력 조회 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        
        if not cancel_ids:
            raise ValueError("조회할 접수번호 목록을 입력해주세요.")
        
        if len(cancel_ids) > MAX_CANCEL_IDS_PER_REQUEST:
            raise ValueError(f"한 번에 최대 {MAX_CANCEL_IDS_PER_REQUEST}개까지 조회 가능합니다.")
        
        # 접수번호 검증
        for cancel_id in cancel_ids:
            if not isinstance(cancel_id, int) or cancel_id <= 0:
                raise ValueError("접수번호는 양의 정수여야 합니다.")
        
        # API 경로 생성
        api_path = RETURN_WITHDRAW_BY_IDS_API_PATH.format(vendor_id)
        
        # 요청 데이터
        request_data = {
            "cancelIds": cancel_ids
        }
        
        try:
            # API 호출
            response = self.execute_api_request("POST", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                withdraw_requests = [ReturnWithdrawRequest.from_dict(item) for item in response.get('data', [])]
                
                return error_handler.handle_api_success(
                    response,
                    default_message="반품철회 이력 접수번호 조회 성공",
                    vendor_id=vendor_id,
                    requested_cancel_ids=cancel_ids,
                    found_count=len(withdraw_requests),
                    withdraw_requests=[req.to_dict() for req in withdraw_requests]
                )
            else:
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품철회 이력 접수번호 조회 API 호출")
    
    def create_return_exchange_invoice(self, vendor_id: str, receipt_id, delivery_company_code: str,
                                     invoice_number: str, return_exchange_delivery_type: str = "RETURN",
                                     reg_number: Optional[str] = None) -> Dict[str, Any]:
        """
        회수 송장 등록
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 반품 또는 교환 접수ID
            delivery_company_code: 택배사 코드
            invoice_number: 운송장번호
            return_exchange_delivery_type: 반품 또는 교환 (RETURN 또는 EXCHANGE)
            reg_number: 택배사 회수번호 (선택사항)
            
        Returns:
            Dict[str, Any]: 회수 송장 등록 결과
            
        Raises:
            ValueError: 잘못된 파라미터
        """
        # 파라미터 검증
        self.validate_vendor_id(vendor_id)
        validated_receipt_id = self.validate_receipt_id(receipt_id)
        
        if not delivery_company_code:
            raise ValueError("택배사 코드를 입력해주세요.")
        
        if not invoice_number:
            raise ValueError("운송장번호를 입력해주세요.")
        
        if return_exchange_delivery_type not in ["RETURN", "EXCHANGE"]:
            raise ValueError("반품/교환 타입은 'RETURN' 또는 'EXCHANGE'여야 합니다.")
        
        # API 경로 생성
        api_path = RETURN_EXCHANGE_INVOICE_API_PATH.format(vendor_id)
        
        # 요청 데이터
        request_data = {
            "returnExchangeDeliveryType": return_exchange_delivery_type,
            "receiptId": validated_receipt_id,
            "deliveryCompanyCode": delivery_company_code,
            "invoiceNumber": invoice_number
        }
        
        if reg_number:
            request_data["regNumber"] = reg_number
        
        try:
            # API 호출
            response = self.execute_api_request("POST", api_path, request_data)
            
            # 응답 처리
            if response.get("code") == 200:
                # 구조화된 응답 생성
                invoice_response = ReturnInvoiceCreateResponse.from_dict(response.get('data', {}))
                
                return error_handler.handle_api_success(
                    response,
                    default_message="회수 송장 등록 성공",
                    vendor_id=vendor_id,
                    receipt_id=validated_receipt_id,
                    invoice_data=invoice_response.to_dict(),
                    delivery_company_code=delivery_company_code,
                    invoice_number=invoice_number
                )
            else:
                # 특별한 오류 처리
                if response.get("code") == 400:
                    error_message = response.get("message", "")
                    if "배송송장과 같은 송장번호" in error_message:
                        return error_handler.handle_api_error(response, "배송처리 시 입력한 송장과 동일한 회수 송장번호입니다. 새로운 회수 송장번호를 입력해주세요.")
                    elif "반품 송장 형식이 올바르지 않습니다" in error_message:
                        return error_handler.handle_api_error(response, "올바른 회수 송장번호와 택배사를 입력해주세요.")
                elif response.get("code") == 500:
                    error_message = response.get("message", "")
                    if "Invalid value for DeliveryCompanyCodeEnum" in error_message:
                        return error_handler.handle_api_error(response, "지원되지 않는 택배사 코드입니다. 올바른 택배사 코드를 입력해주세요.")
                
                return error_handler.handle_api_error(response)
                
        except Exception as e:
            return error_handler.handle_exception_error(e, "회수 송장 등록 API 호출")
    
    def process_return_workflow(self, vendor_id: str, receipt_id, cancel_count: int = None) -> Dict[str, Any]:
        """
        반품 처리 워크플로우 (입고확인 -> 승인 처리)
        
        Args:
            vendor_id: 판매자 ID
            receipt_id: 취소(반품)접수번호
            cancel_count: 반품접수 수량 (승인 처리시 필요, None이면 단건 조회로 확인)
            
        Returns:
            Dict[str, Any]: 반품 처리 워크플로우 결과
        """
        workflow_results = []
        
        try:
            # 1. 현재 상태 확인
            detail_result = self.get_return_request_detail(vendor_id, receipt_id)
            if not detail_result.get("success"):
                return detail_result
            
            return_request_data = detail_result.get("return_request", {})
            current_status = return_request_data.get("receiptStatus", "")
            
            workflow_results.append({
                "step": "status_check",
                "current_status": current_status,
                "success": True
            })
            
            # 2. 입고 확인 처리 (RETURNS_UNCHECKED 상태인 경우)
            if current_status in RECEIPT_STATUS_FOR_RECEIVE_CONFIRMATION:
                print("🔄 반품상품 입고 확인 처리 중...")
                receive_result = self.confirm_return_receive(vendor_id, receipt_id)
                workflow_results.append({
                    "step": "receive_confirmation",
                    "result": receive_result,
                    "success": receive_result.get("success", False)
                })
                
                if not receive_result.get("success"):
                    return {
                        "success": False,
                        "error": "입고 확인 처리 실패",
                        "workflow_results": workflow_results
                    }
                
                print("✅ 반품상품 입고 확인 처리 완료")
                
                # 잠시 대기 후 상태 재확인
                import time
                time.sleep(1)
                
                # 상태 재확인
                detail_result = self.get_return_request_detail(vendor_id, receipt_id)
                if detail_result.get("success"):
                    return_request_data = detail_result.get("return_request", {})
                    current_status = return_request_data.get("receiptStatus", "")
            
            # 3. 승인 처리 (VENDOR_WAREHOUSE_CONFIRM 상태인 경우)
            if current_status in RECEIPT_STATUS_FOR_APPROVAL:
                # cancel_count가 없으면 현재 정보에서 가져오기
                if cancel_count is None:
                    cancel_count = return_request_data.get("cancelCountSum", 1)
                
                print("🔄 반품요청 승인 처리 중...")
                approval_result = self.approve_return_request(vendor_id, receipt_id, cancel_count)
                workflow_results.append({
                    "step": "approval",
                    "result": approval_result,
                    "success": approval_result.get("success", False)
                })
                
                if approval_result.get("success"):
                    print("✅ 반품요청 승인 처리 완료")
                else:
                    print("❌ 반품요청 승인 처리 실패")
            
            # 4. 최종 상태 확인
            final_detail_result = self.get_return_request_detail(vendor_id, receipt_id)
            if final_detail_result.get("success"):
                final_status = final_detail_result.get("return_request", {}).get("receiptStatus", "")
                workflow_results.append({
                    "step": "final_status_check",
                    "final_status": final_status,
                    "success": True
                })
            
            return handle_api_success(
                {},
                default_message="반품 처리 워크플로우 완료",
                vendor_id=vendor_id,
                receipt_id=receipt_id,
                workflow_results=workflow_results,
                total_steps=len(workflow_results)
            )
            
        except Exception as e:
            return error_handler.handle_exception_error(e, "반품 처리 워크플로우")
    
