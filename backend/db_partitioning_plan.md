# 상품 테이블 파티셔닝 계획

## 현재 상태 분석
- **테이블 크기**: 169 MB (테이블: 83 MB, 인덱스: 49 MB)
- **총 레코드 수**: 135,281개
- **일일 증가율 예상**: 약 371개/일

## 데이터 분포
### 공급업체별 분포
- 도매매: 89,335개 (66.04%)
- 오너클랜: 42,410개 (31.35%)
- 젠트레이드: 3,536개 (2.61%)

### 상태별 분포
- active: 125,359개 (92.67%)
- available: 6,325개 (4.68%)
- inactive: 3,531개 (2.61%)
- soldout: 66개 (0.05%)

## 파티셔닝 권장사항

### 현재 (135,281개 레코드)
**권장사항**: 파티셔닝 불필요
- 현재 데이터 크기로는 파티셔닝의 이점이 크지 않음
- 인덱스 최적화로 충분한 성능 확보 가능

### 향후 계획
**100만 건 도달 시 (예상: 약 2년 후)**
1. **리스트 파티셔닝 (supplier_id 기준)**
   ```sql
   CREATE TABLE products_partitioned (
       LIKE products INCLUDING ALL
   ) PARTITION BY LIST (supplier_id);
   
   CREATE TABLE products_domemae PARTITION OF products_partitioned FOR VALUES IN (3);
   CREATE TABLE products_ownerclan PARTITION OF products_partitioned FOR VALUES IN (1);
   CREATE TABLE products_zentrade PARTITION OF products_partitioned FOR VALUES IN (2);
   ```

2. **파티셔닝 시 이점**
   - 공급업체별 독립적인 데이터 관리
   - 병렬 쿼리 성능 향상
   - 공급업체별 유지보수 용이

### 모니터링 지표
```sql
-- 월별 데이터 증가 추이 모니터링
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as new_products,
    pg_size_pretty(pg_total_relation_size('products')) as table_size
FROM products
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;
```

## 즉시 실행 가능한 최적화
1. **VACUUM ANALYZE 정기 실행**
   ```sql
   VACUUM ANALYZE products;
   ```

2. **통계 업데이트**
   ```sql
   ANALYZE products;
   ```

3. **불필요한 인덱스 정리**
   - 현재 인덱스는 모두 적절히 사용되고 있음

## 결론
- **현재**: 파티셔닝 불필요, 기존 구조 유지
- **100만 건 도달 시**: supplier_id 기준 LIST 파티셔닝 구현
- **정기 모니터링**: 월별 데이터 증가율 확인