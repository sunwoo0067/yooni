#!/usr/bin/env python3
"""
쿠팡 카테고리 Excel 파일 파서
Excel 파일에서 카테고리 데이터를 추출하여 구조화된 데이터로 변환
"""

import os
import re
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class CoupangExcelCategoryParser:
    """쿠팡 카테고리 Excel 파일 파서"""
    
    def __init__(self, excel_folder_path: str):
        """
        파서 초기화
        
        Args:
            excel_folder_path: Excel 파일들이 있는 폴더 경로
        """
        self.excel_folder = Path(excel_folder_path)
        self.categories_data = {}
        self.stats = {
            "total_files": 0,
            "total_categories": 0,
            "files_processed": [],
            "errors": []
        }
    
    def parse_all_excel_files(self) -> Dict[str, Any]:
        """
        모든 Excel 파일을 파싱하여 카테고리 데이터 추출
        
        Returns:
            Dict[str, Any]: 전체 카테고리 데이터
        """
        print("🚀 쿠팡 카테고리 Excel 파일 파싱 시작")
        
        excel_files = list(self.excel_folder.glob("*.xlsx"))
        self.stats["total_files"] = len(excel_files)
        
        print(f"📁 발견된 Excel 파일: {len(excel_files)}개")
        
        for excel_file in excel_files:
            try:
                print(f"\n📄 처리 중: {excel_file.name}")
                file_data = self.parse_excel_file(excel_file)
                
                if file_data:
                    self.categories_data.update(file_data)
                    self.stats["files_processed"].append(excel_file.name)
                    print(f"   ✅ {len(file_data)}개 카테고리 추출 완료")
                else:
                    print(f"   ⚠️ 데이터 없음")
                    
            except Exception as e:
                error_msg = f"{excel_file.name}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"   ❌ 오류: {e}")
        
        self.stats["total_categories"] = len(self.categories_data)
        
        print(f"\n🏁 파싱 완료")
        print(f"   📊 총 카테고리: {self.stats['total_categories']}개")
        print(f"   ✅ 성공한 파일: {len(self.stats['files_processed'])}개")
        print(f"   ❌ 실패한 파일: {len(self.stats['errors'])}개")
        
        return self.categories_data
    
    def parse_excel_file(self, file_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        개별 Excel 파일 파싱
        
        Args:
            file_path: Excel 파일 경로
            
        Returns:
            Dict[str, Dict[str, Any]]: 카테고리 데이터 딕셔너리
        """
        try:
            # Excel 파일 읽기 (헤더 4행 스킵)
            df = pd.read_excel(file_path, skiprows=4)
            
            # 컬럼명이 없는 경우 대체
            if df.empty or df.columns[0] is None:
                return {}
            
            # 카테고리 데이터 추출
            categories = {}
            
            for idx, row in df.iterrows():
                try:
                    category_info = self._parse_category_row(row, file_path.stem)
                    if category_info and category_info.get('id'):
                        categories[category_info['id']] = category_info
                except Exception as e:
                    # 개별 행 파싱 오류는 로그만 남기고 계속 진행
                    continue
            
            return categories
            
        except Exception as e:
            print(f"   Excel 파일 읽기 오류: {e}")
            return {}
    
    def _parse_category_row(self, row: pd.Series, file_category: str) -> Optional[Dict[str, Any]]:
        """
        Excel 행에서 카테고리 정보 추출
        
        Args:
            row: 파싱할 DataFrame 행
            file_category: 파일 카테고리명
            
        Returns:
            Optional[Dict[str, Any]]: 카테고리 정보 또는 None
        """
        try:
            # 첫 번째 컬럼에서 카테고리 정보 추출
            category_cell = str(row.iloc[0]) if len(row) > 0 else ""
            
            if pd.isna(category_cell) or category_cell.strip() == "" or category_cell == "nan":
                return None
            
            # 카테고리 ID와 경로 파싱
            category_id, category_path = self._extract_category_info(category_cell)
            
            if not category_id:
                return None
            
            # 수수료율 추출
            commission_rate = self._extract_commission_rate(row)
            
            # 구매 옵션 추출 (컬럼 2-9)
            purchase_options = self._extract_purchase_options(row)
            
            # 검색 옵션 추출 (컬럼 10-149)
            search_options = self._extract_search_options(row)
            
            # 고시정보 추출 (컬럼 150+)
            notice_info = self._extract_notice_info(row)
            
            # 카테고리 정보 구성
            category_info = {
                "id": category_id,
                "path": category_path,
                "file_category": file_category,
                "commission_rate": commission_rate,
                "purchase_options": purchase_options,
                "search_options": search_options,
                "notice_info": notice_info,
                "level": len(category_path.split(">")) if category_path else 0,
                "parent_path": ">".join(category_path.split(">")[:-1]) if category_path and ">" in category_path else ""
            }
            
            return category_info
            
        except Exception as e:
            return None
    
    def _extract_category_info(self, category_cell: str) -> Tuple[Optional[str], Optional[str]]:
        """
        카테고리 셀에서 ID와 경로 추출
        
        Args:
            category_cell: 카테고리 셀 내용
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (카테고리 ID, 카테고리 경로)
        """
        try:
            # [카테고리ID] 경로 형식 파싱
            pattern = r'\[(\d+)\]\s*(.+)'
            match = re.match(pattern, category_cell.strip())
            
            if match:
                category_id = match.group(1)
                category_path = match.group(2).strip()
                return category_id, category_path
            
            return None, None
            
        except Exception:
            return None, None
    
    def _extract_commission_rate(self, row: pd.Series) -> Optional[float]:
        """
        수수료율 추출
        
        Args:
            row: DataFrame 행
            
        Returns:
            Optional[float]: 수수료율 (%)
        """
        try:
            if len(row) > 1:
                commission_cell = str(row.iloc[1])
                if commission_cell and commission_cell != "nan":
                    # 숫자 추출
                    numbers = re.findall(r'\d+\.?\d*', commission_cell)
                    if numbers:
                        return float(numbers[0])
            return None
            
        except Exception:
            return None
    
    def _extract_purchase_options(self, row: pd.Series) -> List[Dict[str, Any]]:
        """
        구매 옵션 추출 (컬럼 2-9)
        
        Args:
            row: DataFrame 행
            
        Returns:
            List[Dict[str, Any]]: 구매 옵션 리스트
        """
        purchase_options = []
        
        try:
            # 구매 옵션은 컬럼 2-9 (옵션유형1-4, 옵션값1-4)
            for i in range(4):  # 4개의 옵션 유형
                type_col = 2 + i * 2      # 옵션유형 컬럼
                value_col = 2 + i * 2 + 1 # 옵션값 컬럼
                
                if len(row) > value_col:
                    option_type = str(row.iloc[type_col]) if pd.notna(row.iloc[type_col]) else ""
                    option_values = str(row.iloc[value_col]) if pd.notna(row.iloc[value_col]) else ""
                    
                    if option_type and option_type != "nan" and option_values and option_values != "nan":
                        # 옵션값들을 파싱 (/ 또는 , 구분자)
                        values_list = [v.strip() for v in re.split(r'[/,]', option_values) if v.strip()]
                        
                        purchase_options.append({
                            "type": option_type.strip(),
                            "values": values_list,
                            "is_required": True  # 구매 옵션은 기본적으로 필수
                        })
        
        except Exception:
            pass
        
        return purchase_options
    
    def _extract_search_options(self, row: pd.Series) -> List[Dict[str, Any]]:
        """
        검색 옵션 추출 (컬럼 10-149)
        
        Args:
            row: DataFrame 행
            
        Returns:
            List[Dict[str, Any]]: 검색 옵션 리스트
        """
        search_options = []
        
        try:
            # 검색 옵션은 컬럼 10부터 (옵션유형1-70, 옵션값1-70)
            start_col = 10
            max_options = 70
            
            for i in range(max_options):
                type_col = start_col + i * 2     # 옵션유형 컬럼
                value_col = start_col + i * 2 + 1 # 옵션값 컬럼
                
                if len(row) > value_col:
                    option_type = str(row.iloc[type_col]) if pd.notna(row.iloc[type_col]) else ""
                    option_values = str(row.iloc[value_col]) if pd.notna(row.iloc[value_col]) else ""
                    
                    if option_type and option_type != "nan" and option_values and option_values != "nan":
                        # 옵션값들을 파싱
                        values_list = [v.strip() for v in re.split(r'[/,]', option_values) if v.strip()]
                        
                        search_options.append({
                            "type": option_type.strip(),
                            "values": values_list,
                            "is_required": False  # 검색 옵션은 선택적
                        })
        
        except Exception:
            pass
        
        return search_options
    
    def _extract_notice_info(self, row: pd.Series) -> Dict[str, Any]:
        """
        고시정보 추출 (컬럼 150+)
        
        Args:
            row: DataFrame 행
            
        Returns:
            Dict[str, Any]: 고시정보
        """
        notice_info = {}
        
        try:
            # 고시정보는 보통 컬럼 150 이후
            start_col = 150
            
            if len(row) > start_col:
                notice_category = str(row.iloc[start_col]) if pd.notna(row.iloc[start_col]) else ""
                
                if notice_category and notice_category != "nan":
                    notice_info["category"] = notice_category.strip()
                    
                    # 고시정보값들 추출
                    notice_values = []
                    for i in range(1, 15):  # 고시정보값1-14
                        val_col = start_col + i
                        if len(row) > val_col:
                            value = str(row.iloc[val_col]) if pd.notna(row.iloc[val_col]) else ""
                            if value and value != "nan":
                                notice_values.append(value.strip())
                    
                    notice_info["required_fields"] = notice_values
        
        except Exception:
            pass
        
        return notice_info
    
    def save_to_json(self, output_path: str) -> None:
        """
        파싱된 데이터를 JSON 파일로 저장
        
        Args:
            output_path: 저장할 JSON 파일 경로
        """
        try:
            output_data = {
                "metadata": {
                    "total_categories": len(self.categories_data),
                    "files_processed": self.stats["files_processed"],
                    "parsing_errors": self.stats["errors"],
                    "generated_at": pd.Timestamp.now().isoformat()
                },
                "categories": self.categories_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 데이터 저장 완료: {output_path}")
            print(f"   📊 총 {len(self.categories_data)}개 카테고리")
            
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        파싱 통계 정보 반환
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        # 파일별 카테고리 수
        file_categories = {}
        for category in self.categories_data.values():
            file_cat = category.get('file_category', 'unknown')
            file_categories[file_cat] = file_categories.get(file_cat, 0) + 1
        
        # 레벨별 카테고리 수
        level_counts = {}
        for category in self.categories_data.values():
            level = category.get('level', 0)
            level_counts[f"level_{level}"] = level_counts.get(f"level_{level}", 0) + 1
        
        return {
            "총_카테고리_수": len(self.categories_data),
            "파일별_카테고리_수": file_categories,
            "레벨별_카테고리_수": level_counts,
            "처리된_파일": self.stats["files_processed"],
            "오류_파일": self.stats["errors"]
        }


def main():
    """메인 실행 함수"""
    excel_folder = "/home/sunwoo/project/yooni_02/market/coupang/category/Coupang_Category_20250712_1390"
    output_file = "/home/sunwoo/project/yooni_02/market/coupang/category/coupang_categories_data.json"
    
    # 파서 초기화 및 실행
    parser = CoupangExcelCategoryParser(excel_folder)
    categories_data = parser.parse_all_excel_files()
    
    # JSON 파일로 저장
    parser.save_to_json(output_file)
    
    # 통계 출력
    stats = parser.get_statistics()
    print(f"\n📈 파싱 통계:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     - {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()