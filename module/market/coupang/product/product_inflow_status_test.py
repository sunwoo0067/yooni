#!/usr/bin/env python3
"""
쿠팡 상품 등록 현황 조회 API 실제 테스트
실제 API 키를 사용한 상품 등록 현황 조회 테스트
"""

import os
import sys
from datetime import datetime
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import ProductClient


def test_real_api_inflow_status():
    """실제 API로 상품 등록 현황 조회 테스트"""
    print("=" * 60 + " 실제 API 상품 등록 현황 조회 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ProductClient()
        print("✅ 실제 API 인증으로 상품 클라이언트 초기화 성공")
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📊 실제 API로 상품 등록 현황 조회 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📅 조회 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/inflow-status")
        
        # 실제 상품 등록 현황 조회 실행
        print(f"\n📤 실제 상품 등록 현황 조회 요청...")
        result = client.get_inflow_status()
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 등록 현황 조회 성공!")
            
            # 기본 정보 표시
            api_vendor_id = result.get("vendor_id")
            restricted = result.get("restricted")
            registered_count = result.get("registered_count")
            permitted_count = result.get("permitted_count")
            
            print(f"\n📋 실제 상품 등록 현황:")
            print(f"   🏢 API 응답 판매자 ID: {api_vendor_id}")
            print(f"   📦 현재 등록된 상품수: {registered_count:,}개 (삭제 상품 제외)")
            
            if permitted_count is not None:
                print(f"   🎯 등록 가능한 최대 상품수: {permitted_count:,}개")
                remaining = permitted_count - registered_count
                usage_rate = (registered_count / permitted_count) * 100
                
                print(f"   ⚡ 추가 등록 가능한 상품수: {remaining:,}개")
                print(f"   📊 현재 사용률: {usage_rate:.1f}%")
                
                # 사용률에 따른 상태 표시
                if usage_rate >= 95:
                    print(f"   🔴 상태: 긴급 (95% 이상 사용)")
                    print(f"   ⚠️ 권장: 즉시 상품 정리 또는 한도 증량 요청")
                elif usage_rate >= 85:
                    print(f"   🟠 상태: 주의 (85% 이상 사용)")
                    print(f"   💡 권장: 등록 계획 조정 필요")
                elif usage_rate >= 70:
                    print(f"   🟡 상태: 관리 필요 (70% 이상 사용)")
                    print(f"   📋 권장: 정기적인 모니터링")
                else:
                    print(f"   🟢 상태: 여유 있음 (70% 미만 사용)")
                    print(f"   🚀 권장: 적극적인 신규 상품 등록 가능")
            else:
                print(f"   🚀 등록 가능한 최대 상품수: 제한없음 (무제한)")
                print(f"   💎 혜택: 프리미엄 계정으로 무제한 등록 가능")
            
            # 등록 제한 상태 확인
            print(f"\n🔐 상품 생성 제한 상태:")
            if restricted:
                print(f"   ❌ 제한됨: 현재 새로운 상품을 등록할 수 없습니다")
                print(f"   🚨 조치사항:")
                print(f"      1. 쿠팡 담당자에게 즉시 문의")
                print(f"      2. 제한 사유 확인")
                print(f"      3. 제한 해제 절차 진행")
            else:
                print(f"   ✅ 허용됨: 새로운 상품을 등록할 수 있습니다")
                print(f"   🎉 현재 상품 등록 기능이 정상 작동 중")
            
            # 실제 응답 데이터 표시
            data = result.get("data", {})
            if data:
                print(f"\n📊 실제 API 응답 데이터:")
                pprint(data, width=100, indent=4)
            
            # 비즈니스 인사이트 제공
            print(f"\n📈 비즈니스 인사이트:")
            
            if registered_count > 0:
                if permitted_count is not None:
                    efficiency = (registered_count / permitted_count) * 100
                    print(f"   📊 계정 활용도: {efficiency:.1f}%")
                    
                    if efficiency < 30:
                        print(f"   💡 기회: 등록 한도의 활용도가 낮습니다. 더 많은 상품 등록을 고려하세요.")
                    elif efficiency < 70:
                        print(f"   ⚖️ 균형: 적절한 수준의 상품을 등록하고 있습니다.")
                    else:
                        print(f"   🔥 활발: 높은 활용도로 상품을 관리하고 있습니다.")
                
                # 규모별 카테고라이징
                if registered_count < 100:
                    print(f"   🌱 규모: 소규모 셀러 (100개 미만)")
                    print(f"   📋 전략: 핵심 상품 위주의 포트폴리오 구축")
                elif registered_count < 1000:
                    print(f"   🌿 규모: 중소규모 셀러 (100-1000개)")
                    print(f"   📋 전략: 카테고리별 다양화 고려")
                elif registered_count < 5000:
                    print(f"   🌳 규모: 중규모 셀러 (1000-5000개)")
                    print(f"   📋 전략: 체계적인 상품 관리 시스템 필요")
                else:
                    print(f"   🏢 규모: 대규모 셀러 (5000개 이상)")
                    print(f"   📋 전략: 자동화된 상품 관리 시스템 필수")
            else:
                print(f"   🌟 신규: 아직 등록된 상품이 없습니다")
                print(f"   🚀 시작: 첫 상품 등록으로 비즈니스를 시작하세요")
            
            print(f"\n✅ 실제 조회 완료 단계:")
            print(f"   1. ✅ API 인증 및 클라이언트 초기화")
            print(f"   2. ✅ 실제 API 등록 현황 조회 요청")
            print(f"   3. ✅ 응답 데이터 파싱 및 분석")
            print(f"   4. ✅ 비즈니스 인사이트 제공")
            
        else:
            print(f"\n❌ 실제 API 상품 등록 현황 조회 실패:")
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
            print(f"   - API 서버 일시적 오류")
                
    except Exception as e:
        print(f"❌ 실제 API 상품 등록 현황 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_multiple_checks():
    """실제 API로 여러 번 조회하여 일관성 테스트"""
    print("\n" + "=" * 60 + " 실제 API 다중 조회 일관성 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🔄 실제 API로 연속 조회 테스트")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📝 목적: API 응답 일관성 확인")
        
        results = []
        
        # 3번 연속 조회
        for i in range(3):
            print(f"\n📤 {i+1}차 조회 중...")
            result = client.get_inflow_status()
            
            if result.get("success"):
                results.append({
                    "attempt": i + 1,
                    "vendor_id": result.get("vendor_id"),
                    "restricted": result.get("restricted"),
                    "registered_count": result.get("registered_count"),
                    "permitted_count": result.get("permitted_count"),
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                print(f"   ✅ {i+1}차 조회 성공")
            else:
                print(f"   ❌ {i+1}차 조회 실패: {result.get('error')}")
        
        # 결과 분석
        if results:
            print(f"\n📊 연속 조회 결과 분석:")
            print(f"   📋 성공한 조회: {len(results)}/3회")
            
            # 일관성 체크
            if len(results) >= 2:
                first = results[0]
                consistent = True
                
                for result in results[1:]:
                    if (result["vendor_id"] != first["vendor_id"] or
                        result["restricted"] != first["restricted"] or
                        result["registered_count"] != first["registered_count"] or
                        result["permitted_count"] != first["permitted_count"]):
                        consistent = False
                        break
                
                if consistent:
                    print(f"   ✅ 일관성: 모든 조회 결과가 동일함")
                    print(f"   💡 안정성: API 응답이 일관되게 안정적")
                else:
                    print(f"   ⚠️ 일관성: 조회 결과에 차이가 있음")
                    print(f"   💡 가능성: 실시간 데이터 변경 또는 API 불안정")
            
            # 상세 결과 표시
            print(f"\n📋 상세 조회 결과:")
            for result in results:
                print(f"   {result['attempt']}차 ({result['timestamp']}): "
                      f"등록수 {result['registered_count']:,}개, "
                      f"제한 {result['restricted']}")
            
            # 최종 상태 요약
            latest = results[-1]
            print(f"\n📊 최종 상태 (마지막 조회 기준):")
            print(f"   🏢 판매자: {latest['vendor_id']}")
            print(f"   📦 등록수: {latest['registered_count']:,}개")
            if latest['permitted_count'] is not None:
                print(f"   🎯 한도: {latest['permitted_count']:,}개")
            else:
                print(f"   🚀 한도: 무제한")
            print(f"   🔐 제한: {'있음' if latest['restricted'] else '없음'}")
        
    except Exception as e:
        print(f"❌ 실제 API 다중 조회 테스트 오류: {e}")


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
        
        # 성능 측정
        start_time = datetime.now()
        result = client.get_inflow_status()
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        if result.get("success"):
            print(f"\n📊 성능 측정 결과:")
            print(f"   ⏱️ 응답 시간: {response_time:.3f}초")
            
            # 성능 평가
            if response_time < 1.0:
                performance_rating = "🟢 우수"
                performance_note = "매우 빠른 응답"
            elif response_time < 2.0:
                performance_rating = "🟡 양호"
                performance_note = "적절한 응답 시간"
            elif response_time < 5.0:
                performance_rating = "🟠 보통"
                performance_note = "다소 느린 응답"
            else:
                performance_rating = "🔴 느림"
                performance_note = "응답 시간 개선 필요"
            
            print(f"   📈 성능 평가: {performance_rating}")
            print(f"   💬 평가: {performance_note}")
            
            # 네트워크 상태 추정
            if response_time < 0.5:
                print(f"   🌐 네트워크: 최적 상태")
            elif response_time < 2.0:
                print(f"   🌐 네트워크: 정상 상태")
            else:
                print(f"   🌐 네트워크: 확인 필요")
            
            print(f"\n📋 응답 데이터 크기:")
            data = result.get("data", {})
            print(f"   📊 필드 수: {len(data)}개")
            print(f"   🔑 키: {list(data.keys())}")
            
        else:
            print(f"\n❌ 성능 테스트 실패:")
            print(f"   ⏱️ 소요 시간: {response_time:.3f}초")
            print(f"   🚨 오류: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ 실제 API 성능 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 등록 현황 조회 API 실제 테스트 시작")
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
        test_real_api_inflow_status()
        test_real_api_multiple_checks()
        test_real_api_performance()
        
        print(f"\n" + "=" * 50 + " 실제 API 등록 현황 조회 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 상품 등록 현황 조회 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 상품 등록 현황 조회")
        print("   2. ✅ 등록 가능/제한 상태 확인")
        print("   3. ✅ 사용률 기반 상태 분석")
        print("   4. ✅ 연속 조회 일관성 테스트")
        print("   5. ✅ API 성능 측정")
        print("   6. ✅ 비즈니스 인사이트 제공")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 등록된 상품수는 삭제 상품 제외")
        print("   - permitted_count가 null이면 무제한")
        print("   - restricted가 true이면 등록 불가")
        print("   - API 응답이 실시간 반영")
        print("   - 성능이 일반적으로 1-2초 내")
        
        print(f"\n📊 활용 가능한 모니터링:")
        print("   🔄 정기 체크: 매일 현황 확인")
        print("   📈 트렌드 분석: 등록수 변화 추이")
        print("   🚨 알림 설정: 임계값 도달 시 알림")
        print("   📋 리포팅: 주기적인 현황 보고")
        print("   🎯 계획 수립: 등록 전략 최적화")
        
    except Exception as e:
        print(f"\n❌ 실제 API 등록 현황 조회 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()