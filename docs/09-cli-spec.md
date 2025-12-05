# CLI Specification

> **Role**: Technical Lead
> **Created**: 2025-12-04
> **Version**: 1.0

---

## 1. CLI Overview

BookBrain CLI는 **Typer** 기반의 명령줄 인터페이스입니다.

### 1.1 기본 구조

```
bookbrain [OPTIONS] COMMAND [ARGS]

Commands:
  ingest     PDF 파일을 벡터 DB에 수집
  search     장서 검색
  list       등록된 책 목록
  delete     책 삭제
  stats      라이브러리 통계
  serve      웹 UI 서버 시작
  config     설정 관리
  cache      캐시 관리
  backup     백업/복원
```

### 1.2 전역 옵션

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--config` | `-c` | 설정 파일 경로 | `.env` |
| `--data-dir` | `-d` | 데이터 디렉토리 | `./data` |
| `--verbose` | `-v` | 상세 로그 출력 | `False` |
| `--quiet` | `-q` | 최소 출력 | `False` |
| `--help` | `-h` | 도움말 | - |
| `--version` | - | 버전 정보 | - |

---

## 2. Commands

### 2.1 `ingest` - PDF 수집

```bash
bookbrain ingest [OPTIONS] PDF_PATH
```

#### Arguments

| 인자 | 필수 | 설명 |
|------|------|------|
| `PDF_PATH` | ✓ | PDF 파일 경로 (파일 또는 디렉토리) |

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--title` | `-t` | 책 제목 (수동 지정) | 파일명에서 추출 |
| `--language` | `-l` | 문서 언어 | `ko` |
| `--recursive` | `-r` | 하위 디렉토리 포함 | `False` |
| `--skip-cache` | - | 캐시 사용 안 함 | `False` |
| `--dry-run` | - | 실제 저장 없이 시뮬레이션 | `False` |
| `--force` | `-f` | 중복 무시하고 덮어쓰기 | `False` |

#### Examples

```bash
# 단일 파일 수집
bookbrain ingest ./books/modern_java.pdf

# 제목 지정
bookbrain ingest -t "모던 자바 인 액션" ./books/mjia.pdf

# 디렉토리 내 모든 PDF
bookbrain ingest -r ./books/

# 시뮬레이션 (실제 저장 X)
bookbrain ingest --dry-run ./books/test.pdf

# 중복 덮어쓰기
bookbrain ingest -f ./books/updated_book.pdf
```

#### Output

```
📥 수집 시작: modern_java.pdf

[1/6] 파일 검증... ✓
[2/6] 문서 파싱... ✓ (45초)
[3/6] 메타데이터 추출... ✓
      제목: 모던 자바 인 액션
      페이지: 592
[4/6] 텍스트 청킹... ✓ (1,234개)
[5/6] 임베딩 생성... ✓ (23초)
[6/6] 저장... ✓

✅ 수집 완료!
   책 ID: modern_java_in_action
   청크: 1,234개
   소요 시간: 1분 23초
   비용 추정: $0.0247
```

#### Implementation

```python
# main.py

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, TaskID

app = typer.Typer(
    name="bookbrain",
    help="BookBrain - Personal Library RAG System",
    add_completion=False,
)
console = Console()


@app.command()
def ingest(
    pdf_path: Path = typer.Argument(
        ...,
        help="PDF 파일 또는 디렉토리 경로",
        exists=True,
        readable=True,
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title", "-t",
        help="책 제목 (수동 지정)",
    ),
    language: str = typer.Option(
        "ko",
        "--language", "-l",
        help="문서 언어 코드",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="하위 디렉토리 포함",
    ),
    skip_cache: bool = typer.Option(
        False,
        "--skip-cache",
        help="파싱 캐시 사용 안 함",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="실제 저장 없이 시뮬레이션",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="중복 덮어쓰기",
    ),
):
    """PDF 파일을 벡터 DB에 수집"""
    import asyncio
    from bookbrain.core.config import get_settings
    from bookbrain.ingestion.pipeline import IngestionPipeline

    settings = get_settings()

    # PDF 파일 목록 수집
    if pdf_path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(pdf_path.glob(pattern))
    else:
        pdf_files = [pdf_path]

    if not pdf_files:
        console.print("[red]PDF 파일을 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]📥 {len(pdf_files)}개 파일 수집 시작[/bold]\n")

    # 파이프라인 초기화
    pipeline = IngestionPipeline(settings)

    # 진행 상황 표시
    with Progress(console=console) as progress:
        for pdf_file in pdf_files:
            task = progress.add_task(
                f"[cyan]{pdf_file.name}[/cyan]",
                total=6,
            )

            def on_progress(stage: str, pct: float):
                stage_num = {
                    "validating": 1,
                    "parsing": 2,
                    "extracting": 3,
                    "chunking": 4,
                    "embedding": 5,
                    "storing": 6,
                }.get(stage, 0)
                progress.update(task, completed=stage_num)

            metadata = {"language": language}
            if title:
                metadata["title"] = title

            result = asyncio.run(
                pipeline.ingest(
                    pdf_path=pdf_file,
                    metadata_override=metadata,
                    progress_callback=on_progress,
                    skip_cache=skip_cache,
                    dry_run=dry_run,
                    force=force,
                )
            )

            if result.success:
                console.print(f"\n✅ [green]{pdf_file.name}[/green] 완료")
                console.print(f"   청크: {result.total_chunks}개")
                console.print(f"   시간: {result.total_time_sec:.1f}초")
            else:
                console.print(f"\n❌ [red]{pdf_file.name}[/red] 실패")
                console.print(f"   에러: {result.error}")
```

