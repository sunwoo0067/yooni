"""
11번가 Open API 기본 클라이언트
"""
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
import time
import logging
import json

logger = logging.getLogger(__name__)

class ElevenBaseClient:
    """11번가 API 기본 클라이언트"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.11st.co.kr/rest"
        self.retry_count = 3
        self.retry_delay = 1  # seconds
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Union[Dict, str]:
        """API 요청 실행 (11번가는 GET 요청만 지원)"""
        # 기본 파라미터에 API 키 추가
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        # URL 생성
        query_string = urllib.parse.urlencode(params)
        url = f"{self.base_url}/{endpoint}?{query_string}"
        
        # 재시도 로직
        for attempt in range(self.retry_count):
            try:
                # 요청 실행
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    
                    # XML 파싱
                    return self._parse_xml_response(content)
            
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                logger.error(f"HTTP Error {e.code}: {error_body}")
                
                # 429 Too Many Requests - 재시도
                if e.code == 429 and attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                raise Exception(f"API request failed: {e.code} - {error_body}")
            
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
    
    def _parse_xml_response(self, xml_content: str) -> Dict:
        """XML 응답을 딕셔너리로 변환"""
        try:
            root = ET.fromstring(xml_content)
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            # XML이 아닌 경우 원본 반환
            return {'raw_response': xml_content}
    
    def _xml_to_dict(self, element: ET.Element) -> Union[Dict, List, str]:
        """XML 엘리먼트를 재귀적으로 딕셔너리로 변환"""
        result = {}
        
        # 속성 처리
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # 자식 요소 처리
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._xml_to_dict(child)
                
                # 같은 태그명이 여러 개인 경우 리스트로 처리
                if child.tag in child_dict:
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            
            result.update(child_dict)
        
        # 텍스트 내용 처리
        if element.text and element.text.strip():
            if children or element.attrib:
                result['text'] = element.text.strip()
            else:
                return element.text.strip()
        
        return result if result else None
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET 요청"""
        return self._make_request(endpoint, params)