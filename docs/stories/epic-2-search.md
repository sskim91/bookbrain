# Epic 2: Hybrid Search Engine

> **Role**: Scrum Master
> **Created**: 2025-12-04
> **Epic Owner**: Developer
> **Priority**: P0 (Must Have)

---

## Epic Overview

### Goal
벡터 유사도 검색과 BM25 키워드 검색을 결합한 하이브리드 검색 엔진 구축

### Success Criteria
- [ ] 벡터 검색 단독 동작
- [ ] BM25 검색 단독 동작
- [ ] 하이브리드 검색 (RRF) 동작
- [ ] 검색 응답 시간 < 2초
- [ ] 검색 결과에 출처 정보 포함

### Dependencies
- Epic 1 완료 (데이터 적재)

---

## Stories

### Story 2.1: 벡터 검색 구현

**As a** User
**I want** 자연어 질의로 의미적으로 유사한 내용을 검색
**So that** 정확한 키워드를 몰라도 찾을 수 있다

#### Acceptance Criteria
```gherkin
Given 쿼리 문자열 "elasticsearch 매핑 설정"
When VectorSearcher.search() 호출
Then 의미적으로 유사한 청크가 반환된다
And 유사도 점수가 포함된다
And 메타데이터(책명, 페이지)가 포함된다
And top_k 개수만큼 반환된다
```

#### Tasks
- [ ] `VectorSearcher` 클래스 구현
- [ ] 쿼리 임베딩 생성
- [ ] Chroma 유사도 검색 호출
- [ ] `SearchResult` 모델 정의
- [ ] 유닛 테스트 작성

#### Definition of Done
- 테스트 쿼리로 관련 결과 반환 확인
- 응답 시간 < 500ms

---

### Story 2.2: BM25 검색 구현

**As a** User
**I want** 특정 키워드가 포함된 내용을 정확히 검색
**So that** 고유명사나 기술 용어를 정확히 찾을 수 있다

#### Acceptance Criteria
```gherkin
Given 쿼리 문자열 "BM25Okapi"
When BM25Searcher.search() 호출
Then 해당 키워드를 포함한 청크가 반환된다
And BM25 점수가 포함된다
And 메타데이터가 포함된다
```

#### Tasks
- [ ] `BM25Searcher` 클래스 구현
- [ ] 쿼리 토크나이징
- [ ] BM25 스코어링
- [ ] 청크 ID → 메타데이터 매핑
- [ ] 유닛 테스트 작성

#### Definition of Done
- 키워드 포함 결과 반환 확인
- 응답 시간 < 200ms

---

### Story 2.3: 하이브리드 검색 (RRF) 구현

**As a** User
**I want** 벡터와 키워드 검색을 결합한 결과를 받기
**So that** 정확도와 재현율 모두 높은 검색을 할 수 있다

#### Acceptance Criteria
```gherkin
Given 쿼리 문자열 "Spring Security OAuth2 설정"
When HybridSearcher.search(mode=HYBRID) 호출
Then 벡터와 BM25 결과가 RRF로 결합된다
And 통합 점수로 정렬된다
And 개별 점수(vector, bm25)도 확인 가능하다
```

#### Tasks
- [ ] `HybridSearcher` 클래스 구현
- [ ] RRF (Reciprocal Rank Fusion) 알고리즘 구현
- [ ] 검색 모드 지원 (vector/keyword/hybrid)
- [ ] 결과 중복 제거
- [ ] 유닛 테스트 작성

#### RRF Algorithm
```python
def rrf_fusion(
    vector_results: List[SearchResult],
    bm25_results: List[SearchResult],
    k: int = 60
) -> List[SearchResult]:
    """
    Reciprocal Rank Fusion
    score(d) = Σ 1 / (k + rank(d))
    """
    scores = {}

    for rank, result in enumerate(vector_results):
        doc_id = result.id
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    for rank, result in enumerate(bm25_results):
        doc_id = result.id
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # Sort by combined score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [get_result_by_id(id) for id in sorted_ids]
```

#### Definition of Done
- 하이브리드 결과가 단독 결과보다 나은 케이스 확인
- 모드 전환 동작 확인

---

### Story 2.4: 검색 결과 모델 정의

**As a** Developer
**I want** 일관된 검색 결과 데이터 구조
**So that** UI와 API에서 쉽게 사용할 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 결과
When 결과 객체 접근
Then 텍스트, 점수, 메타데이터에 접근 가능하다
And JSON 직렬화가 가능하다
And 출처 정보가 포맷팅된다
```

#### Tasks
- [ ] `SearchResult` Pydantic 모델 정의
- [ ] `SearchResponse` 모델 정의
- [ ] 출처 포맷터 구현
- [ ] JSON 직렬화 테스트

#### Models
```python
from pydantic import BaseModel
from typing import Optional, List

class ChunkMetadata(BaseModel):
    book_title: str
    book_file: str
    chapter: Optional[str]
    page_start: int
    page_end: int
    chunk_index: int

