#!/usr/bin/env python3
"""
공급사 상품 AI 분석 모델
- 가격 예측: 시장 동향 기반 적정 판매가 예측
- 수요 분석: 카테고리별 수요 패턴 분석
- 재고 최적화: 예상 판매량 기반 재고 제안
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupplierProductAI:
    """공급사 상품 AI 분석 클래스"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='yoonni',
            user='postgres',
            password='postgres'
        )
        
        # 모델 저장 경로
        self.model_path = {
            'price': 'models/supplier_price_predictor.pkl',
            'demand': 'models/supplier_demand_analyzer.pkl',
            'scaler': 'models/supplier_scaler.pkl',
            'encoders': 'models/supplier_encoders.pkl'
        }
        
        # 모델 초기화
        self.price_model = None
        self.demand_model = None
        self.scaler = StandardScaler()
        self.encoders = {}
        
    def prepare_training_data(self) -> pd.DataFrame:
        """학습 데이터 준비"""
        try:
            # 상품 데이터 로드
            query = """
            SELECT 
                sp.id,
                sp.supplier_id,
                s.name as supplier_name,
                sp.product_name,
                sp.category,
                sp.brand,
                sp.price,
                sp.cost_price,
                sp.stock_quantity,
                sp.weight,
                sp.status,
                sp.collected_at,
                -- 카테고리별 평균 가격
                AVG(sp.price) OVER (PARTITION BY sp.category) as category_avg_price,
                -- 브랜드별 평균 가격
                AVG(sp.price) OVER (PARTITION BY sp.brand) as brand_avg_price,
                -- 공급사별 평균 마진율
                AVG((sp.price - sp.cost_price) / NULLIF(sp.cost_price, 0)) 
                    OVER (PARTITION BY sp.supplier_id) as supplier_avg_margin
            FROM supplier_products sp
            JOIN suppliers s ON sp.supplier_id = s.id
            WHERE sp.status = 'active'
            AND sp.price > 0
            AND sp.cost_price > 0
            """
            
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"✅ {len(df)}개 상품 데이터 로드 완료")
            
            # 추가 특성 생성
            df['margin'] = (df['price'] - df['cost_price']) / df['cost_price']
            df['price_to_category_avg'] = df['price'] / df['category_avg_price']
            df['price_to_brand_avg'] = df['price'] / df['brand_avg_price']
            df['stock_value'] = df['stock_quantity'] * df['cost_price']
            
            # 시간 특성
            df['collected_hour'] = pd.to_datetime(df['collected_at']).dt.hour
            df['collected_dow'] = pd.to_datetime(df['collected_at']).dt.dayofweek
            df['collected_month'] = pd.to_datetime(df['collected_at']).dt.month
            
            # 결측값 처리
            df['category'] = df['category'].fillna('기타')
            df['brand'] = df['brand'].fillna('노브랜드')
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 준비 실패: {e}")
            return pd.DataFrame()
    
    def train_price_prediction_model(self, df: pd.DataFrame):
        """가격 예측 모델 학습"""
        try:
            logger.info("🤖 가격 예측 모델 학습 시작")
            
            # 특성 선택
            features = [
                'cost_price', 'weight', 'stock_quantity',
                'category_avg_price', 'brand_avg_price', 'supplier_avg_margin',
                'price_to_category_avg', 'price_to_brand_avg', 'stock_value',
                'collected_hour', 'collected_dow', 'collected_month'
            ]
            
            # 범주형 변수 인코딩
            categorical_cols = ['supplier_name', 'category', 'brand']
            
            for col in categorical_cols:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col])
                features.append(f'{col}_encoded')
            
            # 학습 데이터 준비
            X = df[features]
            y = df['price']
            
            # 데이터 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 스케일링
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 모델 학습 (앙상블)
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            
            # 학습
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)
            
            # 평가
            rf_score = rf_model.score(X_test_scaled, y_test)
            gb_score = gb_model.score(X_test_scaled, y_test)
            
            logger.info(f"📊 Random Forest R²: {rf_score:.3f}")
            logger.info(f"📊 Gradient Boosting R²: {gb_score:.3f}")
            
            # 더 좋은 모델 선택
            self.price_model = rf_model if rf_score > gb_score else gb_model
            
            # 특성 중요도
            feature_importance = pd.DataFrame({
                'feature': features,
                'importance': self.price_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("🎯 주요 가격 결정 요인:")
            for _, row in feature_importance.head(5).iterrows():
                logger.info(f"   - {row['feature']}: {row['importance']:.3f}")
            
            # 모델 저장
            self._save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"가격 예측 모델 학습 실패: {e}")
            return False
    
    def train_demand_analysis_model(self, df: pd.DataFrame):
        """수요 분석 모델 학습"""
        try:
            logger.info("🤖 수요 분석 모델 학습 시작")
            
            # 수요 지표 생성 (재고 회전율 기반)
            # 실제로는 판매 데이터가 필요하지만, 여기서는 시뮬레이션
            df['demand_score'] = (
                df['stock_quantity'] * df['margin'] * df['price_to_category_avg']
            ).clip(0, 100)
            
            # 가격 예측 모델과 동일한 특성 사용 (일관성 유지)
            features = [
                'cost_price', 'weight', 'stock_quantity',
                'category_avg_price', 'brand_avg_price', 'supplier_avg_margin',
                'price_to_category_avg', 'price_to_brand_avg', 'stock_value',
                'collected_hour', 'collected_dow', 'collected_month'
            ]
            
            # 범주형 변수 추가 (가격 예측과 동일)
            categorical_cols = ['supplier_name', 'category', 'brand']
            
            for col in categorical_cols:
                if col in self.encoders:
                    df[f'{col}_encoded'] = self.encoders[col].transform(df[col])
                    features.append(f'{col}_encoded')
            
            # 학습 데이터 준비
            X = df[features]
            y = df['demand_score']
            
            # 데이터 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 스케일링 (기존 스케일러 사용)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 모델 학습
            self.demand_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                n_jobs=-1
            )
            
            self.demand_model.fit(X_train_scaled, y_train)
            
            # 평가
            score = self.demand_model.score(X_test_scaled, y_test)
            logger.info(f"📊 수요 분석 모델 R²: {score:.3f}")
            
            # 카테고리별 수요 패턴 분석
            category_demand = df.groupby('category').agg({
                'demand_score': ['mean', 'std', 'count'],
                'price': 'mean',
                'margin': 'mean'
            }).round(2)
            
            logger.info("📈 카테고리별 수요 패턴:")
            for category in category_demand.head(5).index:
                demand_mean = category_demand.loc[category, ('demand_score', 'mean')]
                logger.info(f"   - {category}: 수요지수 {demand_mean:.1f}")
            
            return True
            
        except Exception as e:
            logger.error(f"수요 분석 모델 학습 실패: {e}")
            return False
    
    def predict_price(self, product_data: Dict[str, Any]) -> Dict[str, float]:
        """상품 가격 예측"""
        try:
            if self.price_model is None:
                self._load_models()
            
            # 특성 준비
            features = self._prepare_features(product_data)
            
            # 예측
            predicted_price = self.price_model.predict(features.reshape(1, -1))[0]
            
            # 마진 계산 (Decimal 타입 처리)
            cost_price = float(product_data.get('cost_price', 0))
            suggested_margin = (predicted_price - cost_price) / cost_price if cost_price > 0 else 0
            
            # 경쟁력 분석 (Decimal 타입 처리)
            current_price = float(product_data.get('price', predicted_price))
            price_competitiveness = current_price / predicted_price if predicted_price > 0 else 1
            
            result = {
                'predicted_price': round(predicted_price, -2),  # 100원 단위
                'suggested_margin': round(suggested_margin * 100, 1),  # %
                'price_competitiveness': round(price_competitiveness, 2),
                'price_adjustment': round((predicted_price - current_price) / current_price * 100, 1) if current_price > 0 else 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"가격 예측 실패: {e}")
            return {
                'predicted_price': 0,
                'suggested_margin': 0,
                'price_competitiveness': 1,
                'price_adjustment': 0
            }
    
    def analyze_demand(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """상품 수요 분석"""
        try:
            if self.demand_model is None:
                self._load_models()
            
            # 특성 준비
            features = self._prepare_features(product_data)
            
            # 수요 예측
            demand_score = self.demand_model.predict(features.reshape(1, -1))[0]
            
            # 수요 등급 분류
            if demand_score >= 80:
                demand_grade = 'A'
                demand_level = '매우 높음'
            elif demand_score >= 60:
                demand_grade = 'B'
                demand_level = '높음'
            elif demand_score >= 40:
                demand_grade = 'C'
                demand_level = '보통'
            elif demand_score >= 20:
                demand_grade = 'D'
                demand_level = '낮음'
            else:
                demand_grade = 'E'
                demand_level = '매우 낮음'
            
            # 재고 추천 (Decimal 타입 처리)
            current_stock = float(product_data.get('stock_quantity', 0))
            recommended_stock = self._calculate_recommended_stock(demand_score, product_data)
            
            result = {
                'demand_score': round(demand_score, 1),
                'demand_grade': demand_grade,
                'demand_level': demand_level,
                'recommended_stock': recommended_stock,
                'stock_adjustment': recommended_stock - current_stock,
                'reorder_point': max(10, int(recommended_stock * 0.3)),
                'category_rank': self._get_category_rank(product_data)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"수요 분석 실패: {e}")
            return {
                'demand_score': 50,
                'demand_grade': 'C',
                'demand_level': '보통',
                'recommended_stock': 100,
                'stock_adjustment': 0,
                'reorder_point': 30,
                'category_rank': 0
            }
    
    def batch_analyze_products(self, supplier_name: Optional[str] = None) -> List[Dict]:
        """배치 상품 분석"""
        try:
            logger.info(f"🔄 배치 분석 시작: {supplier_name or '전체'}")
            
            # 상품 조회
            query = """
            SELECT 
                sp.*,
                s.name as supplier_name
            FROM supplier_products sp
            JOIN suppliers s ON sp.supplier_id = s.id
            WHERE sp.status = 'active'
            """
            
            if supplier_name:
                query += f" AND s.name = '{supplier_name}'"
            
            query += " LIMIT 100"  # 테스트용 제한
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                products = cursor.fetchall()
            
            results = []
            
            for product in products:
                # 가격 예측
                price_analysis = self.predict_price(product)
                
                # 수요 분석
                demand_analysis = self.analyze_demand(product)
                
                # 종합 결과 (Decimal 타입을 float로 변환)
                result = {
                    'product_id': int(product['id']),
                    'supplier_product_id': str(product['supplier_product_id']),
                    'product_name': str(product['product_name']),
                    'category': str(product['category']) if product['category'] else '기타',
                    'current_price': float(product['price']),
                    'cost_price': float(product['cost_price']),
                    **price_analysis,
                    **demand_analysis,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                results.append(result)
                
                # DB에 저장
                self._save_analysis_result(result)
            
            logger.info(f"✅ {len(results)}개 상품 분석 완료")
            
            return results
            
        except Exception as e:
            logger.error(f"배치 분석 실패: {e}")
            return []
    
    def _prepare_features(self, product_data: Dict[str, Any]) -> np.ndarray:
        """특성 벡터 준비"""
        # 기본 특성 (Decimal 타입을 float로 변환)
        features = [
            float(product_data.get('cost_price', 0)),
            float(product_data.get('weight', 0)),
            float(product_data.get('stock_quantity', 0)),
            float(product_data.get('category_avg_price', 50000)),
            float(product_data.get('brand_avg_price', 50000)),
            float(product_data.get('supplier_avg_margin', 0.3)),
            float(product_data.get('price_to_category_avg', 1.0)),
            float(product_data.get('price_to_brand_avg', 1.0)),
            float(product_data.get('stock_value', 0)),
            datetime.now().hour,
            datetime.now().weekday(),
            datetime.now().month
        ]
        
        # 범주형 변수 인코딩
        for col in ['supplier_name', 'category', 'brand']:
            if col in self.encoders and col in product_data:
                try:
                    encoded = self.encoders[col].transform([product_data[col]])[0]
                except:
                    encoded = 0
                features.append(encoded)
            else:
                features.append(0)
        
        return self.scaler.transform([features])[0]
    
    def _calculate_recommended_stock(self, demand_score: float, 
                                   product_data: Dict[str, Any]) -> int:
        """추천 재고량 계산"""
        # 기본 재고 = 수요점수 * 가중치
        base_stock = demand_score * 2
        
        # 가격대별 조정 (Decimal 타입 처리)
        price = float(product_data.get('price', 0))
        if price > 100000:
            base_stock *= 0.5  # 고가 상품은 재고 축소
        elif price < 10000:
            base_stock *= 1.5  # 저가 상품은 재고 확대
        
        # 무게별 조정 (Decimal 타입 처리)
        weight = float(product_data.get('weight', 0))
        if weight > 10:
            base_stock *= 0.7  # 무거운 상품은 재고 축소
        
        return max(10, int(base_stock))
    
    def _get_category_rank(self, product_data: Dict[str, Any]) -> int:
        """카테고리 내 순위 계산"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) + 1 as rank
                    FROM supplier_products
                    WHERE category = %s
                    AND price < %s
                    AND status = 'active'
                """, (product_data.get('category'), product_data.get('price')))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except:
            return 0
    
    def _save_analysis_result(self, result: Dict[str, Any]):
        """분석 결과 저장"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO supplier_product_analysis 
                    (product_id, analysis_type, analysis_result, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_id, analysis_type) 
                    DO UPDATE SET 
                        analysis_result = EXCLUDED.analysis_result,
                        updated_at = NOW()
                """, (
                    result['product_id'],
                    'price_demand',
                    json.dumps(result),
                    datetime.now()
                ))
                
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {e}")
            self.conn.rollback()
    
    def _save_models(self):
        """모델 저장"""
        import os
        
        # 디렉토리 생성
        os.makedirs('models', exist_ok=True)
        
        # 모델 저장
        if self.price_model:
            joblib.dump(self.price_model, self.model_path['price'])
        if self.demand_model:
            joblib.dump(self.demand_model, self.model_path['demand'])
        
        joblib.dump(self.scaler, self.model_path['scaler'])
        joblib.dump(self.encoders, self.model_path['encoders'])
        
        logger.info("✅ 모델 저장 완료")
    
    def _load_models(self):
        """모델 로드"""
        try:
            import os
            
            if os.path.exists(self.model_path['price']):
                self.price_model = joblib.load(self.model_path['price'])
                self.demand_model = joblib.load(self.model_path['demand'])
                self.scaler = joblib.load(self.model_path['scaler'])
                self.encoders = joblib.load(self.model_path['encoders'])
                logger.info("✅ 모델 로드 완료")
            else:
                logger.warning("⚠️ 저장된 모델이 없습니다. 학습이 필요합니다.")
                
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")

def main():
    """메인 실행 함수"""
    ai = SupplierProductAI()
    
    # 데이터 준비
    df = ai.prepare_training_data()
    
    if not df.empty:
        # 모델 학습
        ai.train_price_prediction_model(df)
        ai.train_demand_analysis_model(df)
        
        # 배치 분석 실행
        results = ai.batch_analyze_products('오너클랜')
        
        # 결과 출력
        for result in results[:5]:
            print(f"\n📦 {result['product_name']}")
            print(f"   현재가: {result['current_price']:,}원")
            print(f"   예측가: {result['predicted_price']:,}원")
            print(f"   수요등급: {result['demand_grade']} ({result['demand_level']})")
            print(f"   재고추천: {result['recommended_stock']}개")

if __name__ == "__main__":
    main()