---

### 2.2 `search` - 검색

```bash
bookbrain search [OPTIONS] QUERY
```

#### Arguments

| 인자 | 필수 | 설명 |
|------|------|------|
| `QUERY` | ✓ | 검색 쿼리 |

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--mode` | `-m` | 검색 모드 (hybrid/vector/keyword) | `hybrid` |
| `--top` | `-k` | 결과 개수 | `10` |
| `--book` | `-b` | 특정 책에서만 검색 (반복 가능) | 전체 |
| `--output` | `-o` | 출력 형식 (table/json/markdown) | `table` |
| `--full` | - | 전체 텍스트 표시 | `False` |

#### Examples

```bash
# 기본 검색
bookbrain search "스트림 API 사용법"

# 키워드 검색, 20개 결과
bookbrain search -m keyword -k 20 "Optional.orElseGet"

# 특정 책에서 검색
bookbrain search -b modern_java "람다 표현식"

# JSON 출력
bookbrain search -o json "Spring Security" > results.json

# 마크다운 출력
bookbrain search -o markdown "의존성 주입" > results.md
```

#### Output (table)

```
🔍 검색: "스트림 API 사용법" (hybrid)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Score   Book                   Chapter           Page
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1  0.892   모던 자바 인 액션       4장 스트림 소개     123-125
2  0.856   이펙티브 자바           아이템 45          201
3  0.823   자바 8 인 액션          Part 2             89-91
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 3개 결과 (234ms)

결과 상세 보기: bookbrain search "스트림 API" --full
```

#### Output (json)

```json
{
  "query": "스트림 API 사용법",
  "mode": "hybrid",
  "results": [
    {
      "rank": 1,
      "score": 0.892,
      "book_title": "모던 자바 인 액션",
      "chapter": "4장 스트림 소개",
      "page_start": 123,
      "page_end": 125,
      "text": "스트림 API는 데이터 처리 연산을 지원하도록..."
    }
  ],
  "total": 3,
  "time_ms": 234
}
```

#### Implementation

```python
@app.command()
def search(
    query: str = typer.Argument(..., help="검색 쿼리"),
    mode: str = typer.Option(
        "hybrid",
        "--mode", "-m",
        help="검색 모드",
    ),
    top: int = typer.Option(
        10,
        "--top", "-k",
        help="결과 개수",
        min=1,
        max=50,
    ),
    book: Optional[list[str]] = typer.Option(
        None,
        "--book", "-b",
        help="특정 책 필터",
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="출력 형식",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="전체 텍스트",
    ),
):
    """장서 검색"""
    import asyncio
    from rich.table import Table

    from bookbrain.core.config import get_settings
    from bookbrain.search.service import SearchService
    from bookbrain.models.search import SearchQuery, SearchMode

    settings = get_settings()
    service = _get_search_service(settings)

    search_query = SearchQuery(
        text=query,
        mode=SearchMode(mode),
        top_k=top,
        book_filter=book,
    )

    console.print(f'[bold]🔍 검색: "{query}"[/bold] ({mode})\n')

    response = asyncio.run(service.search(search_query))

    if output == "json":
        _output_json(response)
    elif output == "markdown":
        _output_markdown(response, query)
    else:
        _output_table(response, full)


def _output_table(response, show_full: bool):
    """테이블 출력"""
    from rich.table import Table

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Book", width=25)
    table.add_column("Chapter", width=20)
    table.add_column("Page", width=10)

    for i, result in enumerate(response.results, 1):
        page = f"{result.page_start}"
        if result.page_end != result.page_start:
            page = f"{result.page_start}-{result.page_end}"

        table.add_row(
            str(i),
            f"{result.score:.3f}",
            result.book_title[:23] + "..." if len(result.book_title) > 25 else result.book_title,
            (result.chapter or "")[:18] + "..." if len(result.chapter or "") > 20 else (result.chapter or "-"),
            page,
        )

    console.print(table)
    console.print(f"\n📊 {len(response.results)}개 결과 ({response.search_time_ms:.0f}ms)")
