#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 유틸리티 함수들
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from collections import defaultdict, Counter

from .constants import ANSWERED_TYPE

# 공통 모듈 import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import config


def generate_inquiry_date_range_for_recent_days(days: int) -> Tuple[str, str]:
    """
    최근 N일간의 날짜 범위 생성 (고객문의 조회용)
    
    Args:
        days: 조회할 일수 (1~7일)
        
    Returns:
        Tuple[str, str]: (시작일, 종료일) yyyy-MM-dd 형식
    """
    if days < 1 or days > 7:
        raise ValueError("조회 기간은 1~7일 사이여야 합니다")
    
    # 현재 날짜
    today = datetime.now().date()
    
    # 종료일: 오늘
    end_date = today.strftime('%Y-%m-%d')
    
    # 시작일: N일 전
    start_date = (today - timedelta(days=days-1)).strftime('%Y-%m-%d')
    
    return start_date, end_date


def generate_inquiry_date_range_for_today() -> Tuple[str, str]:
    """
    오늘의 날짜 범위 생성 (고객문의 조회용)
    
    Returns:
        Tuple[str, str]: (오늘, 오늘) yyyy-MM-dd 형식
    """
    today = datetime.now().date().strftime('%Y-%m-%d')
    return today, today


def analyze_inquiry_patterns(inquiry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    고객문의 패턴 분석
    
    Args:
        inquiry_data: 고객문의 데이터 리스트
        
    Returns:
        Dict[str, Any]: 분석 결과
    """
    if not inquiry_data:
        return {
            "total_inquiries": 0,
            "patterns": {},
            "recommendations": []
        }
    
    # 기본 통계
    total_inquiries = len(inquiry_data)
    
    # 답변 상태별 분포
    answered_distribution = Counter()
    for inquiry in inquiry_data:
        if inquiry.get("is_answered", False):
            answered_distribution["ANSWERED"] += 1
        else:
            answered_distribution["NOANSWER"] += 1
    
    # 시간대별 분포 (시간별)
    hourly_distribution = defaultdict(int)
    for inquiry in inquiry_data:
        inquiry_at = inquiry.get("inquiry_at", "")
        if inquiry_at:
            try:
                # "2019-06-25 01:10:04" 형식 파싱
                dt = datetime.strptime(inquiry_at, '%Y-%m-%d %H:%M:%S')
                hourly_distribution[dt.hour] += 1
            except ValueError:
                continue
    
    # 요일별 분포
    weekday_distribution = defaultdict(int)
    for inquiry in inquiry_data:
        inquiry_at = inquiry.get("inquiry_at", "")
        if inquiry_at:
            try:
                dt = datetime.strptime(inquiry_at, '%Y-%m-%d %H:%M:%S')
                weekday_distribution[dt.strftime('%A')] += 1
            except ValueError:
                continue
    
    # 주문 관련 문의 분포
    order_related_count = sum(1 for inquiry in inquiry_data if len(inquiry.get("order_ids", [])) > 0)
    
    # 상품별 문의 분포
    product_distribution = Counter()
    for inquiry in inquiry_data:
        product_id = inquiry.get("product_id")
        if product_id:
            product_distribution[product_id] += 1
    
    # 문의 응답 시간 분석
    response_time_analysis = analyze_response_times(inquiry_data)
    
    # 개선 권장사항 생성
    recommendations = generate_inquiry_recommendations(
        answered_distribution, hourly_distribution, order_related_count, total_inquiries
    )
    
    return {
        "total_inquiries": total_inquiries,
        "patterns": {
            "answered_distribution": dict(answered_distribution),
            "hourly_distribution": dict(hourly_distribution),
            "weekday_distribution": dict(weekday_distribution),
            "order_related_count": order_related_count,
            "order_related_rate": order_related_count / total_inquiries * 100 if total_inquiries > 0 else 0,
            "top_products": dict(product_distribution.most_common(5))
        },
        "response_analysis": response_time_analysis,
        "recommendations": recommendations
    }


def analyze_response_times(inquiry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    문의 응답 시간 분석
    
    Args:
        inquiry_data: 고객문의 데이터 리스트
        
    Returns:
        Dict[str, Any]: 응답 시간 분석 결과
    """
    response_times = []
    
    for inquiry in inquiry_data:
        if not inquiry.get("is_answered", False):
            continue
        
        inquiry_at = inquiry.get("inquiry_at", "")
        latest_answer_at = inquiry.get("latest_answer_at", "")
        
        if inquiry_at and latest_answer_at:
            try:
                inquiry_dt = datetime.strptime(inquiry_at, '%Y-%m-%d %H:%M:%S')
                answer_dt = datetime.strptime(latest_answer_at, '%Y-%m-%d %H:%M:%S')
                
                response_time_hours = (answer_dt - inquiry_dt).total_seconds() / 3600
                if response_time_hours >= 0:  # 유효한 응답 시간만
                    response_times.append(response_time_hours)
            except ValueError:
                continue
    
    if not response_times:
        return {
            "average_response_hours": 0,
            "median_response_hours": 0,
            "min_response_hours": 0,
            "max_response_hours": 0,
            "total_answered": 0
        }
    
    response_times.sort()
    count = len(response_times)
    
    return {
        "average_response_hours": sum(response_times) / count,
        "median_response_hours": response_times[count // 2],
        "min_response_hours": min(response_times),
        "max_response_hours": max(response_times),
        "total_answered": count,
        "fast_response_count": sum(1 for rt in response_times if rt <= 24),  # 24시간 이내
        "slow_response_count": sum(1 for rt in response_times if rt > 72)   # 72시간 초과
    }


def generate_inquiry_recommendations(answered_distribution: Counter, 
                                   hourly_distribution: defaultdict,
                                   order_related_count: int,
                                   total_inquiries: int) -> List[str]:
    """
    고객문의 개선 권장사항 생성
    
    Args:
        answered_distribution: 답변 상태별 분포
        hourly_distribution: 시간대별 분포
        order_related_count: 주문 관련 문의 수
        total_inquiries: 전체 문의 수
        
    Returns:
        List[str]: 권장사항 리스트
    """
    recommendations = []
    
    # 미답변 비율 체크
    unanswered_count = answered_distribution.get("NOANSWER", 0)
    if total_inquiries > 0:
        unanswered_rate = unanswered_count / total_inquiries * 100
        
        if unanswered_rate > 50:
            recommendations.extend([
                "🚨 미답변 문의가 많습니다 (50% 초과). 즉시 대응이 필요합니다",
                "📋 문의 대응 프로세스를 점검하고 자동 응답 시스템 도입을 고려해보세요",
                "👥 고객서비스 담당자 증원 또는 업무 분담을 검토해주세요"
            ])
        elif unanswered_rate > 20:
            recommendations.append("⚠️ 미답변 문의 비율을 낮추기 위한 대응 계획이 필요합니다 (20% 초과)")
    
    # 주문 관련 문의 비율 체크
    if total_inquiries > 0:
        order_rate = order_related_count / total_inquiries * 100
        
        if order_rate > 60:
            recommendations.extend([
                "📦 주문 관련 문의가 많습니다. 주문/배송 프로세스를 점검해주세요",
                "📍 배송 추적 정보를 더 자세히 제공하는 것을 권장합니다",
                "🔔 주문 상태 변경 시 자동 알림 시스템을 구축해보세요"
            ])
    
    # 피크 시간대 분석
    if hourly_distribution:
        peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hour_list = [str(hour) for hour, count in peak_hours]
        recommendations.append(f"⏰ 문의가 많은 시간대({', '.join(peak_hour_list)}시)에 충분한 상담 인력을 배치해주세요")
    
    # 일반적인 권장사항
    if len(recommendations) == 0:
        recommendations.extend([
            "📊 정기적인 고객문의 패턴 분석을 통해 서비스를 개선해주세요",
            "💬 자주 묻는 질문(FAQ)을 정리하여 고객이 쉽게 찾을 수 있도록 해주세요",
            "🎯 문의 유형별 맞춤형 대응 가이드라인을 마련해주세요"
        ])
    
    return recommendations


def create_inquiry_summary_report(inquiry_data: List[Dict[str, Any]], 
                                analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    고객문의 요약 보고서 생성
    
    Args:
        inquiry_data: 고객문의 데이터 리스트
        analysis_result: 분석 결과
        
    Returns:
        Dict[str, Any]: 요약 보고서
    """
    if not inquiry_data:
        return {
            "summary": "분석할 고객문의 데이터가 없습니다",
            "key_metrics": {},
            "response_performance": {},
            "recommendations": []
        }
    
    total_count = len(inquiry_data)
    patterns = analysis_result.get("patterns", {})
    response_analysis = analysis_result.get("response_analysis", {})
    
    # 핵심 지표
    answered_count = patterns.get("answered_distribution", {}).get("ANSWERED", 0)
    unanswered_count = patterns.get("answered_distribution", {}).get("NOANSWER", 0)
    
    key_metrics = {
        "total_inquiries": total_count,
        "answered_count": answered_count,
        "unanswered_count": unanswered_count,
        "answer_rate": answered_count / total_count * 100 if total_count > 0 else 0,
        "order_related_rate": patterns.get("order_related_rate", 0),
        "average_response_hours": response_analysis.get("average_response_hours", 0)
    }
    
    # 응답 성과
    response_performance = {
        "total_answered": response_analysis.get("total_answered", 0),
        "average_response_hours": response_analysis.get("average_response_hours", 0),
        "median_response_hours": response_analysis.get("median_response_hours", 0),
        "fast_response_count": response_analysis.get("fast_response_count", 0),
        "slow_response_count": response_analysis.get("slow_response_count", 0),
        "fast_response_rate": (response_analysis.get("fast_response_count", 0) / 
                             max(response_analysis.get("total_answered", 1), 1) * 100)
    }
    
    # 종합 평가
    if key_metrics["answer_rate"] >= 90:
        overall_status = "🟢 우수"
    elif key_metrics["answer_rate"] >= 70:
        overall_status = "🟡 보통"
    else:
        overall_status = "🔴 개선 필요"
    
    return {
        "summary": f"총 {total_count}건의 고객문의 분석 완료",
        "overall_status": overall_status,
        "key_metrics": key_metrics,
        "response_performance": response_performance,
        "patterns": patterns,
        "recommendations": analysis_result.get("recommendations", [])
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
    고객문의 API 사용을 위한 환경설정 검증
    
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


def create_sample_inquiry_search_params(days: int = 1, 
                                       answered_type: str = "ALL") -> Dict[str, Any]:
    """
    .env 기반 샘플 고객문의 검색 파라미터 생성
    
    Args:
        days: 조회 기간 (일수)
        answered_type: 답변 상태
        
    Returns:
        Dict[str, Any]: 검색 파라미터 딕셔너리
    """
    start_date, end_date = generate_inquiry_date_range_for_recent_days(days)
    
    return {
        "vendor_id": get_default_vendor_id(),
        "answered_type": answered_type,
        "inquiry_start_at": start_date,
        "inquiry_end_at": end_date,
        "page_size": 10
    }