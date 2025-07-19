#!/usr/bin/env python3
"""BI 대시보드 테스트 스크립트"""

import requests
import time
import json

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("=== API 엔드포인트 테스트 ===")
    
    endpoints = [
        ("대시보드 요약", "http://localhost:8005/api/bi/dashboard/summary"),
        ("카테고리별 수익성", "http://localhost:8005/api/bi/profitability/categories"),
        ("가격 알림", "http://localhost:8005/api/bi/competitors/alerts?limit=10"),
        ("시장 트렌드", "http://localhost:8005/api/bi/trends/categories")
    ]
    
    all_success = True
    
    for name, url in endpoints:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: 성공 (데이터 수신)")
                if name == "대시보드 요약":
                    print(f"   - 전체 상품: {data.get('profitability', {}).get('total_products', 0)}")
                    print(f"   - 평균 마진: {data.get('profitability', {}).get('average_margin', 0):.1f}%")
                    print(f"   - 가격 알림: {data.get('competition', {}).get('active_alerts', 0)}")
            else:
                print(f"❌ {name}: 실패 (상태 코드: {response.status_code})")
                all_success = False
        except Exception as e:
            print(f"❌ {name}: 실패 (에러: {str(e)})")
            all_success = False
    
    return all_success

def test_frontend_page():
    """프론트엔드 페이지 접근성 테스트"""
    print("\n=== 프론트엔드 페이지 테스트 ===")
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:3000/bi/dashboard", 
                                   headers={"Accept": "text/html"})
            if response.status_code == 200:
                print(f"✅ BI 대시보드 페이지: 성공")
                # HTML 내용 확인
                if "비즈니스 인텔리전스 대시보드" in response.text:
                    print("   - 페이지 제목 확인됨")
                if "<div" in response.text and "class=" in response.text:
                    print("   - React 컴포넌트 렌더링 확인됨")
                return True
            else:
                print(f"⏳ 시도 {i+1}/{max_retries}: 상태 코드 {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"⏳ 시도 {i+1}/{max_retries}: 연결 대기 중...")
        
        if i < max_retries - 1:
            time.sleep(2)
    
    print("❌ BI 대시보드 페이지: 실패")
    return False

def main():
    print("BI 대시보드 시스템 테스트 시작...\n")
    
    # API 테스트
    api_success = test_api_endpoints()
    
    # 프론트엔드 테스트
    frontend_success = test_frontend_page()
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    if api_success and frontend_success:
        print("🎉 모든 테스트 통과! BI 대시보드가 정상적으로 작동합니다.")
        print("\n웹 브라우저에서 다음 주소로 접속하세요:")
        print("http://localhost:3000/bi/dashboard")
    else:
        print("⚠️  일부 테스트 실패. 위의 로그를 확인하세요.")
        if not api_success:
            print("   - API 서버 확인이 필요합니다.")
        if not frontend_success:
            print("   - Next.js 서버가 아직 시작 중일 수 있습니다.")

if __name__ == "__main__":
    main()