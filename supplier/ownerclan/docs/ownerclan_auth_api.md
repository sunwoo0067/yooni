# Ownerclan 인증 API 문서

본 문서는 판매사 계정으로 **Ownerclan** 인증 토큰(JWT)을 발급받는 방법을 설명합니다.

## 1. 엔드포인트
| 환경 | URL |
|-------|------------------------------------------------------|
| Production | `https://auth.ownerclan.com/auth` |

> 현재 서비스는 **프로덕션** 엔드포인트만 사용합니다. 샌드박스는 지원되지 않습니다.

## 2. HTTP 메서드
`POST`

## 3. 요청 헤더
| 헤더 | 값 |
|-------|---------------------------|
| `Content-Type` | `application/json` |

## 4. 요청 바디(JSON)
| 필드 | 타입 | 설명 | 필수 |
|-------|--------|-----------------------|------|
| `service` | string | 고정 값: `"ownerclan"` | ✅ |
| `userType` | string | 사용자 유형. 일반적으로 `"seller"` | ✅ |
| `username` | string | 판매사 ID | ✅ |
| `password` | string | 판매사 비밀번호 | ✅ |

### 예시
```json
{
  "service": "ownerclan",
  "userType": "seller",
  "username": "b00679540",
  "password": "***********"
}
```

## 5. 응답
Ownerclan API는 두 가지 형식 중 하나로 JWT를 반환합니다.

1. **RAW**: 본문에 JWT 문자열만 존재하며, `Content-Type: text/html; charset=utf-8`
2. **JSON**: `{ "accessToken": "<JWT>", "tokenType": "Bearer", "expiresIn": 2592000 }`

### 예시 (RAW)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 예시 (JSON)
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "Bearer",
  "expiresIn": 2592000
}
```

## 6. 파이썬 예제 코드
다음 예제는 프로젝트에 포함된 헬퍼 함수 `get_ownerclan_token` 을 사용하여 토큰을 발급받는 방법을 보여줍니다.

```python
from market.ownerclan.utils.auth import get_ownerclan_token

# .env 또는 OS 환경변수에 자격 증명을 설정했다면 인자 없이 호출 가능
# token = get_ownerclan_token()

# 직접 아이디/비밀번호를 넘겨 호출
token = get_ownerclan_token("b00679540", "ehdgod1101*")
print(token)  # JWT 출력
```

## 7. 환경변수 설정(선택)
비밀번호를 코드에 직접 입력하지 않기 위해 다음 환경변수를 사용할 수 있습니다.

| 변수명 | 설명 |
|-------------|---------------------------|
| `OWNERCLAN_USERNAME` | 판매사 ID |
| `OWNERCLAN_PASSWORD` | 판매사 비밀번호 |

`.env` 예시:
```
OWNERCLAN_USERNAME=b00679540
OWNERCLAN_PASSWORD=ehdgod1101*
```

## 8. 오류 코드
| HTTP 상태 | 설명 |
|-----------|----------------------------|
| `401` | 인증 실패 (아이디/비밀번호 오류) |
| `429` | 요청 한도 초과 |
| `5xx` | 서버 오류 |

## 9. 보안 주의사항
- **JWT** 는 민감 정보입니다. Git 등에 노출되지 않도록 주의하세요.
- 네트워크 통신 시 HTTPS를 사용하여 암호화된 채널을 유지합니다.
