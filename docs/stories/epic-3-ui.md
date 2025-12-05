# Epic 3: Streamlit Search UI

> **Role**: Scrum Master
> **Created**: 2025-12-04
> **Epic Owner**: Developer
> **Priority**: P0 (Must Have)

---

## Epic Overview

### Goal
Streamlit 기반의 웹 검색 UI 구축으로 브라우저에서 장서 검색 가능

### Success Criteria
- [ ] 검색창에서 쿼리 입력 및 검색
- [ ] 검색 결과 카드 형태로 표시
- [ ] 출처(책명, 페이지) 명확히 표시
- [ ] 검색 모드 전환 가능
- [ ] 반응형 레이아웃

### Dependencies
- Epic 2 완료 (검색 엔진)

---

## Stories

### Story 3.1: Streamlit 앱 기본 구조

**As a** Developer
**I want** Streamlit 앱의 기본 구조 설정
**So that** UI 컴포넌트를 추가할 수 있다

#### Acceptance Criteria
```gherkin
Given Streamlit 앱 파일
When streamlit run src/ui/app.py 실행
Then 브라우저에서 앱이 열린다
And 페이지 제목과 아이콘이 표시된다
And 기본 레이아웃이 렌더링된다
```

#### Tasks
- [ ] `src/ui/app.py` 생성
- [ ] `st.set_page_config()` 설정
- [ ] 기본 레이아웃 구성
- [ ] Session state 초기화
- [ ] 검색 서비스 초기화 (캐싱)

#### Implementation
```python
# src/ui/app.py
import streamlit as st
from bookbrain.search.hybrid import HybridSearcher

st.set_page_config(
    page_title="BookBrain",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_searcher():
    return HybridSearcher()

def main():
    st.title("📚 BookBrain")
    st.caption("개인 장서 시맨틱 검색")

    searcher = get_searcher()

    # ... UI components

if __name__ == "__main__":
    main()
```

#### Definition of Done
- 앱 실행 및 기본 화면 표시
- Hot reload 동작 확인

---

### Story 3.2: 검색창 컴포넌트

**As a** User
**I want** 검색어를 입력하고 검색 실행
**So that** 원하는 내용을 찾을 수 있다

#### Acceptance Criteria
```gherkin
Given 검색창
When 검색어 입력 후 Enter 또는 버튼 클릭
Then 검색이 실행된다
And 로딩 상태가 표시된다
And 검색어가 유지된다
```

#### Tasks
- [ ] `components/search_bar.py` 생성
- [ ] `st.text_input` 구현
- [ ] Enter 키 검색 지원
- [ ] 검색 버튼 추가
- [ ] 로딩 스피너 표시

#### Implementation
```python
# src/ui/components/search_bar.py
import streamlit as st

def render_search_bar() -> str | None:
    """검색창 렌더링, 쿼리 반환"""

    col1, col2 = st.columns([6, 1])

    with col1:
        query = st.text_input(
            "검색어를 입력하세요",
            placeholder="예: elasticsearch 매핑 설정 방법",
            label_visibility="collapsed",
            key="search_query"
        )

    with col2:
        search_clicked = st.button("🔍 검색", use_container_width=True)

    if query and (search_clicked or st.session_state.get("search_triggered")):
        return query

    return None
```

#### Definition of Done
- 검색어 입력 및 검색 실행
- Enter 키 동작 확인

---

### Story 3.3: 검색 옵션 컴포넌트

**As a** User
**I want** 검색 모드와 결과 개수를 조절
**So that** 원하는 방식으로 검색할 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 옵션 UI
When 모드를 "Vector Only"로 변경
Then 벡터 검색만 실행된다
When top_k를 20으로 변경
Then 20개 결과가 반환된다
```

#### Tasks
- [ ] `components/search_options.py` 생성
- [ ] 검색 모드 선택 (selectbox)
- [ ] 결과 개수 슬라이더
- [ ] 옵션을 session_state에 저장

#### Implementation
```python
# src/ui/components/search_options.py
import streamlit as st
from bookbrain.search.models import SearchMode