class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    score_vector: Optional[float] = None
    score_bm25: Optional[float] = None
    metadata: ChunkMetadata

    @property
    def source(self) -> str:
        """출처 포맷팅"""
        chapter = f", {self.metadata.chapter}" if self.metadata.chapter else ""
        return f"{self.metadata.book_title}{chapter}, p.{self.metadata.page_start}"

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    mode: str  # "vector" | "keyword" | "hybrid"
```

#### Definition of Done
- 모델 정의 완료
- 직렬화/역직렬화 테스트 통과

---

### Story 2.5: 검색어 하이라이트 구현

**As a** User
**I want** 검색 결과에서 검색어가 강조 표시되길
**So that** 관련 부분을 빠르게 찾을 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 결과 텍스트와 쿼리
When highlight_text() 호출
Then 검색어가 <mark> 태그로 감싸진다
And 대소문자 구분 없이 하이라이트된다
And HTML 이스케이프가 적용된다
```

#### Tasks
- [ ] `highlight_text()` 함수 구현
- [ ] 쿼리 토큰 분리
- [ ] 정규식 기반 하이라이트
- [ ] HTML 이스케이프 처리
- [ ] 유닛 테스트 작성

#### Implementation
```python
import re
import html

def highlight_text(text: str, query: str) -> str:
    """검색어 하이라이트"""
    # HTML 이스케이프
    escaped = html.escape(text)

    # 쿼리 토큰 분리
    tokens = query.lower().split()

    # 각 토큰 하이라이트
    for token in tokens:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f"<mark>{m.group()}</mark>",
            escaped
        )

    return escaped
```

#### Definition of Done
- 검색어 하이라이트 동작 확인
- XSS 방지 (HTML 이스케이프) 확인

---

### Story 2.6: 검색 필터 구현

**As a** User
**I want** 특정 책에서만 검색
**So that** 원하는 범위로 결과를 좁힐 수 있다

#### Acceptance Criteria
```gherkin
Given 쿼리와 책 필터 ["Elasticsearch 가이드", "검색엔진 구축"]
When search(book_filter=[...]) 호출
Then 해당 책에서만 검색된다
And 다른 책 결과는 제외된다
```

#### Tasks
- [ ] Chroma 메타데이터 필터 적용
- [ ] BM25 필터 로직 추가
- [ ] `SearchRequest` 모델에 필터 추가
- [ ] 유닛 테스트 작성

#### Implementation
```python
# Chroma where 필터
results = collection.query(
    query_embeddings=[embedding],
    n_results=top_k,
    where={"book_title": {"$in": book_filter}}  # 필터 적용
)
```

#### Definition of Done
- 책 필터 동작 확인
- 빈 필터 시 전체 검색 확인

---

### Story 2.7: 검색 CLI 도구 구현

**As a** Developer
**I want** CLI에서 검색을 테스트
**So that** UI 없이도 검색 기능을 확인할 수 있다

#### Acceptance Criteria
```gherkin
Given CLI 도구
When python scripts/search_cli.py "elasticsearch 매핑" 실행
Then 검색 결과가 터미널에 출력된다
And 모드 선택 옵션이 동작한다
```

#### Tasks
- [ ] `scripts/search_cli.py` 작성
- [ ] argparse로 옵션 파싱
- [ ] 결과 포맷팅 출력
- [ ] 인터랙티브 모드 (선택)

#### CLI Interface
```bash
# 기본 검색 (하이브리드)
python scripts/search_cli.py "elasticsearch 매핑"

# 벡터 검색만
python scripts/search_cli.py "elasticsearch 매핑" --mode vector

# 결과 개수 지정
python scripts/search_cli.py "elasticsearch 매핑" --top-k 5

# 책 필터
python scripts/search_cli.py "매핑" --book "Elasticsearch 가이드"

# 인터랙티브 모드
python scripts/search_cli.py --interactive
```

#### Definition of Done
- CLI 검색 동작 확인
- 모든 옵션 동작 확인

---

## Sprint Planning Suggestion

### Sprint 4 (Core Search)
- Story 2.1: 벡터 검색
- Story 2.2: BM25 검색
- Story 2.4: 검색 결과 모델

### Sprint 5 (Hybrid & Enhancement)
- Story 2.3: 하이브리드 검색 (RRF)
- Story 2.5: 검색어 하이라이트
- Story 2.6: 검색 필터
- Story 2.7: 검색 CLI

---

## Technical Considerations

### Performance Optimization
- 쿼리 임베딩 캐싱 고려 (동일 쿼리 재검색)
- BM25 인덱스 메모리 로딩 최적화
- Chroma 인덱스 설정 (HNSW 파라미터)

### Quality Metrics
```
검색 품질 평가 (수동 테스트)
├── Precision@5: 상위 5개 중 관련 결과 비율
├── MRR: 첫 번째 관련 결과의 역순위
└── 사용자 만족도: 원하는 정보를 찾았는가
```

