#!/usr/bin/env python3
"""
쿠팡 상품 등록 현황 조회 API 사용 예제
판매자의 상품 등록 가능 수량과 현재 등록된 상품 수를 조회합니다
"""

import os
import sys
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import ProductClient


def test_inflow_status_basic():
    """기본적인 상품 등록 현황 조회 테스트"""
    print("=" * 60 + " 기본 상품 등록 현황 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        print(f"\n📊 상품 등록 현황 조회 중...")
        print(f"   🔍 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/inflow-status")
        print(f"   📝 기능: 등록 가능한 상품수와 현재 등록된 상품수 조회")
        
        # 상품 등록 현황 조회 실행
        print(f"\n📤 상품 등록 현황 조회 요청 중...")
        result = client.get_inflow_status()
        
        if result.get("success"):
            print(f"\n✅ 상품 등록 현황 조회 성공!")
            
            # 기본 정보 표시
            vendor_id = result.get("vendor_id")
            restricted = result.get("restricted")
            registered_count = result.get("registered_count")
            permitted_count = result.get("permitted_count")
            
            print(f"\n📋 상품 등록 현황 정보:")
            print(f"   🏢 판매자 ID: {vendor_id}")
            print(f"   📦 현재 등록된 상품수: {registered_count:,}개")
            
            if permitted_count is not None:
                print(f"   🎯 등록 가능한 최대 상품수: {permitted_count:,}개")
                remaining = permitted_count - registered_count
                if remaining > 0:
                    print(f"   ✅ 추가 등록 가능한 상품수: {remaining:,}개")
                else:
                    print(f"   ⚠️ 등록 한도 도달 (추가 등록 불가)")
            else:
                print(f"   🚀 등록 가능한 최대 상품수: 제한없음")
            
            # 등록 제한 상태 표시
            if restricted:
                print(f"\n❌ 상품 생성 제한 상태:")
                print(f"   🚫 현재 새로운 상품을 등록할 수 없습니다")
                print(f"   💡 제한 해제를 위해 쿠팡 담당자에게 문의하세요")
            else:
                print(f"\n✅ 상품 생성 가능 상태:")
                print(f"   🎉 새로운 상품을 등록할 수 있습니다")
            
            # 상세 데이터 표시
            data = result.get("data", {})
            if data:
                print(f"\n📊 응답 데이터:")
                pprint(data, width=100, indent=8)
            
            # 등록 현황 분석
            print(f"\n📈 등록 현황 분석:")
            if permitted_count is not None:
                usage_rate = (registered_count / permitted_count) * 100
                print(f"   📊 사용률: {usage_rate:.1f}%")
                
                if usage_rate >= 90:
                    print(f"   🔴 경고: 등록 한도의 90% 이상 사용 중")
                elif usage_rate >= 70:
                    print(f"   🟡 주의: 등록 한도의 70% 이상 사용 중")
                else:
                    print(f"   🟢 양호: 등록 한도 여유 있음")
            else:
                print(f"   🚀 무제한: 상품 등록에 제한이 없습니다")
            
        else:
            print(f"\n❌ 상품 등록 현황 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 상품 등록 현황 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_inflow_status_analysis():
    """상품 등록 현황 분석 예제"""
    print("\n" + "=" * 60 + " 상품 등록 현황 분석 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n📈 상품 등록 현황 분석 기능")
        print(f"   📝 기능: 등록 현황을 바탕으로 상품 관리 전략 제시")
        
        # 현황 조회
        result = client.get_inflow_status()
        
        if result.get("success"):
            vendor_id = result.get("vendor_id")
            restricted = result.get("restricted")
            registered_count = result.get("registered_count")
            permitted_count = result.get("permitted_count")
            
            print(f"\n📊 {vendor_id} 판매자 분석 결과:")
            
            # 1. 등록 상태 분석
            print(f"\n1️⃣ 등록 상태 분석:")
            if restricted:
                print(f"   🚫 상품 등록 제한: 활성화")
                print(f"   💡 조치사항: 쿠팡 담당자 문의 필요")
            else:
                print(f"   ✅ 상품 등록 제한: 없음")
                print(f"   🎉 신규 상품 등록 가능")
            
            # 2. 용량 분석
            print(f"\n2️⃣ 등록 용량 분석:")
            print(f"   📦 현재 등록: {registered_count:,}개")
            
            if permitted_count is not None:
                remaining = permitted_count - registered_count
                usage_rate = (registered_count / permitted_count) * 100
                
                print(f"   🎯 등록 한도: {permitted_count:,}개")
                print(f"   ⚡ 남은 용량: {remaining:,}개")
                print(f"   📊 사용률: {usage_rate:.1f}%")
                
                # 용량별 권장사항
                if usage_rate >= 95:
                    print(f"\n🔴 긴급 상황 (사용률 95% 이상):")
                    print(f"   - 즉시 불필요한 상품 삭제 검토")
                    print(f"   - 상품 등록 한도 증량 요청 고려")
                    print(f"   - 신규 상품 등록 일시 중단")
                elif usage_rate >= 85:
                    print(f"\n🟠 주의 필요 (사용률 85% 이상):")
                    print(f"   - 상품 포트폴리오 최적화 검토")
                    print(f"   - 성과가 낮은 상품 정리")
                    print(f"   - 등록 한도 증량 사전 준비")
                elif usage_rate >= 70:
                    print(f"\n🟡 관리 권장 (사용률 70% 이상):")
                    print(f"   - 정기적인 상품 성과 모니터링")
                    print(f"   - 상품 등록 계획 수립")
                else:
                    print(f"\n🟢 여유 있음 (사용률 70% 미만):")
                    print(f"   - 적극적인 신규 상품 등록 가능")
                    print(f"   - 상품 포트폴리오 확장 기회")
            else:
                print(f"   🚀 등록 한도: 무제한")
                print(f"   💎 프리미엄 계정: 제한 없이 상품 등록 가능")
                
                print(f"\n🟢 무제한 계정 활용 방안:")
                print(f"   - 다양한 카테고리 진출")
                print(f"   - 시즌 상품 적극 활용")
                print(f"   - 테스트 상품 자유로운 등록")
            
            # 3. 권장 액션 플랜
            print(f"\n3️⃣ 권장 액션 플랜:")
            
            if not restricted and (permitted_count is None or remaining > 100):
                print(f"   📈 성장 단계:")
                print(f"      1. 트렌드 상품 발굴 및 등록")
                print(f"      2. 카테고리별 포트폴리오 균형")
                print(f"      3. 시즌/이벤트 상품 준비")
            elif not restricted and remaining > 0:
                print(f"   ⚖️ 최적화 단계:")
                print(f"      1. 성과 기반 상품 선별 등록")
                print(f"      2. ROI 높은 상품 우선순위")
                print(f"      3. 저성과 상품 정리")
            else:
                print(f"   🛡️ 관리 단계:")
                print(f"      1. 기존 상품 성과 분석")
                print(f"      2. 불필요한 상품 삭제")
                print(f"      3. 등록 한도 증량 요청")
            
        else:
            print(f"\n❌ 분석 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 상품 등록 현황 분석 오류: {e}")


def test_inflow_status_monitoring():
    """상품 등록 현황 모니터링 예제"""
    print("\n" + "=" * 60 + " 상품 등록 현황 모니터링 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n📊 상품 등록 현황 모니터링")
        print(f"   💡 용도: 정기적인 현황 체크 및 알림")
        
        # 현황 조회
        result = client.get_inflow_status()
        
        if result.get("success"):
            vendor_id = result.get("vendor_id")
            restricted = result.get("restricted")
            registered_count = result.get("registered_count")
            permitted_count = result.get("permitted_count")
            
            print(f"\n📋 모니터링 체크리스트:")
            
            # 체크 1: 등록 제한 상태
            print(f"\n✓ 등록 제한 상태 체크:")
            if restricted:
                print(f"   ❌ FAIL: 상품 등록이 제한되어 있습니다")
                print(f"   🚨 액션: 즉시 쿠팡 담당자 문의 필요")
            else:
                print(f"   ✅ PASS: 상품 등록 가능 상태")
            
            # 체크 2: 등록 용량 상태
            print(f"\n✓ 등록 용량 상태 체크:")
            if permitted_count is not None:
                usage_rate = (registered_count / permitted_count) * 100
                remaining = permitted_count - registered_count
                
                if usage_rate >= 90:
                    print(f"   ⚠️ WARN: 용량 사용률 {usage_rate:.1f}% (90% 이상)")
                    print(f"   📢 알림: 등록 한도 관리 필요")
                elif usage_rate >= 70:
                    print(f"   ⚡ INFO: 용량 사용률 {usage_rate:.1f}% (70% 이상)")
                    print(f"   💡 권장: 등록 계획 검토")
                else:
                    print(f"   ✅ PASS: 용량 사용률 {usage_rate:.1f}% (정상)")
                
                print(f"   📊 상세: {registered_count:,}/{permitted_count:,}개 (남은 용량: {remaining:,}개)")
            else:
                print(f"   🚀 UNLIMITED: 무제한 등록 가능")
                print(f"   📊 현재: {registered_count:,}개 등록됨")
            
            # 체크 3: 권장 액션
            print(f"\n✓ 권장 액션:")
            
            if restricted:
                print(f"   🚨 긴급: 등록 제한 해제 요청")
            elif permitted_count is not None:
                usage_rate = (registered_count / permitted_count) * 100
                remaining = permitted_count - registered_count
                
                if usage_rate >= 95:
                    print(f"   🔴 긴급: 상품 정리 또는 한도 증량 요청")
                elif usage_rate >= 85:
                    print(f"   🟠 주의: 등록 계획 조정 필요")
                elif remaining < 50:
                    print(f"   🟡 준비: 한도 증량 사전 검토")
                else:
                    print(f"   🟢 정상: 현재 상태 유지")
            else:
                print(f"   🚀 최적: 적극적인 상품 확장 가능")
            
            # 모니터링 결과 요약
            print(f"\n📊 모니터링 결과 요약:")
            print(f"   🏢 판매자: {vendor_id}")
            print(f"   📅 조회일시: {result.get('message', '상품 등록 현황 조회 성공')}")
            
            # 상태별 색상 표시
            if restricted:
                status_icon = "🔴"
                status_text = "제한됨"
            elif permitted_count is not None:
                usage_rate = (registered_count / permitted_count) * 100
                if usage_rate >= 90:
                    status_icon = "🟠"
                    status_text = "주의필요"
                elif usage_rate >= 70:
                    status_icon = "🟡"
                    status_text = "관리필요"
                else:
                    status_icon = "🟢"
                    status_text = "정상"
            else:
                status_icon = "🚀"
                status_text = "무제한"
            
            print(f"   {status_icon} 전체 상태: {status_text}")
            
        else:
            print(f"\n❌ 모니터링 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 상품 등록 현황 모니터링 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 등록 현황 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 현황 조회 테스트
        test_inflow_status_basic()
        
        # 현황 분석 테스트
        test_inflow_status_analysis()
        
        # 현황 모니터링 테스트
        test_inflow_status_monitoring()
        
        print(f"\n" + "=" * 50 + " 상품 등록 현황 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 등록 현황 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 등록 현황 조회")
        print("   2. ✅ 등록 용량 및 제한 상태 확인")
        print("   3. ✅ 사용률 기반 상태 분석")
        print("   4. ✅ 등록 전략 권장사항 제시")
        print("   5. ✅ 모니터링 체크리스트")
        print("   6. ✅ 액션 플랜 제공")
        
        print(f"\n💡 상품 등록 현황 조회 주요 특징:")
        print("   - 실시간 등록 상품수 확인")
        print("   - 등록 가능한 최대 상품수 조회")
        print("   - 상품 생성 제한 여부 확인")
        print("   - 삭제된 상품은 제외하고 계산")
        print("   - null 값은 무제한을 의미")
        
        print(f"\n📊 활용 방안:")
        print("   🔄 정기 모니터링: 매일/주간 현황 체크")
        print("   📈 용량 관리: 등록 한도 대비 사용률 관리")
        print("   🚨 알림 시스템: 임계값 도달 시 자동 알림")
        print("   📋 리포팅: 월간/분기별 등록 현황 보고")
        print("   🎯 전략 수립: 상품 포트폴리오 계획")
        
    except Exception as e:
        print(f"\n❌ 상품 등록 현황 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()