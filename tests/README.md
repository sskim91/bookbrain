# BookBrain Test Suite

이 문서는 BookBrain 프로젝트의 테스트 프레임워크 구성을 설명합니다.

## 테스트 구조

```
bookbrain/
├── tests/                          # E2E 테스트 (Playwright)
│   ├── e2e/                        # E2E 테스트 파일
│   │   └── health.spec.ts
│   └── support/                    # 테스트 인프라
│       ├── fixtures/               # 테스트 fixtures
│       └── helpers/                # 유틸리티 함수
├── bookbrain-backend/
│   └── tests/                      # Backend 단위 테스트 (pytest)
│       ├── conftest.py
│       └── test_health.py
└── bookbrain-frontend/
    └── tests/                      # Frontend 단위 테스트 (Vitest)
        ├── setup.ts
        └── components/
            └── Button.test.tsx
```

## 테스트 도구

| 계층 | 도구 | 설명 |
|------|------|------|
| Backend Unit | pytest + respx | FastAPI 엔드포인트, 서비스 로직 테스트 |
| Frontend Unit | Vitest + Testing Library | React 컴포넌트, 훅 테스트 |
| E2E | Playwright | 전체 사용자 흐름 테스트 |

## 테스트 실행

### Backend 테스트

```bash
cd bookbrain-backend
uv run pytest              # 모든 테스트 실행
uv run pytest -v           # 상세 출력
uv run pytest --cov        # 커버리지 포함
```

### Frontend 테스트

```bash
cd bookbrain-frontend
npm run test               # Watch 모드
npm run test:run           # 단일 실행
npm run test:coverage      # 커버리지 포함
```

### E2E 테스트

```bash
# 프로젝트 루트에서
npm run test:e2e           # 모든 E2E 테스트 실행
npm run test:e2e:ui        # Playwright UI 모드
npm run test:e2e:headed    # 브라우저 표시
npm run test:e2e:report    # HTML 리포트 보기
```

## 환경 설정

1. `.env.example`을 `.env`로 복사
2. 환경 변수 설정:
   - `BASE_URL`: Frontend URL (기본: http://localhost:5173)
   - `API_URL`: Backend URL (기본: http://localhost:8000)

## 테스트 작성 가이드

### Selector 전략

- UI 요소에 `data-testid` 속성 사용
- 예: `<button data-testid="submit-btn">Submit</button>`

### 테스트 격리

- 각 테스트는 독립적으로 실행 가능해야 함
- 테스트 데이터는 테스트 내에서 생성하고 정리

### Failure Artifacts

Playwright 설정:
- 스크린샷: 실패 시에만 캡처
- 비디오: 실패 시에만 보존
- Trace: 실패 시에만 보존

## CI/CD

GitHub Actions에서 자동 실행:
- PR 생성 시 모든 테스트 실행
- 테스트 결과 리포트 생성

---

*Last Updated: 2025-12-23*