```

---

### 2.3 `list` - 책 목록

```bash
bookbrain list [OPTIONS]
```

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--sort` | `-s` | 정렬 기준 (title/chunks/date) | `title` |
| `--output` | `-o` | 출력 형식 | `table` |

#### Examples

```bash
# 기본 목록
bookbrain list

# 청크 수 기준 정렬
bookbrain list -s chunks

# JSON 출력
bookbrain list -o json
```

#### Output

```
📚 등록된 책 목록

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ID                        Title                  Chunks  Pages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1  modern_java_in_action     모던 자바 인 액션        1,234   592
2  effective_java            이펙티브 자바            987     412
3  spring_in_action          스프링 인 액션           1,456   624
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

총 3권, 3,677 청크
```

#### Implementation

```python
@app.command("list")
def list_books(
    sort: str = typer.Option(
        "title",
        "--sort", "-s",
        help="정렬 기준",
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="출력 형식",
    ),
):
    """등록된 책 목록"""
    from rich.table import Table

    settings = get_settings()
    service = _get_search_service(settings)
    stats = service.get_stats()

    books = stats["books"]

    # 정렬
    if sort == "chunks":
        books.sort(key=lambda x: x["chunks"], reverse=True)
    elif sort == "date":
        books.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    else:  # title
        books.sort(key=lambda x: x["title"])

    if output == "json":
        import json
        console.print(json.dumps(books, ensure_ascii=False, indent=2))
        return

    table = Table(title="📚 등록된 책 목록")
    table.add_column("#", style="dim", width=3)
    table.add_column("ID", width=28)
    table.add_column("Title", width=25)
    table.add_column("Chunks", justify="right", width=8)

    for i, book in enumerate(books, 1):
        table.add_row(
            str(i),
            book["id"],
            book["title"],
            f"{book['chunks']:,}",
        )

    console.print(table)
    console.print(f"\n총 {len(books)}권, {stats['total_chunks']:,} 청크")
```

---

### 2.4 `delete` - 책 삭제

```bash
bookbrain delete [OPTIONS] BOOK_ID
```

#### Arguments

| 인자 | 필수 | 설명 |
|------|------|------|
| `BOOK_ID` | ✓ | 삭제할 책 ID |

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--yes` | `-y` | 확인 없이 삭제 | `False` |
| `--keep-cache` | - | 파싱 캐시 유지 | `False` |

#### Examples

```bash
# 확인 후 삭제
bookbrain delete modern_java_in_action

# 확인 없이 삭제
bookbrain delete -y old_book

# 캐시 유지하고 삭제
bookbrain delete --keep-cache test_book
```

#### Implementation

```python
@app.command()
def delete(
    book_id: str = typer.Argument(..., help="삭제할 책 ID"),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="확인 없이 삭제",
    ),
    keep_cache: bool = typer.Option(
        False,
        "--keep-cache",
        help="파싱 캐시 유지",
    ),
):
    """책 삭제"""
    settings = get_settings()
    chroma = ChromaStore(settings)
    chroma.initialize()

    # 책 확인
    stats = chroma.get_stats()
    book = next((b for b in stats["books"] if b["id"] == book_id), None)

    if not book:
        console.print(f"[red]책을 찾을 수 없습니다: {book_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]삭제 대상:[/yellow]")
    console.print(f"  제목: {book['title']}")
    console.print(f"  청크: {book['chunks']}개")

    if not yes:
        confirm = typer.confirm("정말 삭제하시겠습니까?")
        if not confirm:
            console.print("[dim]취소됨[/dim]")
            raise typer.Exit(0)

    # 삭제 실행
    deleted = chroma.delete_book(book_id)

    if not keep_cache:
        # 캐시 삭제
        from bookbrain.ingestion.cache import ParseCache
        cache = ParseCache(settings)
        # book의 file_hash로 캐시 삭제 필요

    console.print(f"[green]✓ {deleted}개 청크 삭제됨[/green]")
```

---

### 2.5 `stats` - 통계

```bash
bookbrain stats [OPTIONS]
```

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--detailed` | `-d` | 상세 통계 | `False` |
| `--output` | `-o` | 출력 형식 | `table` |

#### Output

```
📊 라이브러리 통계

총 책: 52권
총 청크: 45,678개
총 페이지: 12,345페이지

스토리지:
  ChromaDB: 234.5 MB
  BM25 Index: 12.3 MB
  캐시: 45.6 MB

상위 5개 책 (청크 수):
  1. 스프링 인 액션     1,456개
  2. 모던 자바 인 액션  1,234개
  3. 이펙티브 자바      987개
  ...
```

