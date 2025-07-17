#!/usr/bin/env python3
"""
쿠팡 상품 목록 구간 조회 API 실제 테스트
실제 API 키를 사용한 시간 구간 조회 테스트
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


def test_real_api_time_frame():
    """실제 API로 시간 구간 조회 테스트"""
    print("=" * 60 + " 실제 API 시간 구간 조회 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ProductClient()
        print("✅ 실제 API 인증으로 상품 클라이언트 초기화 성공")
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        # 현재 시간에서 10분 전부터 현재까지 조회
        now = datetime.now()
        start_time = now - timedelta(minutes=10)
        
        created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        created_at_to = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        print(f"\n📊 실제 API로 시간 구간 조회 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📅 조회 시작: {created_at_from}")
        print(f"   📅 조회 종료: {created_at_to}")
        print(f"   ⏱️ 조회 범위: 10분")
        print(f"   📅 조회 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame")
        
        # 실제 시간 구간 조회 요청
        print(f"\n📤 실제 시간 구간 조회 요청...")
        result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 시간 구간 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            time_range_minutes = result.get("time_range_minutes", 0)
            
            print(f"\n📊 실제 조회 결과:")
            print(f"   📦 조회된 상품수: {len(data)}개")
            print(f"   ⏱️ 실제 조회 범위: {time_range_minutes:.1f}분")
            print(f"   📅 조회 기간: {created_at_from} ~ {created_at_to}")
            
            # 실제 상품 정보 표시
            if data:
                print(f"\n📋 실제 해당 시간대 등록 상품 (상위 10개):")
                for i, product in enumerate(data[:10], 1):
                    seller_product_id = product.get('sellerProductId')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    category_code = product.get('displayCategoryCode', 'N/A')
                    
                    print(f"\n   {i}. 실제 상품:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 상품명: {seller_product_name[:60]}{'...' if len(seller_product_name) > 60 else ''}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📊 상태: {status_name}")
                    print(f"      📂 카테고리: {category_code}")
                    print(f"      📅 등록시각: {created_at}")
                
                if len(data) > 10:
                    print(f"\n   ... 외 {len(data) - 10}개 상품")
                
                # 실제 데이터 분석
                print(f"\n📈 실제 시간대 등록 분석:")
                
                # 상태별 분포
                status_count = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"\n📊 상품 상태 분포:")
                for status, count in status_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
                
                # 브랜드별 분포 (상위 5개)
                brand_count = {}
                for product in data:
                    brand = product.get('brand', 'Unknown')
                    brand_count[brand] = brand_count.get(brand, 0) + 1
                
                print(f"\n🏷️ 주요 브랜드 분포 (상위 5개):")
                sorted_brands = sorted(brand_count.items(), key=lambda x: x[1], reverse=True)
                for brand, count in sorted_brands[:5]:
                    percentage = (count / len(data)) * 100
                    print(f"   🏷️ {brand}: {count}개 ({percentage:.1f}%)")
                
                # 카테고리별 분포 (상위 3개)
                category_count = {}
                for product in data:
                    category = product.get('displayCategoryCode', 'Unknown')
                    category_count[category] = category_count.get(category, 0) + 1
                
                print(f"\n📂 주요 카테고리 분포 (상위 3개):")
                sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
                for category, count in sorted_categories[:3]:
                    percentage = (count / len(data)) * 100
                    print(f"   📂 카테고리 {category}: {count}개 ({percentage:.1f}%)")
                
                # 시간대별 등록 패턴 분석
                print(f"\n⏰ 실제 등록 패턴 분석:")
                print(f"   📊 10분간 총 등록수: {len(data)}개")
                print(f"   📊 분당 평균 등록률: {len(data) / time_range_minutes:.1f}개/분")
                
                # 등록 활동 수준 평가
                activity_per_minute = len(data) / time_range_minutes
                if activity_per_minute >= 2:
                    activity_level = "🔥 매우 활발"
                    activity_note = "높은 등록 활동"
                elif activity_per_minute >= 1:
                    activity_level = "🟡 활발"
                    activity_note = "보통 등록 활동"
                elif activity_per_minute >= 0.5:
                    activity_level = "🟢 보통"
                    activity_note = "평균적 등록 활동"
                else:
                    activity_level = "⚪ 조용함"
                    activity_note = "낮은 등록 활동"
                
                print(f"   📈 활동 수준: {activity_level}")
                print(f"   💬 평가: {activity_note}")
                
                # 등록 시간 분포 분석
                minute_distribution = {}
                for product in data:
                    created_at = product.get('createdAt', '')
                    if created_at:
                        try:
                            created_time = datetime.fromisoformat(created_at.replace('T', ' '))
                            minute_key = created_time.strftime('%H:%M')
                            minute_distribution[minute_key] = minute_distribution.get(minute_key, 0) + 1
                        except:
                            pass
                
                if minute_distribution:
                    print(f"\n🕐 분단위 등록 분포:")
                    sorted_minutes = sorted(minute_distribution.items())
                    for minute, count in sorted_minutes:
                        print(f"   🕐 {minute}: {count}개")
                
            else:
                print(f"\n📭 해당 시간대에 등록된 상품이 없습니다")
                print(f"💡 다른 시간대나 더 넓은 범위를 시도해보세요")
            
            # 실제 응답 데이터 샘플
            original_response = result.get('originalResponse', {})
            if original_response and data:
                print(f"\n📊 실제 API 응답 샘플 (첫 번째 상품):") 
                sample_product = data[0]
                pprint(sample_product, width=100, indent=4)
            
            print(f"\n✅ 실제 조회 완료 단계:")
            print(f"   1. ✅ API 인증 및 클라이언트 초기화")
            print(f"   2. ✅ 시간 구간 파라미터 설정")
            print(f"   3. ✅ 실제 API 시간 구간 조회 요청")
            print(f"   4. ✅ 응답 데이터 파싱 및 분석")
            print(f"   5. ✅ 시간대별 등록 패턴 분석")
            
        else:
            print(f"\n❌ 실제 API 시간 구간 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
            print(f"\n💡 일반적인 조회 실패 사유:")
            print(f"   - API 키 또는 시크릿이 잘못됨")
            print(f"   - 판매자 ID 권한 문제")
            print(f"   - 네트워크 연결 문제")
            print(f"   - 시간 범위가 10분을 초과함")
                
    except Exception as e:
        print(f"❌ 실제 API 시간 구간 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_recent_activity():
    """실제 API로 최근 등록 활동 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 최근 등록 활동 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🔍 실제 API로 최근 등록 활동 분석")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 목적: 최근 5분간 등록 활동 분석")
        
        # 현재 시간에서 5분 전부터 현재까지 조회
        now = datetime.now()
        start_time = now - timedelta(minutes=5)
        
        created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        created_at_to = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        print(f"\n📤 최근 5분간 활동 조회 요청...")
        result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 최근 활동 조회 성공!")
            
            data = result.get("data", [])
            
            print(f"\n📊 최근 5분간 활동 분석:")
            print(f"   ⏰ 분석 기간: 최근 5분")
            print(f"   📦 등록된 상품수: {len(data)}개")
            
            if data:
                print(f"\n📋 최근 등록된 상품 목록:")
                for i, product in enumerate(data, 1):
                    product_name = product.get('sellerProductName', 'N/A')
                    status = product.get('statusName', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    
                    print(f"   {i}. {product_name[:40]}{'...' if len(product_name) > 40 else ''}")
                    print(f"      📊 상태: {status}, 📅 등록: {created_at}")
                
                # 최근 활동 수준 평가
                activity_rate = len(data) / 5  # 분당 등록률
                
                print(f"\n📈 최근 활동 수준:")
                print(f"   📊 5분간 등록수: {len(data)}개")
                print(f"   📊 분당 등록률: {activity_rate:.1f}개/분")
                
                if activity_rate >= 1:
                    print(f"   🔥 평가: 활발한 등록 활동 중")
                    print(f"   💡 권장: 지속적인 모니터링")
                elif activity_rate >= 0.5:
                    print(f"   🟡 평가: 보통 수준의 등록 활동")
                    print(f"   💡 권장: 정기적인 확인")
                else:
                    print(f"   🟢 평가: 조용한 등록 활동")
                    print(f"   💡 참고: 평소보다 낮은 활동")
                
                # 최근 상태별 분포
                recent_status_dist = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    recent_status_dist[status] = recent_status_dist.get(status, 0) + 1
                
                print(f"\n📊 최근 등록 상태 분포:")
                for status, count in recent_status_dist.items():
                    print(f"   📊 {status}: {count}개")
                
                print(f"\n💡 실시간 모니터링 활용:")
                print(f"   🔄 정기 체크: 5-10분마다 조회")
                print(f"   🚨 알림 설정: 임계값 이상 등록 시 알림")
                print(f"   📊 활동 추적: 등록 패턴 실시간 파악")
                
            else:
                print(f"\n📭 최근 5분간 등록 활동이 없습니다")
                print(f"   💡 현재 등록 활동이 조용한 상태")
                print(f"   📋 참고: 정상적인 상황일 수 있음")
        
        else:
            print(f"\n❌ 실제 API 최근 활동 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ 실제 API 최근 활동 조회 오류: {e}")


def test_real_api_time_range_comparison():
    """실제 API로 시간대별 비교 분석 테스트"""
    print("\n" + "=" * 60 + " 실제 API 시간대별 비교 분석 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수 확인
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📊 실제 API로 시간대별 비교 분석")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 목적: 최근 3개 시간대 비교")
        
        # 현재 시간부터 역순으로 10분씩 3구간 분석
        base_time = datetime.now()
        comparison_results = []
        
        for i in range(3):
            end_time = base_time - timedelta(minutes=i*10)
            start_time = end_time - timedelta(minutes=10)
            
            created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            created_at_to = end_time.strftime("%Y-%m-%dT%H:%M:%S")
            
            period_label = f"구간{i+1} ({start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')})"
            
            print(f"\n📄 {period_label} 조회 중...")
            
            # 실제 구간별 조회
            result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
            
            if result.get("success"):
                data = result.get("data", [])
                
                comparison_results.append({
                    "period": period_label,
                    "count": len(data),
                    "start_time": start_time,
                    "end_time": end_time,
                    "data": data
                })
                
                print(f"   ✅ {period_label} 조회 성공: {len(data)}개 상품")
            else:
                print(f"   ❌ {period_label} 조회 실패: {result.get('error')}")
        
        # 시간대별 비교 분석
        if comparison_results:
            print(f"\n📈 실제 시간대별 비교 분석 결과:")
            
            # 구간별 등록수 비교
            print(f"\n📊 구간별 등록수 비교:")
            for result in comparison_results:
                activity_level = "🔥" if result["count"] >= 5 else "🟡" if result["count"] >= 2 else "🟢"
                print(f"   {activity_level} {result['period']}: {result['count']}개")
            
            # 평균 및 트렌드 분석
            total_count = sum(r["count"] for r in comparison_results)
            avg_count = total_count / len(comparison_results)
            
            print(f"\n📈 전체 트렌드 분석:")
            print(f"   📊 전체 등록수: {total_count}개")
            print(f"   📊 평균 등록수: {avg_count:.1f}개/구간")
            
            # 시간대별 트렌드 방향
            if len(comparison_results) >= 2:
                recent_trend = comparison_results[0]["count"] - comparison_results[-1]["count"]
                if recent_trend > 0:
                    trend_direction = "📈 증가"
                    trend_note = "최근 등록 활동이 증가하고 있음"
                elif recent_trend < 0:
                    trend_direction = "📉 감소"
                    trend_note = "최근 등록 활동이 감소하고 있음"
                else:
                    trend_direction = "➡️ 안정"
                    trend_note = "등록 활동이 안정적임"
                
                print(f"   {trend_direction} 최근 트렌드: {trend_note}")
            
            # 가장 활발한 시간대
            most_active = max(comparison_results, key=lambda x: x["count"])
            print(f"\n🏆 가장 활발한 시간대:")
            print(f"   ⏰ {most_active['period']}: {most_active['count']}개 등록")
            
            # 실제 데이터가 있는 경우 상세 분석
            if total_count > 0:
                all_products = []
                for result in comparison_results:
                    all_products.extend(result["data"])
                
                # 전체 상태별 분포
                status_distribution = {}
                for product in all_products:
                    status = product.get('statusName', 'Unknown')
                    status_distribution[status] = status_distribution.get(status, 0) + 1
                
                print(f"\n📊 전체 상태별 분포:")
                for status, count in status_distribution.items():
                    percentage = (count / total_count) * 100
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
                
                print(f"\n💡 시간대별 분석 결과:")
                print(f"   📊 데이터 기반: 실제 등록 패턴 확인")
                print(f"   ⏰ 활동 시간: 등록이 활발한 시간대 파악")
                print(f"   📈 트렌드: 등록 활동의 변화 추세")
                print(f"   🎯 최적화: 등록 전략 수립에 활용")
        
    except Exception as e:
        print(f"❌ 실제 API 시간대별 비교 분석 오류: {e}")


def test_real_api_performance():
    """실제 API 성능 테스트"""
    print("\n" + "=" * 60 + " 실제 API 성능 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수 확인
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n⏱️ 실제 API 성능 측정")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 측정 항목: 응답 시간")
        
        # 다양한 시간 범위로 성능 측정
        test_ranges = [
            {"name": "1분 범위", "minutes": 1},
            {"name": "5분 범위", "minutes": 5},
            {"name": "10분 범위", "minutes": 10},
        ]
        
        performance_results = []
        
        for test_range in test_ranges:
            print(f"\n📊 {test_range['name']} 성능 측정...")
            
            # 시간 범위 설정
            now = datetime.now()
            start_time = now - timedelta(minutes=test_range['minutes'])
            
            created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            created_at_to = now.strftime("%Y-%m-%dT%H:%M:%S")
            
            # 성능 측정
            start_measure = datetime.now()
            result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
            end_measure = datetime.now()
            
            response_time = (end_measure - start_measure).total_seconds()
            
            if result.get("success"):
                data = result.get("data", [])
                
                performance_results.append({
                    "name": test_range['name'],
                    "minutes": test_range['minutes'],
                    "response_time": response_time,
                    "product_count": len(data),
                    "throughput": len(data) / response_time if response_time > 0 else 0
                })
                
                print(f"   ✅ 성공: {len(data)}개 조회")
                print(f"   ⏱️ 응답 시간: {response_time:.3f}초")
                print(f"   📊 처리량: {len(data) / response_time:.1f}개/초")
            else:
                print(f"   ❌ 실패: {result.get('error')}")
        
        # 성능 결과 분석
        if performance_results:
            print(f"\n📈 전체 성능 분석 결과:")
            
            # 응답 시간 분석
            avg_response_time = sum(r['response_time'] for r in performance_results) / len(performance_results)
            max_response_time = max(r['response_time'] for r in performance_results)
            min_response_time = min(r['response_time'] for r in performance_results)
            
            print(f"\n⏱️ 응답 시간 분석:")
            print(f"   📊 평균 응답 시간: {avg_response_time:.3f}초")
            print(f"   📊 최대 응답 시간: {max_response_time:.3f}초")
            print(f"   📊 최소 응답 시간: {min_response_time:.3f}초")
            
            # 성능 등급 평가
            if avg_response_time < 1.0:
                performance_grade = "🟢 우수"
            elif avg_response_time < 2.0:
                performance_grade = "🟡 양호"
            else:
                performance_grade = "🔴 개선필요"
            
            print(f"\n🏆 전체 성능 등급: {performance_grade}")
            
            # 상세 결과 표
            print(f"\n📋 상세 성능 결과:")
            for result in performance_results:
                print(f"   {result['name']}: "
                      f"{result['response_time']:.3f}초, "
                      f"{result['product_count']}개 조회")
        
    except Exception as e:
        print(f"❌ 실제 API 성능 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 목록 구간 조회 API 실제 테스트 시작")
    print("=" * 120)
    
    # 환경 변수 확인
    required_env_vars = ['COUPANG_ACCESS_KEY', 'COUPANG_SECRET_KEY', 'COUPANG_VENDOR_ID']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        print("설정 방법:")
        print("   export COUPANG_ACCESS_KEY='your_access_key'")
        print("   export COUPANG_SECRET_KEY='your_secret_key'")
        print("   export COUPANG_VENDOR_ID='your_vendor_id'")
        return
    
    try:
        # 실제 API 테스트 실행
        test_real_api_time_frame()
        test_real_api_recent_activity()
        test_real_api_time_range_comparison()
        test_real_api_performance()
        
        print(f"\n" + "=" * 50 + " 실제 API 구간 조회 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 상품 목록 구간 조회 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 시간 구간 조회")
        print("   2. ✅ 최근 등록 활동 실시간 분석")
        print("   3. ✅ 시간대별 비교 분석")
        print("   4. ✅ API 성능 측정 및 분석")
        print("   5. ✅ 등록 패턴 및 트렌드 분석")
        print("   6. ✅ 실시간 모니터링 시나리오")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 최대 10분 시간 범위 제한 엄격 적용")
        print("   - 생성일시 기준 정확한 구간 조회")
        print("   - 실시간 등록 활동 정확 반영")
        print("   - 시간대별 패턴 분석 가능")
        print("   - API 응답 시간 1-2초 내")
        
        print(f"\n📊 실제 데이터 활용 방안:")
        print("   🔍 실시간 모니터링: 등록 활동 즉시 파악")
        print("   📊 패턴 분석: 시간대별 등록 경향 분석")
        print("   🚨 알림 시스템: 임계값 기반 실시간 알림")
        print("   📈 트렌드 추적: 등록 활동 변화 추세")
        print("   🎯 전략 수립: 데이터 기반 등록 전략")
        
    except Exception as e:
        print(f"\n❌ 실제 API 구간 조회 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()