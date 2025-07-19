-- PostgreSQL 인증 문제 해결
-- 비밀번호를 MD5로 재설정
ALTER USER postgres WITH PASSWORD '1234';

-- 테스트용 사용자 생성
CREATE USER yooni WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE yoonni TO yooni;

-- 권한 확인
\du