---

### 2.6 `serve` - 웹 서버

```bash
bookbrain serve [OPTIONS]
```

#### Options

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--host` | `-H` | 호스트 | `localhost` |
| `--port` | `-p` | 포트 | `8501` |
| `--no-browser` | - | 브라우저 자동 열기 비활성화 | `False` |

#### Examples

```bash
# 기본 실행
bookbrain serve

# 외부 접속 허용
bookbrain serve -H 0.0.0.0 -p 8080

# 브라우저 자동 열기 비활성화
bookbrain serve --no-browser
```

#### Implementation

```python
@app.command()
def serve(
    host: str = typer.Option(
        "localhost",
        "--host", "-H",
        help="호스트",
    ),
    port: int = typer.Option(
        8501,
        "--port", "-p",
        help="포트",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="브라우저 자동 열기 비활성화",
    ),
):
    """웹 UI 서버 시작"""
    import subprocess
    import sys

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "src/bookbrain/ui/app.py",
        "--server.address", host,
        "--server.port", str(port),
    ]

    if no_browser:
        cmd.extend(["--server.headless", "true"])

    console.print(f"[bold]🌐 서버 시작: http://{host}:{port}[/bold]")

    subprocess.run(cmd)
```

---

### 2.7 `config` - 설정 관리

```bash
bookbrain config [COMMAND]

Commands:
  show     현재 설정 표시
  set      설정 값 변경
  reset    기본값으로 초기화
```

#### Examples

```bash
# 현재 설정 표시
bookbrain config show

# 설정 변경
bookbrain config set chunk_size 1000

# 초기화
bookbrain config reset
```

---

### 2.8 `cache` - 캐시 관리

```bash
bookbrain cache [COMMAND]

Commands:
  list     캐시된 파일 목록
  clear    캐시 삭제
  stats    캐시 통계
```

#### Examples

```bash
# 캐시 목록
bookbrain cache list

# 만료된 캐시 삭제
bookbrain cache clear --expired

# 전체 캐시 삭제
bookbrain cache clear --all
```

---

### 2.9 `backup` - 백업/복원

```bash
bookbrain backup [COMMAND]

Commands:
  create   백업 생성
  restore  백업 복원
  list     백업 목록
```

#### Examples

```bash
# 백업 생성
bookbrain backup create

# 특정 위치에 백업
bookbrain backup create -o /backup/bookbrain_$(date +%Y%m%d).tar.gz

# 복원
bookbrain backup restore ./backups/bookbrain_20251204.tar.gz

# 백업 목록
bookbrain backup list
```

---

## 3. Exit Codes

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1 | 일반 에러 |
| 2 | 사용법 에러 (잘못된 인자) |
| 3 | 파일 없음 |
| 4 | 권한 에러 |
| 5 | 설정 에러 |
| 10 | API 에러 (Storm Parse) |
| 11 | API 에러 (OpenAI) |
| 20 | 저장소 에러 |

---

## 4. Configuration File

### 4.1 `.bookbrainrc` (선택적)

```yaml
# ~/.bookbrainrc

# 기본 설정
data_dir: ~/bookbrain/data
log_level: INFO

# 수집 설정
ingestion:
  chunk_size: 800
  chunk_overlap: 200
  language: ko

# 검색 설정
search:
  default_mode: hybrid
  default_top_k: 10
  vector_weight: 0.5

# UI 설정
ui:
  theme: auto
  show_scores: false
```

---

## 5. Shell Completion

### 5.1 Bash

```bash
# ~/.bashrc에 추가
eval "$(_BOOKBRAIN_COMPLETE=bash_source bookbrain)"
```

### 5.2 Zsh

```zsh
# ~/.zshrc에 추가
eval "$(_BOOKBRAIN_COMPLETE=zsh_source bookbrain)"
```

### 5.3 Fish

```fish
# ~/.config/fish/completions/bookbrain.fish
_BOOKBRAIN_COMPLETE=fish_source bookbrain | source
```

---

## 6. Interactive Mode (향후)

```bash
bookbrain interactive
# 또는
bookbrain -i

BookBrain Interactive Mode
Type 'help' for commands, 'exit' to quit

bookbrain> search 스트림 API
... results ...

bookbrain> /mode keyword
검색 모드: keyword

bookbrain> search Optional.orElseGet
... results ...

bookbrain> exit
```

---

## 7. Logging

### 7.1 로그 위치

```
~/.bookbrain/logs/
├── bookbrain.log        # 메인 로그
├── ingestion.log        # 수집 로그
└── search.log           # 검색 로그
```

### 7.2 로그 레벨

```bash
# 디버그 로그 활성화
bookbrain -v ingest ./book.pdf

# 상세 디버그
bookbrain -vv ingest ./book.pdf
```

