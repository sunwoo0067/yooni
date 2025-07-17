#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 고객문의(CS) 관리 사용 예제
"""

import sys
import os
from datetime import datetime, timedelta

# 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cs.cs_client import CSClient
from cs.call_center_client import CallCenterClient
from cs.models import InquirySearchParams, CallCenterInquirySearchParams
from cs.utils import (
    generate_inquiry_date_range_for_recent_days, validate_environment_setup,
    create_sample_inquiry_search_params, generate_inquiry_date_range_for_today
)


def print_section(title: str):
    """섹션 제목 출력"""
    print(f"\n{'='*60}")
    print(f"🔸 {title}")
    print('='*60)


def example_basic_customer_inquiries():
    """기본 고객문의 목록 조회 예제"""
    print_section("기본 고객문의 목록 조회")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id  # .env에서 자동으로 로드된 벤더 ID 사용
        
        # 검색 파라미터 설정 (최근 1일)
        from_date, to_date = generate_inquiry_date_range_for_recent_days(1)
        
        search_params = InquirySearchParams(
            vendor_id=vendor_id,
            answered_type="ALL",
            inquiry_start_at=from_date,
            inquiry_end_at=to_date,
            page_size=10
        )
        
        print(f"🔍 고객문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   기간: {from_date} ~ {to_date}")
        print(f"   답변 상태: 전체")
        
        result = client.get_customer_inquiries(search_params)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   총 건수: {result.get('total_count', 0)}건")
            
            if result.get("summary_stats"):
                stats = result["summary_stats"]
                print(f"   답변 완료: {stats.get('answered_count', 0)}건")
                print(f"   미답변: {stats.get('unanswered_count', 0)}건")
                print(f"   답변률: {stats.get('answer_rate', 0):.1f}%")
                
                if result.get("pagination_info"):
                    pagination = result["pagination_info"]
                    print(f"   페이지: {pagination.get('current_page')}/{pagination.get('total_pages')}")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_today_inquiries():
    """오늘의 고객문의 조회 예제"""
    print_section("오늘의 고객문의 조회")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id
        
        print(f"🔍 오늘의 고객문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   답변 상태: 전체")
        
        result = client.get_today_inquiries(vendor_id, "ALL")
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   오늘의 문의: {result.get('total_count', 0)}건")
            
            # 개별 문의 정보 출력 (최대 3건)
            inquiries = result.get("data", [])
            for i, inquiry in enumerate(inquiries[:3], 1):
                print(f"   [{i}] 문의 ID: {inquiry.get('inquiry_id')}")
                print(f"       상품 ID: {inquiry.get('product_id')}")
                print(f"       문의 시간: {inquiry.get('inquiry_at')}")
                print(f"       답변 상태: {'완료' if inquiry.get('is_answered') else '미답변'}")
                content_preview = inquiry.get('content', '')[:30]
                print(f"       내용: {content_preview}{'...' if len(content_preview) >= 30 else ''}")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_unanswered_inquiries():
    """미답변 고객문의 조회 예제"""
    print_section("미답변 고객문의 조회")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id
        
        print(f"🔍 미답변 고객문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   조회 기간: 최근 7일")
        
        result = client.get_unanswered_inquiries(vendor_id, days=7, page_size=20)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   미답변 문의: {result.get('total_count', 0)}건")
            
            # 미답변 문의 상세 정보
            inquiries = result.get("data", [])
            if inquiries:
                print(f"\n📋 미답변 문의 목록:")
                for i, inquiry in enumerate(inquiries[:5], 1):  # 최대 5건 출력
                    print(f"   [{i}] 문의 ID: {inquiry.get('inquiry_id')}")
                    print(f"       상품 ID: {inquiry.get('product_id')}")
                    print(f"       문의일: {inquiry.get('inquiry_at')}")
                    
                    # 문의 경과 시간 계산
                    inquiry_time = inquiry.get('inquiry_at', '')
                    if inquiry_time:
                        try:
                            inquiry_dt = datetime.strptime(inquiry_time, '%Y-%m-%d %H:%M:%S')
                            elapsed = datetime.now() - inquiry_dt
                            elapsed_hours = elapsed.total_seconds() / 3600
                            print(f"       경과 시간: {elapsed_hours:.1f}시간")
                        except:
                            pass
                    
                    # 주문 관련 여부
                    has_order = len(inquiry.get('order_ids', [])) > 0
                    print(f"       주문 관련: {'예' if has_order else '아니오'}")
                    print()
            else:
                print("🎉 미답변 문의가 없습니다!")
                
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_answered_type_filter():
    """답변 상태별 고객문의 조회 예제"""
    print_section("답변 상태별 고객문의 조회")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id
        
        # 답변 완료된 문의만 조회
        from_date, to_date = generate_inquiry_date_range_for_recent_days(3)
        
        search_params = InquirySearchParams(
            vendor_id=vendor_id,
            answered_type="ANSWERED",  # 답변 완료만
            inquiry_start_at=from_date,
            inquiry_end_at=to_date,
            page_size=15
        )
        
        print(f"🔍 답변 완료된 고객문의 조회 중...")
        print(f"   기간: {from_date} ~ {to_date}")
        print(f"   답변 상태: 답변완료")
        
        result = client.get_customer_inquiries(search_params)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   답변 완료 문의: {result.get('total_count', 0)}건")
            
            # 답변 완료된 문의의 응답 시간 분석
            inquiries = result.get("data", [])
            if inquiries:
                total_response_time = 0
                response_count = 0
                
                for inquiry in inquiries:
                    inquiry_at = inquiry.get('inquiry_at', '')
                    latest_answer_at = inquiry.get('latest_answer_at', '')
                    
                    if inquiry_at and latest_answer_at:
                        try:
                            inquiry_dt = datetime.strptime(inquiry_at, '%Y-%m-%d %H:%M:%S')
                            answer_dt = datetime.strptime(latest_answer_at, '%Y-%m-%d %H:%M:%S')
                            response_time = (answer_dt - inquiry_dt).total_seconds() / 3600
                            
                            if response_time >= 0:
                                total_response_time += response_time
                                response_count += 1
                        except:
                            continue
                
                if response_count > 0:
                    avg_response_time = total_response_time / response_count
                    print(f"   평균 응답 시간: {avg_response_time:.1f}시간")
                    
                    if avg_response_time <= 24:
                        print("   🟢 응답 속도 우수 (24시간 이내)")
                    elif avg_response_time <= 72:
                        print("   🟡 응답 속도 보통 (72시간 이내)")
                    else:
                        print("   🔴 응답 속도 개선 필요 (72시간 초과)")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_inquiry_analysis_report():
    """고객문의 분석 보고서 생성 예제"""
    print_section("고객문의 분석 보고서 생성")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id
        
        print(f"📊 고객문의 분석 보고서 생성 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   분석 기간: 최근 7일")
        
        result = client.create_inquiry_analysis_report(vendor_id, days=7)
        
        if result.get("success"):
            print(f"✅ 분석 보고서 생성 성공!")
            print(f"   분석 기간: {result.get('analysis_period', '7일')}")
            print(f"   총 문의 수: {result.get('total_inquiries', 0)}건")
            
            if result.get("analysis_report"):
                report = result["analysis_report"]
                
                print(f"\n📈 분석 결과:")
                print(f"   종합 평가: {report.get('overall_status', 'N/A')}")
                print(f"   요약: {report.get('summary', 'N/A')}")
                
                # 핵심 지표
                if report.get("key_metrics"):
                    metrics = report["key_metrics"]
                    print(f"\n📊 핵심 지표:")
                    print(f"   전체 문의: {metrics.get('total_inquiries', 0)}건")
                    print(f"   답변 완료: {metrics.get('answered_count', 0)}건")
                    print(f"   미답변: {metrics.get('unanswered_count', 0)}건")
                    print(f"   답변률: {metrics.get('answer_rate', 0):.1f}%")
                    print(f"   주문 관련 문의: {metrics.get('order_related_rate', 0):.1f}%")
                    print(f"   평균 응답 시간: {metrics.get('average_response_hours', 0):.1f}시간")
                
                # 응답 성과
                if report.get("response_performance"):
                    performance = report["response_performance"]
                    print(f"\n⏱️ 응답 성과:")
                    print(f"   총 답변 수: {performance.get('total_answered', 0)}건")
                    print(f"   평균 응답 시간: {performance.get('average_response_hours', 0):.1f}시간")
                    print(f"   중간값 응답 시간: {performance.get('median_response_hours', 0):.1f}시간")
                    print(f"   빠른 응답(24h 이내): {performance.get('fast_response_count', 0)}건")
                    print(f"   늦은 응답(72h 초과): {performance.get('slow_response_count', 0)}건")
                    print(f"   빠른 응답 비율: {performance.get('fast_response_rate', 0):.1f}%")
                
                # 권장사항
                if report.get("recommendations"):
                    print(f"\n💡 권장사항:")
                    for i, recommendation in enumerate(report["recommendations"], 1):
                        print(f"   {i}. {recommendation}")
        else:
            print(f"❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_environment_validation():
    """환경설정 검증 예제"""
    print_section("환경설정 검증")
    
    try:
        print("🔧 환경설정 검증 중...")
        
        validation_result = validate_environment_setup()
        
        if validation_result.get("is_valid"):
            print("✅ 환경설정이 올바르게 구성되었습니다!")
            print(f"   벤더 ID: {validation_result.get('vendor_id')}")
            print(f"   메시지: {validation_result.get('message')}")
        else:
            print("❌ 환경설정에 문제가 있습니다!")
            print(f"   메시지: {validation_result.get('message')}")
            
            missing_configs = validation_result.get("missing_configs", [])
            if missing_configs:
                print("   누락된 환경변수:")
                for config in missing_configs:
                    print(f"     - {config}")
                    
                print("\n💡 해결 방법:")
                print("   1. 프로젝트 루트에 .env 파일을 생성하세요")
                print("   2. 다음과 같이 환경변수를 설정하세요:")
                print("      COUPANG_ACCESS_KEY=your_access_key")
                print("      COUPANG_SECRET_KEY=your_secret_key") 
                print("      COUPANG_VENDOR_ID=A01234567")
                
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_sample_params_generation():
    """샘플 파라미터 생성 예제"""
    print_section("샘플 검색 파라미터 생성")
    
    try:
        print("🛠️ 샘플 검색 파라미터 생성 중...")
        
        # 기본 샘플 파라미터 (최근 1일)
        sample_params_1day = create_sample_inquiry_search_params(days=1, answered_type="ALL")
        print(f"📋 1일 전체 문의 조회:")
        print(f"   벤더 ID: {sample_params_1day.get('vendor_id')}")
        print(f"   답변 상태: {sample_params_1day.get('answered_type')}")
        print(f"   시작일: {sample_params_1day.get('inquiry_start_at')}")
        print(f"   종료일: {sample_params_1day.get('inquiry_end_at')}")
        print(f"   페이지 크기: {sample_params_1day.get('page_size')}")
        
        # 미답변 문의 샘플 파라미터 (최근 3일)
        sample_params_unanswered = create_sample_inquiry_search_params(days=3, answered_type="NOANSWER")
        print(f"\n📋 3일 미답변 문의 조회:")
        print(f"   벤더 ID: {sample_params_unanswered.get('vendor_id')}")
        print(f"   답변 상태: {sample_params_unanswered.get('answered_type')}")
        print(f"   시작일: {sample_params_unanswered.get('inquiry_start_at')}")
        print(f"   종료일: {sample_params_unanswered.get('inquiry_end_at')}")
        print(f"   페이지 크기: {sample_params_unanswered.get('page_size')}")
        
        # 답변 완료 문의 샘플 파라미터 (최근 7일)
        sample_params_answered = create_sample_inquiry_search_params(days=7, answered_type="ANSWERED")
        print(f"\n📋 7일 답변완료 문의 조회:")
        print(f"   벤더 ID: {sample_params_answered.get('vendor_id')}")
        print(f"   답변 상태: {sample_params_answered.get('answered_type')}")
        print(f"   시작일: {sample_params_answered.get('inquiry_start_at')}")
        print(f"   종료일: {sample_params_answered.get('inquiry_end_at')}")
        print(f"   페이지 크기: {sample_params_answered.get('page_size')}")
        
        print(f"\n💡 이 파라미터들은 InquirySearchParams 객체로 변환하여 사용할 수 있습니다.")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_reply_to_inquiry():
    """고객문의 답변 예제"""
    print_section("고객문의 답변")
    
    try:
        client = CSClient()
        vendor_id = client.vendor_id
        
        # 예제 데이터 (실제 사용 시에는 먼저 문의 목록을 조회하여 inquiry_id를 확인해야 함)
        inquiry_id = 12345  # 실제 문의 ID로 변경 필요
        content = "안녕하세요\\n문의해주신 상품은 현재 재고가 충분합니다.\\n배송은 주문 후 1-2일 소요됩니다."
        reply_by = "manager01"  # 실제 WING ID로 변경 필요
        
        print(f"💬 고객문의 답변 중...")
        print(f"   문의 ID: {inquiry_id}")
        print(f"   응답자: {reply_by}")
        print(f"   답변 내용 길이: {len(content)}자")
        
        # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
        print("⚠️ 주의: 실제 API 호출을 수행합니다. 실제 문의 ID와 WING ID가 필요합니다.")
        print("💡 테스트를 위해서는 먼저 문의 목록 조회로 실제 inquiry_id를 확인하세요.")
        
        # 실제 API 호출 (주석 처리)
        # result = client.reply_to_inquiry(inquiry_id, vendor_id, content, reply_by)
        
        # 시뮬레이션 결과 표시
        print("🔧 시뮬레이션 모드:")
        print("✅ 답변 처리 성공 (시뮬레이션)")
        print(f"   문의 ID: {inquiry_id}")
        print(f"   처리 완료: 답변이 등록되었습니다")
        print(f"   답변 길이: {len(content)}자")
        
        # 실제 사용법 안내
        print(f"\n📝 실제 사용법:")
        print(f"   1. 먼저 get_unanswered_inquiries()로 미답변 문의 조회")
        print(f"   2. 답변할 문의의 inquiry_id 확인")
        print(f"   3. reply_to_inquiry(inquiry_id, vendor_id, content, reply_by) 호출")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_bulk_reply():
    """여러 고객문의 일괄 답변 예제"""
    print_section("여러 고객문의 일괄 답변")
    
    try:
        client = CSClient()
        
        # 예제 일괄 답변 요청 (실제 사용 시에는 실제 inquiry_id들로 변경 필요)
        reply_requests = [
            {
                "inquiry_id": 12345,
                "content": "안녕하세요\\n문의해주신 상품은 재고가 충분합니다.\\n감사합니다.",
                "reply_by": "manager01"
            },
            {
                "inquiry_id": 12346,
                "content": "안녕하세요\\n배송 관련 문의에 답변드립니다.\\n주문 후 1-2일 소요됩니다.",
                "reply_by": "manager01"
            },
            {
                "inquiry_id": 12347,
                "content": "안녕하세요\\n해당 상품은 현재 품절입니다.\\n입고 시 알려드리겠습니다.",
                "reply_by": "manager02"
            }
        ]
        
        print(f"📝 일괄 답변 처리 중...")
        print(f"   총 답변 수: {len(reply_requests)}건")
        
        # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
        print("⚠️ 주의: 실제 API 호출을 수행합니다. 실제 문의 ID들과 WING ID가 필요합니다.")
        
        # 실제 API 호출 (주석 처리)
        # result = client.bulk_reply_to_inquiries(reply_requests)
        
        # 시뮬레이션 결과 표시
        print("🔧 시뮬레이션 모드:")
        print("✅ 일괄 답변 처리 완료 (시뮬레이션)")
        print(f"   총 요청: {len(reply_requests)}건")
        print(f"   성공: {len(reply_requests)}건 (100.0%)")
        print(f"   실패: 0건")
        
        # 개별 결과 시뮬레이션
        print(f"\n📋 개별 답변 결과:")
        for i, request in enumerate(reply_requests):
            print(f"   [{i+1}] 문의 ID: {request['inquiry_id']} ✅ 성공")
            print(f"       응답자: {request['reply_by']}")
            print(f"       답변 길이: {len(request['content'])}자")
        
        # 실제 사용법 안내
        print(f"\n📝 실제 사용법:")
        print(f"   1. 미답변 문의 목록 조회")
        print(f"   2. 각 문의에 대한 답변 내용 준비")
        print(f"   3. reply_requests 리스트 구성")
        print(f"   4. bulk_reply_to_inquiries(reply_requests) 호출")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_reply_with_validation():
    """답변 내용 검증을 포함한 답변 예제"""
    print_section("답변 내용 검증을 포함한 답변")
    
    try:
        from cs.validators import is_valid_reply_content, is_valid_reply_by
        
        print("🔍 답변 내용 및 WING ID 검증 예제...")
        
        # 테스트할 답변 내용들
        test_contents = [
            "안녕하세요\\n문의해주신 내용에 답변드립니다.",  # 유효
            "",  # 무효 (빈 내용)
            "   ",  # 무효 (공백만)
            "안녕하세요\\n줄바꿈\\n테스트\\n입니다.",  # 유효
            "a" * 1001,  # 무효 (너무 긺)
        ]
        
        # 테스트할 WING ID들
        test_wing_ids = [
            "manager01",  # 유효
            "user_123",   # 유효
            "",           # 무효 (빈 값)
            "invalid@id", # 무효 (특수문자)
            "valid123",   # 유효
            "a" * 51,     # 무효 (너무 긺)
        ]
        
        print("📝 답변 내용 검증 결과:")
        for i, content in enumerate(test_contents):
            is_valid = is_valid_reply_content(content)
            preview = content[:20] + "..." if len(content) > 20 else content
            preview = preview.replace('\n', '\\n')
            print(f"   [{i+1}] {'✅' if is_valid else '❌'} \"{preview}\"")
        
        print("\n🔑 WING ID 검증 결과:")
        for i, wing_id in enumerate(test_wing_ids):
            is_valid = is_valid_reply_by(wing_id)
            print(f"   [{i+1}] {'✅' if is_valid else '❌'} \"{wing_id}\"")
        
        # 올바른 답변 예제
        print("\n💡 올바른 답변 예제:")
        valid_examples = [
            {
                "inquiry_id": 12345,
                "content": "안녕하세요\\n문의해주신 상품 정보를 안내드립니다.\\n추가 문의 사항이 있으시면 언제든 연락주세요.",
                "reply_by": "manager01",
                "description": "일반적인 답변"
            },
            {
                "inquiry_id": 12346,
                "content": "배송 지연에 대해 사과드립니다.\\n현재 상황을 확인하여 빠른 시일 내에 배송해드리겠습니다.",
                "reply_by": "support_team",
                "description": "배송 관련 답변"
            },
            {
                "inquiry_id": 12347,
                "content": "교환/환불 절차 안내드립니다.\\n1. 마이페이지 > 주문내역\\n2. 교환/환불 신청\\n3. 택배 발송",
                "reply_by": "cs_manager",
                "description": "절차 안내 답변"
            }
        ]
        
        for i, example in enumerate(valid_examples, 1):
            print(f"   [{i}] {example['description']}")
            print(f"       문의 ID: {example['inquiry_id']}")
            print(f"       응답자: {example['reply_by']}")
            content_preview = example['content'].replace('\\n', ' / ')[:50]
            print(f"       내용: {content_preview}...")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


# 고객센터 문의 관리 예제들
def example_call_center_inquiries():
    """고객센터 문의 목록 조회 예제"""
    print_section("고객센터 문의 목록 조회")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        # 최근 1일간 전체 고객센터 문의 조회
        print(f"🔍 고객센터 문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   기간: 최근 1일")
        print(f"   상담 상태: 전체")
        
        result = client.get_call_center_inquiries_by_date(
            vendor_id=vendor_id,
            days=1,
            counseling_status="NONE",
            page_size=10
        )
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            print(f"   총 건수: {result.get('total_count', 0)}건")
            
            if result.get("summary_stats"):
                stats = result["summary_stats"]
                print(f"   답변 완료: {stats.get('answered_count', 0)}건")
                print(f"   답변 대기: {stats.get('pending_count', 0)}건")
                print(f"   확인 대기: {stats.get('transfer_count', 0)}건")
                print(f"   답변률: {stats.get('answer_rate', 0):.1f}%")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_pending_call_center_inquiries():
    """답변 대기 중인 고객센터 문의 조회 예제"""
    print_section("답변 대기 중인 고객센터 문의 조회")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        print(f"🔍 답변 대기 중인 고객센터 문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   기간: 최근 7일")
        
        result = client.get_pending_call_center_inquiries(vendor_id, days=7)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            total_count = result.get('total_count', 0)
            print(f"   답변 대기 중인 문의: {total_count}건")
            
            # 개별 문의 정보 출력 (최대 3건)
            inquiries = result.get("data", [])
            for i, inquiry in enumerate(inquiries[:3], 1):
                print(f"   [{i}] 문의 ID: {inquiry.get('inquiry_id')}")
                print(f"       상품명: {inquiry.get('item_name', 'N/A')[:30]}")
                print(f"       문의 상태: {inquiry.get('inquiry_status')}")
                print(f"       상담 상태: {inquiry.get('cs_partner_counseling_status')}")
                content_preview = inquiry.get('content', '')[:40]
                print(f"       내용: {content_preview}{'...' if len(content_preview) >= 40 else ''}")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_transfer_call_center_inquiries():
    """확인 대기 중인 고객센터 문의 조회 예제 (TRANSFER 상태)"""
    print_section("확인 대기 중인 고객센터 문의 조회")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        print(f"🔍 확인 대기 중인 고객센터 문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   기간: 최근 7일")
        print(f"   상태: TRANSFER (확인 대기)")
        
        result = client.get_transfer_call_center_inquiries(vendor_id, days=7)
        
        if result.get("success"):
            print(f"✅ 조회 성공!")
            total_count = result.get('total_count', 0)
            print(f"   확인 대기 중인 문의: {total_count}건")
            
            if total_count > 0:
                print(f"   📋 확인 처리가 필요한 문의들이 있습니다.")
                print(f"   💡 각 문의에 대해 confirm_call_center_inquiry() 를 호출하여 확인 처리하세요.")
        else:
            print(f"❌ 조회 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_call_center_inquiry_detail():
    """고객센터 문의 상세 조회 예제"""
    print_section("고객센터 문의 상세 조회")
    
    try:
        client = CallCenterClient()
        
        # 예제 문의 ID (실제 사용 시에는 실제 inquiry_id로 변경 필요)
        inquiry_id = 12345
        
        print(f"🔍 고객센터 문의 상세 조회 중...")
        print(f"   문의 ID: {inquiry_id}")
        
        # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
        print("⚠️ 주의: 실제 API 호출을 수행합니다. 실제 문의 ID가 필요합니다.")
        
        # 실제 API 호출 (주석 처리)
        # result = client.get_call_center_inquiry_detail(inquiry_id)
        
        # 시뮬레이션 결과 표시
        print("🔧 시뮬레이션 모드:")
        print("✅ 문의 상세 조회 완료 (시뮬레이션)")
        print(f"   문의 ID: {inquiry_id}")
        print(f"   상품명: 예제 상품명")
        print(f"   문의 상태: progress")
        print(f"   상담 상태: requestAnswer")
        print(f"   답변 수: 2개")
        print(f"   답변 대기 여부: 있음")
        
        print(f"\n📝 실제 사용법:")
        print(f"   1. 실제 inquiry_id 준비")
        print(f"   2. get_call_center_inquiry_detail(inquiry_id) 호출")
        print(f"   3. 반환된 상세 정보 확인")
        print(f"   4. 필요시 답변 또는 확인 처리")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_reply_to_call_center_inquiry():
    """고객센터 문의 답변 예제"""
    print_section("고객센터 문의 답변")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        # 예제 답변 데이터 (실제 사용 시에는 실제 값들로 변경 필요)
        inquiry_id = 12345
        content = "안녕하세요\\n\\n문의해주신 내용에 답변드립니다.\\n\\n추가 문의 사항이 있으시면 언제든 연락주세요.\\n\\n감사합니다."
        reply_by = "manager01"
        parent_answer_id = 67890
        
        print(f"📝 고객센터 문의 답변 중...")
        print(f"   문의 ID: {inquiry_id}")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   응답자: {reply_by}")
        print(f"   부모 답변 ID: {parent_answer_id}")
        print(f"   답변 길이: {len(content)}자")
        
        # 답변 내용 검증
        from cs.validators import is_valid_cc_reply_content, is_valid_reply_by
        
        content_valid = is_valid_cc_reply_content(content)
        reply_by_valid = is_valid_reply_by(reply_by)
        
        print(f"   답변 내용 검증: {'✅' if content_valid else '❌'}")
        print(f"   응답자 ID 검증: {'✅' if reply_by_valid else '❌'}")
        
        if content_valid and reply_by_valid:
            # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
            print("⚠️ 주의: 실제 API 호출을 수행합니다. 실제 문의 ID와 parent_answer_id가 필요합니다.")
            
            # 실제 API 호출 (주석 처리)
            # result = client.reply_to_call_center_inquiry(
            #     inquiry_id, vendor_id, content, reply_by, parent_answer_id
            # )
            
            # 시뮬레이션 결과 표시
            print("🔧 시뮬레이션 모드:")
            print("✅ 고객센터 문의 답변 완료 (시뮬레이션)")
            print(f"   처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ 검증 실패: 답변 내용 또는 응답자 ID가 올바르지 않습니다.")
        
        print(f"\n📝 실제 사용법:")
        print(f"   1. 답변 대기 중인 문의 조회")
        print(f"   2. 문의 상세 정보에서 parent_answer_id 확인")
        print(f"   3. 답변 내용 작성 (2~1000자)")
        print(f"   4. reply_to_call_center_inquiry() 호출")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_confirm_call_center_inquiry():
    """고객센터 문의 확인 처리 예제"""
    print_section("고객센터 문의 확인 처리")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        # 예제 확인 데이터 (실제 사용 시에는 실제 값들로 변경 필요)
        inquiry_id = 12345
        confirm_by = "manager01"
        
        print(f"✅ 고객센터 문의 확인 처리 중...")
        print(f"   문의 ID: {inquiry_id}")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   확인자: {confirm_by}")
        
        # 확인자 ID 검증
        from cs.validators import is_valid_confirm_by
        
        confirm_by_valid = is_valid_confirm_by(confirm_by)
        print(f"   확인자 ID 검증: {'✅' if confirm_by_valid else '❌'}")
        
        if confirm_by_valid:
            # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
            print("⚠️ 주의: 실제 API 호출을 수행합니다. TRANSFER 상태의 실제 문의 ID가 필요합니다.")
            
            # 실제 API 호출 (주석 처리)
            # result = client.confirm_call_center_inquiry(inquiry_id, vendor_id, confirm_by)
            
            # 시뮬레이션 결과 표시
            print("🔧 시뮬레이션 모드:")
            print("✅ 고객센터 문의 확인 완료 (시뮬레이션)")
            print(f"   처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   상태 변경: TRANSFER → 확인완료")
        else:
            print("❌ 검증 실패: 확인자 ID가 올바르지 않습니다.")
        
        print(f"\n📝 실제 사용법:")
        print(f"   1. TRANSFER 상태의 문의 조회")
        print(f"   2. 확인이 필요한 문의 식별")
        print(f"   3. confirm_call_center_inquiry() 호출")
        print(f"   4. 문의 상태가 확인완료로 변경됨")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_call_center_inquiries_by_item():
    """특정 상품의 고객센터 문의 조회 예제"""
    print_section("특정 상품의 고객센터 문의 조회")
    
    try:
        client = CallCenterClient()
        vendor_id = client.vendor_id
        
        # 예제 옵션 ID (실제 사용 시에는 실제 vendor_item_id로 변경 필요)
        vendor_item_id = "1234567890"
        
        print(f"🔍 특정 상품의 고객센터 문의 조회 중...")
        print(f"   벤더 ID: {vendor_id}")
        print(f"   옵션 ID: {vendor_item_id}")
        print(f"   상담 상태: 전체")
        
        # 주의: 이 예제는 실제 API 호출을 수행하므로 테스트 시 주의 필요
        print("⚠️ 주의: 실제 API 호출을 수행합니다. 실제 vendor_item_id가 필요합니다.")
        
        # 실제 API 호출 (주석 처리)
        # result = client.get_call_center_inquiries_by_item(
        #     vendor_id, vendor_item_id, counseling_status="NONE"
        # )
        
        # 시뮬레이션 결과 표시
        print("🔧 시뮬레이션 모드:")
        print("✅ 상품별 고객센터 문의 조회 완료 (시뮬레이션)")
        print(f"   해당 상품 문의: 5건")
        print(f"   답변 완료: 3건")
        print(f"   답변 대기: 2건")
        print(f"   확인 대기: 0건")
        
        print(f"\n📝 실제 사용법:")
        print(f"   1. 조회할 상품의 vendor_item_id 준비")
        print(f"   2. get_call_center_inquiries_by_item() 호출")
        print(f"   3. 해당 상품 관련 문의들 확인")
        print(f"   4. 필요시 답변 또는 확인 처리")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def example_call_center_validation():
    """고객센터 문의 관련 검증 함수들 예제"""
    print_section("고객센터 문의 검증 함수들")
    
    try:
        from cs.validators import (
            is_valid_partner_counseling_status, is_valid_cc_reply_content, 
            is_valid_confirm_by
        )
        
        print("🔍 고객센터 문의 관련 검증 예제...")
        
        # 상담 상태 검증 테스트
        counseling_statuses = ["NONE", "ANSWER", "NO_ANSWER", "TRANSFER", "INVALID"]
        print("\n📊 상담 상태 검증 결과:")
        for status in counseling_statuses:
            is_valid = is_valid_partner_counseling_status(status)
            print(f"   {'✅' if is_valid else '❌'} {status}")
        
        # 답변 내용 검증 테스트 (고객센터용 - 2~1000자)
        reply_contents = [
            "안녕하세요",  # 유효 (5자)
            "안",  # 유효 (2자)
            "감사합니다. 문의해주신 내용에 답변드립니다.",  # 유효
            "",  # 무효 (빈 값)
            "a",  # 무효 (1자)
            "a" * 1001,  # 무효 (1001자)
        ]
        
        print("\n💬 답변 내용 검증 결과 (2~1000자):")
        for i, content in enumerate(reply_contents):
            is_valid = is_valid_cc_reply_content(content)
            preview = content[:20] + "..." if len(content) > 20 else content
            print(f"   [{i+1}] {'✅' if is_valid else '❌'} \"{preview}\" ({len(content)}자)")
        
        # 확인자 ID 검증 테스트
        confirm_ids = [
            "manager01",      # 유효
            "user_123",       # 유효
            "cs-team",        # 유효 (하이픈 허용)
            "",               # 무효 (빈 값)
            "invalid@id",     # 무효 (@ 기호)
            "valid123",       # 유효
            "a" * 51,         # 무효 (51자)
        ]
        
        print("\n🔑 확인자 ID 검증 결과:")
        for confirm_id in confirm_ids:
            is_valid = is_valid_confirm_by(confirm_id)
            print(f"   {'✅' if is_valid else '❌'} \"{confirm_id}\"")
        
        print("\n📝 검증 규칙 요약:")
        print("   상담 상태: NONE, ANSWER, NO_ANSWER, TRANSFER")
        print("   답변 내용: 2자 이상 1000자 이하")
        print("   확인자 ID: 영문자, 숫자, 언더스코어, 하이픈만 허용 (최대 50자)")
        
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")


def main():
    """메인 실행 함수"""
    print("🔸 쿠팡 파트너스 고객문의(CS) 관리 API 사용 예제")
    print("=" * 60)
    
    try:
        # 환경설정 먼저 검증
        example_environment_validation()
        
        # 기본 예제들 실행
        example_basic_customer_inquiries()
        example_today_inquiries()
        example_unanswered_inquiries()
        example_answered_type_filter()
        example_inquiry_analysis_report()
        example_sample_params_generation()
        
        # 답변 관련 예제들
        example_reply_to_inquiry()
        example_bulk_reply()
        example_reply_with_validation()
        
        # 고객센터 문의 관련 예제들
        example_call_center_inquiries()
        example_pending_call_center_inquiries()
        example_transfer_call_center_inquiries()
        example_call_center_inquiry_detail()
        example_reply_to_call_center_inquiry()
        example_confirm_call_center_inquiry()
        example_call_center_inquiries_by_item()
        example_call_center_validation()
        
        print_section("실행 완료")
        print("✅ 모든 예제가 실행되었습니다!")
        print("📚 자세한 사용법은 각 함수를 개별적으로 호출해보세요.")
        print("\n🎯 고객센터 문의 관리 기능:")
        print("   - 고객센터 문의 목록 조회")
        print("   - 답변 대기/확인 대기 문의 조회")
        print("   - 고객센터 문의 답변 처리")
        print("   - 고객센터 문의 확인 처리")
        print("   - 상품별 고객센터 문의 조회")
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {str(e)}")


if __name__ == "__main__":
    main()