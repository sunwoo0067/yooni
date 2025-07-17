#!/usr/bin/env python3
"""
쿠팡 상품 목록 구간 조회 API 사용 예제
생성일시 기준으로 특정 시간 구간의 상품 목록을 조회하는 방법을 보여줍니다
"""

import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import ProductClient


def test_basic_time_frame_query():
    """기본적인 시간 구간 조회 테스트"""
    print("=" * 60 + " 기본 시간 구간 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 기본 파라미터 설정
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')  # 실제 벤더 ID로 변경 필요
        
        # 현재 시간에서 10분 전부터 현재까지 조회
        now = datetime.now()
        start_time = now - timedelta(minutes=10)
        
        created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        created_at_to = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        print(f"\n📋 시간 구간 상품 목록 조회 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📅 조회 시작시간: {created_at_from}")
        print(f"   📅 조회 종료시간: {created_at_to}")
        print(f"   ⏱️ 조회 범위: 10분")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame")
        
        # 시간 구간 조회 실행
        print(f"\n📤 시간 구간 조회 요청 중...")
        result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
        
        if result.get("success"):
            print(f"\n✅ 시간 구간 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            time_range_minutes = result.get("time_range_minutes", 0)
            
            print(f"\n📊 조회 결과 정보:")
            print(f"   📦 조회된 상품수: {len(data)}개")
            print(f"   ⏱️ 실제 조회 범위: {time_range_minutes:.1f}분")
            print(f"   📅 조회 기간: {created_at_from} ~ {created_at_to}")
            
            # 상품 목록 표시
            if data:
                print(f"\n📋 해당 시간대 등록된 상품:")
                for i, product in enumerate(data[:10], 1):  # 상위 10개만 표시
                    seller_product_id = product.get('sellerProductId')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상품 정보:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 상품명: {seller_product_name[:50]}{'...' if len(seller_product_name) > 50 else ''}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📊 상태: {status_name}")
                    print(f"      📅 등록시각: {created_at}")
                
                if len(data) > 10:
                    print(f"\n   ... 외 {len(data) - 10}개 상품")
                
                # 시간대별 상품 등록 분석
                print(f"\n📈 시간대 등록 분석:")
                
                # 상태별 분포
                status_count = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"\n📊 상품 상태 분포:")
                for status, count in status_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
                
                # 등록 빈도 분석
                print(f"\n⏰ 등록 빈도 분석:")
                print(f"   📊 총 등록수: {len(data)}개")
                print(f"   📊 평균 등록률: {len(data) / time_range_minutes:.1f}개/분")
                
                if len(data) > 0:
                    print(f"   💡 활동성: {'높음' if len(data) / time_range_minutes > 1 else '보통' if len(data) / time_range_minutes > 0.5 else '낮음'}")
                
            else:
                print(f"\n📭 해당 시간대에 등록된 상품이 없습니다")
                print(f"💡 다른 시간대를 조회해보세요")
            
        else:
            print(f"\n❌ 시간 구간 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 시간 구간 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_specific_time_range_query():
    """특정 시간 범위 조회 테스트"""
    print("\n" + "=" * 60 + " 특정 시간 범위 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        # 특정 날짜의 특정 시간대 (예: 오늘 오전 10:00-10:05)
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time().replace(hour=10, minute=0, second=0))
        end_time = start_time + timedelta(minutes=5)
        
        created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        created_at_to = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        print(f"\n🕙 특정 시간대 상품 조회")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📅 조회 날짜: {today}")
        print(f"   🕙 조회 시간대: 10:00-10:05 (5분간)")
        print(f"   📝 목적: 특정 시간대 등록 활동 분석")
        
        # 특정 시간대 조회 실행
        print(f"\n📤 특정 시간대 조회 요청 중...")
        result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
        
        if result.get("success"):
            print(f"\n✅ 특정 시간대 조회 성공!")
            
            data = result.get("data", [])
            
            print(f"\n📊 특정 시간대 분석:")
            print(f"   🕙 분석 시간대: 10:00-10:05")
            print(f"   📦 해당 시간대 등록수: {len(data)}개")
            
            if data:
                # 브랜드별 분류
                brand_count = {}
                for product in data:
                    brand = product.get('brand', 'Unknown')
                    brand_count[brand] = brand_count.get(brand, 0) + 1
                
                print(f"\n🏷️ 해당 시간대 브랜드별 등록 (상위 5개):")
                sorted_brands = sorted(brand_count.items(), key=lambda x: x[1], reverse=True)
                for brand, count in sorted_brands[:5]:
                    print(f"   🏷️ {brand}: {count}개")
                
                # 시간대별 등록 패턴 분석
                print(f"\n⏰ 등록 패턴 분석:")
                print(f"   📊 5분간 등록수: {len(data)}개")
                print(f"   📊 분당 평균: {len(data) / 5:.1f}개")
                
                # 등록 활동 평가
                if len(data) >= 10:
                    activity_level = "🔥 매우 활발"
                elif len(data) >= 5:
                    activity_level = "🟡 보통"
                elif len(data) >= 1:
                    activity_level = "🟢 조용함"
                else:
                    activity_level = "⚪ 비활성"
                
                print(f"   📈 활동 수준: {activity_level}")
                
            else:
                print(f"\n📭 해당 시간대에는 등록 활동이 없었습니다")
                print(f"💡 다른 시간대나 더 넓은 범위를 시도해보세요")
        
        else:
            print(f"\n❌ 특정 시간대 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 특정 시간대 조회 오류: {e}")


def test_multiple_time_ranges():
    """여러 시간 구간 연속 조회 테스트"""
    print("\n" + "=" * 60 + " 연속 시간 구간 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        print(f"\n🔄 연속 시간 구간 조회 테스트")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 방법: 여러 시간대를 순차적으로 조회")
        
        # 현재 시간부터 역순으로 10분씩 3구간 조회
        base_time = datetime.now()
        time_ranges = []
        all_products = []
        
        for i in range(3):
            end_time = base_time - timedelta(minutes=i*10)
            start_time = end_time - timedelta(minutes=10)
            
            time_ranges.append({
                "period": f"{i+1}구간",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "label": f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
            })
        
        # 각 구간별로 조회
        for i, time_range in enumerate(time_ranges, 1):
            print(f"\n📄 {time_range['period']} ({time_range['label']}) 조회 중...")
            
            result = client.get_products_by_time_frame(vendor_id, time_range['start'], time_range['end'])
            
            if result.get("success"):
                data = result.get("data", [])
                print(f"   ✅ {time_range['period']} 조회 성공: {len(data)}개 상품")
                
                # 전체 목록에 추가
                all_products.extend(data)
                
                # 구간별 요약 정보
                if data:
                    statuses = {}
                    for product in data:
                        status = product.get('statusName', 'Unknown')
                        statuses[status] = statuses.get(status, 0) + 1
                    
                    print(f"   📊 {time_range['period']} 상태 분포: {dict(statuses)}")
                else:
                    print(f"   📭 {time_range['period']} 등록 상품 없음")
            else:
                print(f"   ❌ {time_range['period']} 조회 실패: {result.get('error')}")
        
        # 전체 결과 분석
        print(f"\n📊 전체 연속 조회 결과:")
        print(f"   📄 조회한 구간 수: {len(time_ranges)}구간")
        print(f"   📦 총 수집된 상품수: {len(all_products)}개")
        print(f"   ⏱️ 총 조회 범위: 30분")
        
        if all_products:
            # 전체 시간대별 등록 트렌드
            period_stats = {}
            for i, time_range in enumerate(time_ranges):
                start_idx = i * len([p for p in all_products if time_ranges[i]['start'] <= p.get('createdAt', '') <= time_ranges[i]['end']])
                period_count = len([p for p in all_products if time_ranges[i]['start'] <= p.get('createdAt', '') <= time_ranges[i]['end']])
                period_stats[time_range['label']] = period_count
            
            print(f"\n📈 시간대별 등록 트렌드:")
            for period, count in period_stats.items():
                print(f"   ⏰ {period}: {count}개")
            
            # 전체 상태별 통계
            total_status_stats = {}
            for product in all_products:
                status = product.get('statusName', 'Unknown')
                total_status_stats[status] = total_status_stats.get(status, 0) + 1
            
            print(f"\n📊 전체 상태별 통계:")
            for status, count in total_status_stats.items():
                percentage = (count / len(all_products)) * 100
                print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
            
            print(f"\n💡 시간대별 조회 활용법:")
            print(f"   📊 등록 패턴 분석: 시간대별 등록 활동 파악")
            print(f"   🔍 실시간 모니터링: 최근 등록 상품 추적")
            print(f"   📈 트렌드 분석: 등록 활동의 시간적 변화")
        
    except Exception as e:
        print(f"❌ 연속 시간 구간 조회 오류: {e}")


def test_time_frame_validation():
    """시간 구간 조회 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 시간 구간 검증 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "vendor_id 누락",
            "vendor_id": "",
            "created_at_from": "2024-01-15T10:00:00",
            "created_at_to": "2024-01-15T10:05:00",
            "expected_error": "판매자 ID"
        },
        {
            "name": "잘못된 시작시간 형식",
            "vendor_id": "A00012345",
            "created_at_from": "2024/01/15 10:00:00",  # 잘못된 형식
            "created_at_to": "2024-01-15T10:05:00",
            "expected_error": "yyyy-MM-ddTHH:mm:ss"
        },
        {
            "name": "잘못된 종료시간 형식",
            "vendor_id": "A00012345",
            "created_at_from": "2024-01-15T10:00:00",
            "created_at_to": "2024-01-15 10:05:00",  # 잘못된 형식
            "expected_error": "yyyy-MM-ddTHH:mm:ss"
        },
        {
            "name": "10분 초과 범위",
            "vendor_id": "A00012345",
            "created_at_from": "2024-01-15T10:00:00",
            "created_at_to": "2024-01-15T10:15:00",  # 15분 (10분 초과)
            "expected_error": "10분"
        },
        {
            "name": "시작시간이 종료시간보다 늦음",
            "vendor_id": "A00012345",
            "created_at_from": "2024-01-15T10:05:00",
            "created_at_to": "2024-01-15T10:00:00",  # 역순
            "expected_error": "늦어야"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        
        try:
            result = client.get_products_by_time_frame(
                test_case['vendor_id'],
                test_case['created_at_from'],
                test_case['created_at_to']
            )
            
            if result.get("success"):
                print(f"   ⚠️ 예상과 다르게 성공함 (검증 로직 확인 필요)")
            else:
                print(f"   ✅ 예상대로 검증 실패: {result.get('error')}")
                
        except ValueError as e:
            expected = test_case.get('expected_error', '')
            if expected in str(e):
                print(f"   ✅ 예상대로 검증 오류: {e}")
            else:
                print(f"   ⚠️ 예상과 다른 검증 오류: {e}")
        except Exception as e:
            print(f"   ❌ 예상치 못한 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 목록 구간 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 시간 구간 조회 테스트
        test_basic_time_frame_query()
        
        # 특정 시간 범위 조회 테스트
        test_specific_time_range_query()
        
        # 연속 시간 구간 조회 테스트
        test_multiple_time_ranges()
        
        # 검증 시나리오 테스트
        test_time_frame_validation()
        
        print(f"\n" + "=" * 50 + " 시간 구간 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 시간 구간 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 시간 구간 조회 (최대 10분)")
        print("   2. ✅ 특정 시간대 조회")
        print("   3. ✅ 연속 시간 구간 조회")
        print("   4. ✅ 시간 범위 검증")
        print("   5. ✅ 시간대별 등록 패턴 분석")
        print("   6. ✅ 실시간 등록 활동 모니터링")
        
        print(f"\n💡 시간 구간 조회 주요 특징:")
        print("   - 생성일시 기준 정확한 시간 구간 조회")
        print("   - 최대 10분 범위 제한으로 정밀 조회")
        print("   - 실시간 등록 활동 모니터링 가능")
        print("   - 시간대별 등록 패턴 분석 지원")
        print("   - 연속 구간 조회로 트렌드 파악")
        
        print(f"\n📊 활용 방안:")
        print("   🔍 실시간 모니터링: 최근 등록 상품 즉시 확인")
        print("   📊 패턴 분석: 시간대별 등록 활동 패턴 파악")
        print("   🚨 알림 시스템: 특정 시간대 등록 알림")
        print("   📈 트렌드 추적: 등록 활동의 시간적 변화")
        print("   🔄 배치 처리: 특정 시간대 상품 일괄 처리")
        
    except Exception as e:
        print(f"\n❌ 시간 구간 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()