def render_search_options() -> dict:
    """검색 옵션 렌더링, 옵션 딕셔너리 반환"""

    col1, col2 = st.columns(2)

    with col1:
        mode = st.selectbox(
            "검색 모드",
            options=["Hybrid", "Vector Only", "Keyword Only"],
            index=0,
            help="Hybrid: 의미 + 키워드 결합 (추천)"
        )

    with col2:
        top_k = st.slider(
            "결과 개수",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )

    mode_map = {
        "Hybrid": SearchMode.HYBRID,
        "Vector Only": SearchMode.VECTOR,
        "Keyword Only": SearchMode.KEYWORD
    }

    return {
        "mode": mode_map[mode],
        "top_k": top_k
    }
```

#### Definition of Done
- 모드 전환 시 검색 결과 변화 확인
- 결과 개수 조절 동작 확인

---

### Story 3.4: 검색 결과 카드 컴포넌트

**As a** User
**I want** 검색 결과를 보기 좋은 카드 형태로 확인
**So that** 내용과 출처를 빠르게 파악할 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 결과
When 결과 카드 렌더링
Then 책 제목이 헤더에 표시된다
And 챕터, 페이지 정보가 표시된다
And 매칭 텍스트에 검색어가 하이라이트된다
And 점수 breakdown이 표시된다
```

#### Tasks
- [ ] `components/result_card.py` 생성
- [ ] 카드 레이아웃 구현
- [ ] 출처 정보 포맷팅
- [ ] 하이라이트 텍스트 표시
- [ ] 점수 표시 (collapsible)

#### Implementation
```python
# src/ui/components/result_card.py
import streamlit as st
from bookbrain.search.models import SearchResult
from bookbrain.utils.highlight import highlight_text

def render_result_card(result: SearchResult, query: str, rank: int):
    """검색 결과 카드 렌더링"""

    with st.container():
        # 헤더: 책 제목
        st.markdown(f"### {rank}. 📖 {result.metadata.book_title}")

        # 출처 정보
        chapter_str = f" > {result.metadata.chapter}" if result.metadata.chapter else ""
        st.caption(
            f"📍 {chapter_str} | 페이지 {result.metadata.page_start}-{result.metadata.page_end}"
        )

        st.divider()

        # 본문 (하이라이트)
        highlighted = highlight_text(result.text, query)
        st.markdown(highlighted, unsafe_allow_html=True)

        # 점수 (expandable)
        with st.expander("📊 점수 상세"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", f"{result.score:.3f}")
            if result.score_vector:
                col2.metric("Vector", f"{result.score_vector:.3f}")
            if result.score_bm25:
                col3.metric("BM25", f"{result.score_bm25:.3f}")

        st.markdown("---")
```

#### Definition of Done
- 카드 레이아웃 정상 표시
- 하이라이트 동작 확인
- 긴 텍스트 처리 확인

---

### Story 3.5: 사이드바 컴포넌트

**As a** User
**I want** 사이드바에서 통계와 필터를 확인
**So that** 데이터 현황을 파악하고 검색 범위를 조절할 수 있다

#### Acceptance Criteria
```gherkin
Given 사이드바
When 앱 로드
Then 총 책 수, 청크 수가 표시된다
And 책 필터 선택 UI가 있다
And 최근 검색어가 표시된다
```

#### Tasks
- [ ] `components/sidebar.py` 생성
- [ ] 통계 정보 표시
- [ ] 책 필터 multiselect
- [ ] 최근 검색어 표시 (session_state)

#### Implementation
```python
# src/ui/components/sidebar.py
import streamlit as st

def render_sidebar(stats: dict, books: list[str]) -> dict:
    """사이드바 렌더링"""

    with st.sidebar:
        st.header("📊 라이브러리 통계")
        col1, col2 = st.columns(2)
        col1.metric("총 책", stats["total_books"])
        col2.metric("총 청크", stats["total_chunks"])

        st.divider()

        st.header("🔖 책 필터")
        selected_books = st.multiselect(
            "검색할 책 선택",
            options=books,
            default=[],
            placeholder="전체 책에서 검색"
        )

        st.divider()

        st.header("🕐 최근 검색")
        recent = st.session_state.get("recent_searches", [])
        for q in recent[-5:]:
            if st.button(q, key=f"recent_{q}"):
                st.session_state.search_query = q
                st.rerun()

    return {"book_filter": selected_books if selected_books else None}
```

#### Definition of Done
- 통계 정보 정상 표시
- 책 필터 동작 확인
- 최근 검색 클릭 시 재검색

---

### Story 3.6: 검색 결과 없음 / 에러 처리

