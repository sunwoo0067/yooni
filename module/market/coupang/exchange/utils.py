#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 유틸리티 함수들
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from collections import defaultdict, Counter

from .constants import VOC_CODES, EXCHANGE_STATUS, EXCHANGE_FAULT_TYPE

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import config


def generate_exchange_date_range_for_recent_days(days: int) -> Tuple[str, str]:
    """
    최근 N일간의 날짜 범위 생성 (교환요청 조회용)
    
    Args:
        days: 조회할 일수 (1~7일)
        
    Returns:
        Tuple[str, str]: (시작일시, 종료일시) yyyy-MM-ddTHH:mm:ss 형식
    """
    if days < 1 or days > 7:
        raise ValueError("조회 기간은 1~7일 사이여야 합니다")
    
    # 현재 시각
    now = datetime.now()
    
    # 종료일시: 현재 시각
    to_date = now.strftime('%Y-%m-%dT%H:%M:%S')
    
    # 시작일시: N일 전
    from_date = (now - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S')
    
    return from_date, to_date


def generate_exchange_date_range_for_today() -> Tuple[str, str]:
    """
    오늘의 날짜 범위 생성 (교환요청 조회용)
    
    Returns:
        Tuple[str, str]: (오늘 00:00:00, 현재시각) yyyy-MM-ddTHH:mm:ss 형식
    """
    now = datetime.now()
    
    # 오늘 시작 시각 (00:00:00)
    today_start = now.replace(hour=0, minute=0, second=0)
    from_date = today_start.strftime('%Y-%m-%dT%H:%M:%S')
    
    # 현재 시각
    to_date = now.strftime('%Y-%m-%dT%H:%M:%S')
    
    return from_date, to_date


def analyze_exchange_patterns(exchange_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    교환요청 패턴 분석
    
    Args:
        exchange_data: 교환요청 데이터 리스트
        
    Returns:
        Dict[str, Any]: 분석 결과
    """
    if not exchange_data:
        return {
            "total_exchanges": 0,
            "patterns": {},
            "recommendations": []
        }
    
    # 기본 통계
    total_exchanges = len(exchange_data)
    
    # 상태별 분포
    status_distribution = Counter(req.get("exchange_status", "") for req in exchange_data)
    
    # 귀책별 분포
    fault_distribution = Counter(req.get("fault_type", "") for req in exchange_data)
    
    # 사유 코드별 분포
    reason_distribution = Counter(req.get("reason_code", "") for req in exchange_data)
    
    # 접수 경로별 분포
    refer_type_distribution = Counter(req.get("refer_type", "") for req in exchange_data)
    
    # 시간대별 분포 (시간별)
    hourly_distribution = defaultdict(int)
    for req in exchange_data:
        created_at = req.get("created_at", "")
        if created_at:
            try:
                dt = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S')
                hourly_distribution[dt.hour] += 1
            except ValueError:
                continue
    
    # 위험 패턴 감지
    risk_patterns = detect_exchange_risk_patterns(exchange_data)
    
    # 개선 권장사항 생성
    recommendations = generate_exchange_recommendations(
        fault_distribution, reason_distribution, risk_patterns
    )
    
    return {
        "total_exchanges": total_exchanges,
        "patterns": {
            "status_distribution": dict(status_distribution),
            "fault_distribution": dict(fault_distribution),
            "reason_distribution": dict(reason_distribution),
            "refer_type_distribution": dict(refer_type_distribution),
            "hourly_distribution": dict(hourly_distribution)
        },
        "risk_patterns": risk_patterns,
        "recommendations": recommendations
    }


def detect_exchange_risk_patterns(exchange_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    교환요청 위험 패턴 감지
    
    Args:
        exchange_data: 교환요청 데이터 리스트
        
    Returns:
        Dict[str, Any]: 위험 패턴 분석 결과
    """
    risk_patterns = {
        "high_vendor_fault_rate": False,
        "frequent_product_defects": False,
        "delivery_issues": False,
        "customer_dissatisfaction": False,
        "risk_score": 0,
        "alerts": []
    }
    
    if not exchange_data:
        return risk_patterns
    
    total_count = len(exchange_data)
    
    # 업체 과실 비율 체크
    vendor_fault_count = sum(1 for req in exchange_data if req.get("fault_type") == "VENDOR")
    vendor_fault_rate = vendor_fault_count / total_count
    
    if vendor_fault_rate > 0.3:  # 30% 이상
        risk_patterns["high_vendor_fault_rate"] = True
        risk_patterns["alerts"].append("업체 과실 교환 비율이 높습니다 (30% 이상)")
        risk_patterns["risk_score"] += 3
    
    # 상품 결함 관련 교환 체크
    defect_reasons = ["DAMAGED", "DEFECT", "INACCURATE", "BOTHDAMAGED", "SHIPBOXOK"]
    defect_count = sum(1 for req in exchange_data 
                      if req.get("reason_code") in defect_reasons)
    defect_rate = defect_count / total_count
    
    if defect_rate > 0.2:  # 20% 이상
        risk_patterns["frequent_product_defects"] = True
        risk_patterns["alerts"].append("상품 결함 관련 교환이 빈발합니다 (20% 이상)")
        risk_patterns["risk_score"] += 2
    
    # 배송 관련 문제 체크
    delivery_reasons = ["DELIVERYSTOP", "CARRIERLOST", "LOST", "LATEDELIVERED", 
                       "WRONGDELIVERY", "WRONGSIZECOL"]
    delivery_count = sum(1 for req in exchange_data 
                        if req.get("reason_code") in delivery_reasons)
    delivery_rate = delivery_count / total_count
    
    if delivery_rate > 0.15:  # 15% 이상
        risk_patterns["delivery_issues"] = True
        risk_patterns["alerts"].append("배송 관련 교환 문제가 증가하고 있습니다 (15% 이상)")
        risk_patterns["risk_score"] += 2
    
    # 고객 불만 관련 체크
    dissatisfaction_reasons = ["DONTLIKESIZECOLOR", "DIFFERENTOPT", "INACCURATE"]
    dissatisfaction_count = sum(1 for req in exchange_data 
                               if req.get("reason_code") in dissatisfaction_reasons)
    dissatisfaction_rate = dissatisfaction_count / total_count
    
    if dissatisfaction_rate > 0.25:  # 25% 이상
        risk_patterns["customer_dissatisfaction"] = True
        risk_patterns["alerts"].append("고객 불만족 관련 교환이 증가하고 있습니다 (25% 이상)")
        risk_patterns["risk_score"] += 1
    
    return risk_patterns


def generate_exchange_recommendations(fault_distribution: Counter, 
                                    reason_distribution: Counter,
                                    risk_patterns: Dict[str, Any]) -> List[str]:
    """
    교환요청 개선 권장사항 생성
    
    Args:
        fault_distribution: 귀책별 분포
        reason_distribution: 사유별 분포
        risk_patterns: 위험 패턴 분석 결과
        
    Returns:
        List[str]: 권장사항 리스트
    """
    recommendations = []
    
    # 업체 과실 비율이 높은 경우
    if risk_patterns.get("high_vendor_fault_rate"):
        recommendations.extend([
            "📋 상품 품질관리 프로세스를 점검해주세요",
            "🔍 출고 전 검수 절차를 강화하는 것을 권장합니다",
            "📞 고객서비스 교육을 통해 사전 문의 대응을 개선해주세요"
        ])
    
    # 상품 결함이 빈발하는 경우
    if risk_patterns.get("frequent_product_defects"):
        recommendations.extend([
            "🏭 제조업체와의 품질 기준 재검토가 필요합니다",
            "📦 포장 및 보관 방법을 개선해주세요",
            "🔧 상품별 취급 주의사항을 명확히 안내해주세요"
        ])
    
    # 배송 문제가 많은 경우
    if risk_patterns.get("delivery_issues"):
        recommendations.extend([
            "🚚 배송업체와의 서비스 품질 점검이 필요합니다",
            "📍 배송지 확인 절차를 강화해주세요",
            "📱 배송 추적 서비스 개선을 검토해주세요"
        ])
    
    # 가장 빈발하는 교환 사유별 권장사항
    if reason_distribution:
        top_reason = reason_distribution.most_common(1)[0][0]
        voc_info = VOC_CODES.get(top_reason, {})
        
        if top_reason == "DIFFERENTOPT":
            recommendations.append("🎨 상품 옵션 정보(색상/사이즈)를 더 명확히 표시해주세요")
        elif top_reason == "DAMAGED":
            recommendations.append("📦 포장재 보강 및 운송 중 파손 방지 대책이 필요합니다")
        elif top_reason == "DEFECT":
            recommendations.append("🔍 출고 전 상품 기능 테스트를 강화해주세요")
        elif top_reason == "WRONGDELIVERY":
            recommendations.append("📋 피킹 및 포장 과정의 정확성을 높여주세요")
    
    # 일반적인 권장사항
    if not recommendations:
        recommendations.extend([
            "📊 정기적인 교환요청 패턴 분석을 통해 예방 조치를 수립해주세요",
            "💬 고객 피드백을 적극 수집하여 서비스 개선에 활용해주세요",
            "🎯 교환 사유별 맞춤형 대응 방안을 마련해주세요"
        ])
    
    return recommendations


def create_exchange_summary_report(exchange_data: List[Dict[str, Any]], 
                                 analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    교환요청 요약 보고서 생성
    
    Args:
        exchange_data: 교환요청 데이터 리스트
        analysis_result: 분석 결과
        
    Returns:
        Dict[str, Any]: 요약 보고서
    """
    if not exchange_data:
        return {
            "summary": "분석할 교환요청 데이터가 없습니다",
            "key_metrics": {},
            "top_issues": [],
            "recommendations": []
        }
    
    total_count = len(exchange_data)
    patterns = analysis_result.get("patterns", {})
    risk_patterns = analysis_result.get("risk_patterns", {})
    
    # 핵심 지표
    key_metrics = {
        "total_exchanges": total_count,
        "vendor_fault_rate": patterns.get("fault_distribution", {}).get("VENDOR", 0) / total_count * 100,
        "completion_rate": patterns.get("status_distribution", {}).get("SUCCESS", 0) / total_count * 100,
        "risk_score": risk_patterns.get("risk_score", 0)
    }
    
    # 주요 이슈 식별
    top_issues = []
    reason_dist = patterns.get("reason_distribution", {})
    
    # 상위 3개 교환 사유
    top_reasons = sorted(reason_dist.items(), key=lambda x: x[1], reverse=True)[:3]
    for reason_code, count in top_reasons:
        voc_info = VOC_CODES.get(reason_code, {})
        top_issues.append({
            "issue": voc_info.get("text", reason_code),
            "count": count,
            "percentage": count / total_count * 100,
            "fault_type": voc_info.get("fault", "")
        })
    
    # 위험 알림
    alerts = risk_patterns.get("alerts", [])
    
    # 종합 평가
    if key_metrics["risk_score"] >= 5:
        overall_status = "🔴 주의 필요"
    elif key_metrics["risk_score"] >= 3:
        overall_status = "🟡 관찰 필요"
    else:
        overall_status = "🟢 양호"
    
    return {
        "summary": f"총 {total_count}건의 교환요청 분석 완료",
        "overall_status": overall_status,
        "key_metrics": key_metrics,
        "top_issues": top_issues,
        "risk_alerts": alerts,
        "patterns": patterns,
        "recommendations": analysis_result.get("recommendations", [])
    }


def calculate_exchange_financial_impact(exchange_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    교환요청의 재정적 영향 계산
    
    Args:
        exchange_data: 교환요청 데이터 리스트
        
    Returns:
        Dict[str, Any]: 재정적 영향 분석
    """
    if not exchange_data:
        return {
            "total_exchange_amount": 0,
            "total_item_value": 0,
            "average_exchange_cost": 0,
            "vendor_fault_cost": 0
        }
    
    total_exchange_amount = 0
    total_item_value = 0
    vendor_fault_cost = 0
    
    for exchange in exchange_data:
        # 교환 배송비
        exchange_amount = exchange.get("exchange_amount", 0)
        total_exchange_amount += exchange_amount
        
        # 교환 상품 가치 계산
        items = exchange.get("exchange_items", [])
        for item in items:
            item_value = item.get("target_item_unit_price", 0) * item.get("quantity", 0)
            total_item_value += item_value
        
        # 업체 과실인 경우 비용 누적
        if exchange.get("fault_type") == "VENDOR":
            vendor_fault_cost += exchange_amount
    
    average_exchange_cost = total_exchange_amount / len(exchange_data) if exchange_data else 0
    
    return {
        "total_exchange_amount": total_exchange_amount,
        "total_item_value": total_item_value,
        "average_exchange_cost": average_exchange_cost,
        "vendor_fault_cost": vendor_fault_cost,
        "vendor_fault_rate": vendor_fault_cost / total_exchange_amount * 100 if total_exchange_amount > 0 else 0
    }


def get_default_vendor_id() -> str:
    """
    .env 파일에서 기본 벤더 ID 가져오기
    
    Returns:
        str: 기본 벤더 ID
        
    Raises:
        ValueError: 벤더 ID가 설정되지 않은 경우
    """
    vendor_id = config.coupang_vendor_id
    if not vendor_id:
        raise ValueError(
            "COUPANG_VENDOR_ID가 .env 파일에 설정되지 않았습니다. "
            "A01409684 형식으로 설정해주세요."
        )
    return vendor_id


def validate_environment_setup() -> Dict[str, Any]:
    """
    교환요청 API 사용을 위한 환경설정 검증
    
    Returns:
        Dict[str, Any]: 검증 결과
    """
    result = {
        "is_valid": False,
        "missing_configs": [],
        "vendor_id": None,
        "message": ""
    }
    
    # 필수 환경변수 확인
    required_configs = {
        "COUPANG_ACCESS_KEY": config.coupang_access_key,
        "COUPANG_SECRET_KEY": config.coupang_secret_key,
        "COUPANG_VENDOR_ID": config.coupang_vendor_id
    }
    
    missing = []
    for key, value in required_configs.items():
        if not value:
            missing.append(key)
    
    if missing:
        result["missing_configs"] = missing
        result["message"] = f"다음 환경변수가 .env 파일에 설정되지 않았습니다: {', '.join(missing)}"
    else:
        result["is_valid"] = True
        result["vendor_id"] = config.coupang_vendor_id
        result["message"] = "환경설정이 올바르게 구성되었습니다."
    
    return result


def create_sample_exchange_search_params(days: int = 1) -> Dict[str, Any]:
    """
    .env 기반 샘플 교환요청 검색 파라미터 생성
    
    Args:
        days: 조회 기간 (일수)
        
    Returns:
        Dict[str, Any]: 검색 파라미터 딕셔너리
    """
    from_date, to_date = generate_exchange_date_range_for_recent_days(days)
    
    return {
        "vendor_id": get_default_vendor_id(),
        "created_at_from": from_date,
        "created_at_to": to_date,
        "max_per_page": 10
    }