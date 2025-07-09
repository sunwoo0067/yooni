# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import time
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")

def generate_hmac_authorization(method, path, query=''):
    """
    Coupang API의 HMAC 인증을 위한 Authorization 헤더를 생성합니다.
    성공 예제(hmac_auth_example.py)의 방식을 그대로 적용합니다.
    """
    # 1. 시간 값 생성 (예제와 동일하게)
    # Coupang API requires the signed-date to be in UTC (Zulu time)
    # Coupang API requires the signed-date to be in 'yymmddTHHMMSSZ' format
    datetime_str = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    
    # 2. 서명 문자열 생성 (URL 인코딩 없이)
    message = datetime_str + method.upper() + path + query
    # DEBUG
    print("[HMAC DEBUG] signed-date:", datetime_str)
    print("[HMAC DEBUG] message:", message)
    

    # 3. 서명 생성
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # 4. 최종 Authorization 헤더 문자열 생성
    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_str}, signature={signature}"
    )
    
    print("[HMAC DEBUG] signature:", signature)
    print("[HMAC DEBUG] Authorization:", authorization)
    return authorization