**As a** User
**I want** 결과가 없거나 에러 발생 시 명확한 피드백
**So that** 다음 행동을 결정할 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 결과가 0개
When 결과 표시
Then "검색 결과가 없습니다" 메시지 표시
And 검색어 수정 제안

Given API 에러 발생
When 검색 실행
Then 에러 메시지 표시
And 재시도 버튼 표시
```

#### Tasks
- [ ] 빈 결과 UI 구현
- [ ] 에러 핸들링 UI 구현
- [ ] 검색어 제안 로직 (간단)

#### Implementation
```python
def render_no_results(query: str):
    st.warning("🔍 검색 결과가 없습니다")
    st.info(f"""
    **검색어**: {query}

    다음을 시도해보세요:
    - 다른 키워드로 검색
    - 검색 모드를 "Hybrid"로 변경
    - 책 필터를 해제
    """)

def render_error(error: Exception):
    st.error("⚠️ 검색 중 오류가 발생했습니다")
    with st.expander("오류 상세"):
        st.code(str(error))
    if st.button("🔄 다시 시도"):
        st.rerun()
```

#### Definition of Done
- 빈 결과 시 메시지 표시
- 에러 시 메시지 및 재시도 버튼

---

### Story 3.7: 반응형 레이아웃 및 스타일링

**As a** User
**I want** 다양한 화면 크기에서 잘 보이는 UI
**So that** 데스크톱과 태블릿에서 모두 사용할 수 있다

#### Acceptance Criteria
```gherkin
Given 데스크톱 브라우저
When 앱 접속
Then 와이드 레이아웃으로 표시

Given 좁은 브라우저 창
When 창 크기 줄임
Then 레이아웃이 적절히 조정됨
```

#### Tasks
- [ ] Custom CSS 추가
- [ ] 카드 스타일 개선
- [ ] 다크/라이트 모드 지원
- [ ] 폰트 및 간격 조정

#### Custom CSS
```python
# src/ui/styles.py
CUSTOM_CSS = """
<style>
/* 검색 결과 카드 */
.result-card {
    padding: 1rem;
    border-radius: 8px;
    background: var(--background-secondary);
    margin-bottom: 1rem;
}

/* 하이라이트 */
mark {
    background-color: #fef08a;
    padding: 0 2px;
    border-radius: 2px;
}

/* 다크모드 하이라이트 */
@media (prefers-color-scheme: dark) {
    mark {
        background-color: #854d0e;
        color: #fef9c3;
    }
}

/* 검색창 */
.stTextInput input {
    font-size: 1.1rem;
}
</style>
"""
```

#### Definition of Done
- 데스크톱에서 레이아웃 확인
- 모바일 너비에서 레이아웃 확인
- 다크모드 하이라이트 확인

---

### Story 3.8: 검색 결과 내보내기

**As a** User
**I want** 검색 결과를 마크다운으로 내보내기
**So that** 노트나 문서에 인용할 수 있다

#### Acceptance Criteria
```gherkin
Given 검색 결과
When "마크다운 복사" 버튼 클릭
Then 결과가 마크다운 형식으로 클립보드에 복사됨
```

#### Tasks
- [ ] 마크다운 포맷터 구현
- [ ] 복사 버튼 추가
- [ ] 다운로드 옵션 (선택)

#### Markdown Format
```markdown
## 검색: "elasticsearch 매핑"

### 1. Elasticsearch 실전 가이드 (p.45)
> 매핑(Mapping)은 인덱스에 저장될 문서의 구조를 정의합니다...

### 2. 검색 엔진 구축 (p.201)
> 동적 매핑을 사용하면 필드를 자동으로 감지하지만...

---
*BookBrain에서 검색됨*
```

#### Definition of Done
- 마크다운 형식 정상 생성
- 클립보드 복사 동작

---

## Sprint Planning Suggestion

### Sprint 6 (Core UI)
- Story 3.1: 기본 구조
- Story 3.2: 검색창
- Story 3.3: 검색 옵션
- Story 3.4: 결과 카드

### Sprint 7 (Enhancement)
- Story 3.5: 사이드바
- Story 3.6: 에러 처리
- Story 3.7: 스타일링
- Story 3.8: 내보내기

---

## UI/UX Considerations

### Accessibility
- 키보드 네비게이션 지원
- 적절한 색상 대비
- 스크린리더 호환 라벨

### Performance
- 결과 lazy loading (많은 결과 시)
- 이미지/미디어 최적화 (해당 없음)
- 캐싱 활용

