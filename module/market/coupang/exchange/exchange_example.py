#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 교환요청 관리 사용 예제
"""

import sys
import os
from datetime import datetime, timedelta

# 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exchange.exchange_client import ExchangeClient
from exchange.models import ExchangeRequestSearchParams
from exchange.utils import (
    generate_exchange_date_range_for_recent_days, validate_environment_setup,
    create_sample_exchange_search_params
)


def print_section(title: str):
    """섹션 제목 출력"""
    print(f"\n{'='*60}")
    print(f"🔸 {title}")
    print('='*60)


def example_basic_exchange_requests():
    """기본 교환요청 목록 조회 예제"""
    print_section("기본 교환요청 목록 조회")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id  # .env에서 자동으로 로드된 벤더 ID 사용
        
        # 검색 파라미터 설정 (최근 1일)
        from_date, to_date = generate_exchange_date_range_for_recent_days(1)
        
        search_params = ExchangeRequestSearchParams(
            vendor_id=vendor_id,
            created_at_from=from_date,
            created_at_to=to_date
        )
        
        print(f"🔍 교환요청 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   기간: {from_date} ~ {to_date}")
        
        result = client.get_exchange_requests(search_params)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   총 건수: {result.get('total_count', 0)}건")
            
            if result.get("summary_stats"):
                stats = result["summary_stats"]
                print(f"   상태별 분포: {stats.get('status_breakdown', {})}")
                print(f"   귀책별 분포: {stats.get('fault_type_breakdown', {})}")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_status_filtered_exchanges():
    """상태별 교환요청 조회 예제"""
    print_section("상태별 교환요청 조회")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        
        # 진행 중인 교환요청만 조회
        from_date, to_date = generate_exchange_date_range_for_recent_days(3)
        
        search_params = ExchangeRequestSearchParams(
            vendor_id=vendor_id,
            created_at_from=from_date,
            created_at_to=to_date,
            status="PROGRESS"  # 진행 중 상태만
        )
        
        print(f"🔍 진행 중인 교환요청 조회 중...")
        print(f"   상태 필터: PROGRESS")
        
        result = client.get_exchange_requests(search_params)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   진행 중인 교환요청: {result.get('total_count', 0)}건")
            
            # 개별 교환요청 정보 출력
            exchanges = result.get("data", [])
            for i, exchange in enumerate(exchanges[:3], 1):  # 최대 3건만 출력
                print(f"   [{i}] 교환 ID: {exchange.get('exchange_id')}")
                print(f"       주문 ID: {exchange.get('order_id')}")
                print(f"       사유: {exchange.get('reason_code_text', 'N/A')}")
                print(f"       귀책: {exchange.get('fault_type_label', 'N/A')}")
        else:
            print(f"❌ 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_today_exchanges():
    """오늘의 교환요청 조회 예제"""
    print_section("오늘의 교환요청 조회")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        
        print(f"📅 오늘의 교환요청 조회 중...")
        
        result = client.get_today_exchange_requests(vendor_id)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   오늘 접수된 교환요청: {result.get('total_count', 0)}건")
            
            if result.get("summary_stats"):
                stats = result["summary_stats"]
                print(f"   업체 과실 건수: {stats.get('vendor_fault_count', 0)}건")
                print(f"   고객 과실 건수: {stats.get('customer_fault_count', 0)}건")
                print(f"   처리 가능 건수: {stats.get('actionable_count', 0)}건")
        else:
            print(f"❌ 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_vendor_fault_exchanges():
    """업체 과실 교환요청 조회 예제"""
    print_section("업체 과실 교환요청 조회")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        
        print(f"⚠️  업체 과실 교환요청 조회 중 (최근 7일)...")
        
        result = client.get_vendor_fault_exchanges(vendor_id, days=7)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   업체 과실 교환요청: {result.get('total_count', 0)}건")
            print(f"   과실률: {result.get('fault_rate', 0):.1f}%")
            
            # 업체 과실 교환요청 상세 정보
            exchanges = result.get("data", [])
            if exchanges:
                print(f"\n   📋 상세 내역:")
                for i, exchange in enumerate(exchanges[:5], 1):  # 최대 5건
                    print(f"   [{i}] 교환 ID: {exchange.get('exchange_id')}")
                    print(f"       사유: {exchange.get('reason_code_text', 'N/A')}")
                    print(f"       금액: {exchange.get('exchange_amount', 0):,}원")
            else:
                print(f"   🎉 업체 과실 교환요청이 없습니다!")
        else:
            print(f"❌ 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_exchange_analysis_report():
    """교환요청 분석 보고서 예제"""
    print_section("교환요청 분석 보고서 생성")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        
        print(f"📊 교환요청 분석 보고서 생성 중 (최근 7일)...")
        
        result = client.create_exchange_analysis_report(vendor_id, days=7)
        
        if result.get("success"):
            print(f"✅ 분석 완료!")
            
            report = result.get("analysis_report", {})
            print(f"   📋 {report.get('summary', 'N/A')}")
            print(f"   🟢 전반적 상태: {report.get('overall_status', 'N/A')}")
            
            # 핵심 지표
            metrics = report.get("key_metrics", {})
            if metrics:
                print(f"\n   📈 핵심 지표:")
                print(f"      총 교환요청: {metrics.get('total_exchanges', 0)}건")
                print(f"      업체 과실률: {metrics.get('vendor_fault_rate', 0):.1f}%")
                print(f"      완료율: {metrics.get('completion_rate', 0):.1f}%")
                print(f"      위험 점수: {metrics.get('risk_score', 0)}점")
            
            # 주요 이슈
            top_issues = report.get("top_issues", [])
            if top_issues:
                print(f"\n   🔥 주요 이슈:")
                for i, issue in enumerate(top_issues, 1):
                    print(f"      [{i}] {issue.get('issue', 'N/A')} ({issue.get('count', 0)}건, {issue.get('percentage', 0):.1f}%)")
            
            # 권장사항
            recommendations = report.get("recommendations", [])
            if recommendations:
                print(f"\n   💡 권장사항:")
                for i, rec in enumerate(recommendations[:3], 1):  # 최대 3개
                    print(f"      {i}. {rec}")
                    
            # 위험 알림
            risk_alerts = report.get("risk_alerts", [])
            if risk_alerts:
                print(f"\n   ⚠️  위험 알림:")
                for alert in risk_alerts:
                    print(f"      • {alert}")
        else:
            print(f"❌ 분석 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_pagination_exchanges():
    """페이징을 통한 전체 교환요청 조회 예제"""
    print_section("페이징 교환요청 조회")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        
        # 검색 파라미터 설정 (최근 7일, 페이지당 5건)
        from_date, to_date = generate_exchange_date_range_for_recent_days(7)
        
        search_params = ExchangeRequestSearchParams(
            vendor_id=vendor_id,
            created_at_from=from_date,
            created_at_to=to_date,
            max_per_page=5  # 페이지당 5건씩
        )
        
        print(f"📑 페이징을 통한 전체 교환요청 조회 중...")
        print(f"   페이지당 건수: 5건")
        
        result = client.get_exchange_requests_with_pagination(search_params, max_pages=3)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   총 건수: {result.get('total_count', 0)}건")
            print(f"   조회된 페이지: {result.get('page_count', 0)}개")
        else:
            print(f"❌ 조회 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_exchange_processing_apis():
    """교환요청 처리 API 예제"""
    print_section("교환요청 처리 API")
    
    try:
        client = ExchangeClient()
        vendor_id = client.vendor_id
        exchange_id = 101268974  # 예시 교환 ID
        
        print(f"🔧 교환요청 처리 API 테스트 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   교환 ID: {exchange_id}")
        
        # 1. 입고 확인 처리 예제
        print(f"\n   📦 1. 입고 확인 처리 테스트...")
        try:
            result = client.confirm_exchange_receive(exchange_id, vendor_id)
            if result.get("success"):
                print(f"      ✅ 입고 확인 처리 성공!")
                print(f"         결과 코드: {result.get('result_code', 'N/A')}")
                print(f"         결과 메시지: {result.get('result_message', 'N/A')}")
            else:
                print(f"      ❌ 입고 확인 처리 실패: {result.get('error', '알 수 없는 오류')}")
        except Exception as e:
            print(f"      💥 입고 확인 처리 예외: {str(e)}")
        
        # 2. 교환 거부 처리 예제
        print(f"\n   🚫 2. 교환 거부 처리 테스트...")
        try:
            reject_code = "SOLDOUT"  # 매진으로 인한 거부
            result = client.reject_exchange_request(exchange_id, vendor_id, reject_code)
            if result.get("success"):
                print(f"      ✅ 교환 거부 처리 성공!")
                print(f"         거부 코드: {result.get('reject_code', 'N/A')}")
                print(f"         거부 사유: {result.get('reject_message', 'N/A')}")
                print(f"         결과 코드: {result.get('result_code', 'N/A')}")
            else:
                print(f"      ❌ 교환 거부 처리 실패: {result.get('error', '알 수 없는 오류')}")
        except Exception as e:
            print(f"      💥 교환 거부 처리 예외: {str(e)}")
        
        # 3. 송장 업로드 처리 예제
        print(f"\n   📋 3. 송장 업로드 처리 테스트...")
        try:
            delivery_code = "CJGLS"  # CJ대한통운
            invoice_number = "1234567890123"  # 예시 운송장번호
            shipment_box_id = 12345  # 예시 배송번호
            
            result = client.upload_exchange_invoice(
                exchange_id, vendor_id, delivery_code, invoice_number, shipment_box_id
            )
            if result.get("success"):
                print(f"      ✅ 송장 업로드 성공!")
                print(f"         택배사: {result.get('delivery_code', 'N/A')}")
                print(f"         운송장번호: {result.get('invoice_number', 'N/A')}")
                print(f"         배송번호: {result.get('shipment_box_id', 'N/A')}")
                print(f"         결과 코드: {result.get('result_code', 'N/A')}")
            else:
                print(f"      ❌ 송장 업로드 실패: {result.get('error', '알 수 없는 오류')}")
        except Exception as e:
            print(f"      💥 송장 업로드 예외: {str(e)}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def main():
    """메인 실행 함수"""
    print("🛒 쿠팡 파트너스 교환요청 관리 API 사용 예제")
    print("=" * 60)
    
    # .env 기반 환경설정 검증
    env_status = validate_environment_setup()
    
    if not env_status["is_valid"]:
        print("⚠️  환경설정 오류")
        print(f"   {env_status['message']}")
        print("   .env 파일에 다음 형식으로 설정해주세요:")
        print("   COUPANG_ACCESS_KEY=your_access_key")
        print("   COUPANG_SECRET_KEY=your_secret_key")
        print("   COUPANG_VENDOR_ID=A01409684")
        return
    
    print(f"✅ 환경설정 확인 완료 (Vendor ID: {env_status['vendor_id']})")
    print("=" * 60)
    
    try:
        # 1. 기본 교환요청 조회
        example_basic_exchange_requests()
        
        # 2. 상태별 교환요청 조회  
        example_status_filtered_exchanges()
        
        # 3. 오늘의 교환요청 조회
        example_today_exchanges()
        
        # 4. 업체 과실 교환요청 조회
        example_vendor_fault_exchanges()
        
        # 5. 교환요청 분석 보고서
        example_exchange_analysis_report()
        
        # 6. 페이징 조회
        example_pagination_exchanges()
        
        # 7. 교환요청 처리 API
        example_exchange_processing_apis()
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n💥 예상치 못한 오류 발생: {str(e)}")
    
    print(f"\n🎯 교환요청 관리 API 예제 실행 완료!")


if __name__ == "__main__":
    main()