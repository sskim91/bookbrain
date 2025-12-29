/**
 * UI string constants for the bookbrain frontend.
 * Centralized location for all user-facing text.
 */

export const STRINGS = {
  // Search
  SEARCH_PLACEHOLDER: '책 내용을 검색하세요...',
  SEARCH_ARIA_LABEL: '책 내용 검색',
  SEARCH_LOADING: '검색 중...',
  SEARCH_NO_RESULTS: '검색 결과가 없습니다',
  SEARCH_NO_RESULTS_HINT: '다른 키워드로 시도해보세요',
  SEARCH_ERROR: '검색 중 오류가 발생했습니다',
  SEARCH_ERROR_HINT: '잠시 후 다시 시도해주세요',
  SEARCH_EMPTY_QUERY: '검색어를 입력해주세요',
  SEARCH_RESULTS_META: (total: number, timeMs: number) =>
    `${total}건, ${(timeMs / 1000).toFixed(2)}초`,

  // Header
  APP_NAME: 'bookbrain',

  // Theme
  THEME_SWITCH_TO_LIGHT: 'Switch to light mode',
  THEME_SWITCH_TO_DARK: 'Switch to dark mode',

  // Copy
  COPY: 'Copy',
  COPYING: 'Copying...',
  COPIED: 'Copied',
  COPY_BUTTON_LABEL: '마크다운으로 복사',
  TOAST_COPIED: '복사됨',
  TOAST_COPY_FAILED: '복사에 실패했습니다',

  // Score
  SCORE_ARIA_LABEL: (percent: number) => `유사도 ${percent}%`,

  // Detail Dialog
  DIALOG_DESCRIPTION_SUFFIX: '의 상세 내용',
  DIALOG_CLOSE: '닫기',

  // Command Palette
  COMMAND_PALETTE_TITLE: '책 검색',
  COMMAND_PALETTE_PLACEHOLDER: '검색...',
  COMMAND_PALETTE_DESCRIPTION: '검색어를 입력하여 책 내용을 찾으세요',
  COMMAND_PALETTE_EMPTY: '검색 결과가 없습니다',
  COMMAND_PALETTE_LOADING: '검색 중...',

  // Upload
  UPLOAD_BUTTON: 'Upload',
  UPLOAD_BUTTON_ARIA_LABEL: 'PDF 업로드',
  UPLOAD_DIALOG_TITLE: 'Upload PDF',
  UPLOAD_DIALOG_DESCRIPTION: 'Add a new book to your library',
  UPLOAD_DIALOG_SR_INSTRUCTIONS:
    'PDF 파일을 선택하여 책을 추가하세요. 업로드 후 자동으로 텍스트가 추출되어 검색이 가능해집니다.',
  UPLOAD_DIALOG_PLACEHOLDER: 'PDF upload area will be here',

  // Dropzone
  DROPZONE_DEFAULT_TEXT: 'PDF 파일을 드래그하거나 클릭하여 선택',
  DROPZONE_ACTIVE_TEXT: '여기에 놓으세요',
  DROPZONE_ERROR_INVALID_TYPE: 'PDF 파일만 업로드 가능합니다',
  DROPZONE_ARIA_LABEL:
    'PDF 파일 드롭존. 클릭하여 파일을 선택하거나 드래그 앤 드롭하세요.',

  // Upload flow
  UPLOAD_SUBMIT_BUTTON: '업로드',
  UPLOAD_SELECTED_FILE: '선택된 파일:',
  UPLOAD_FILE_REMOVE: '파일 선택 취소',
  UPLOAD_FILE_REMOVE_ARIA_LABEL: '선택된 파일 제거',

  // Upload Progress
  UPLOAD_STAGE_UPLOADING: '업로드 중...',
  UPLOAD_STAGE_PARSING: 'PDF 파싱 중...',
  UPLOAD_STAGE_CHUNKING: '텍스트 분할 중...',
  UPLOAD_STAGE_EMBEDDING: '임베딩 생성 중...',
  UPLOAD_STAGE_COMPLETE: '완료!',
  UPLOAD_PROGRESS_ARIA_LABEL: (percent: number) => `업로드 진행률 ${percent}%`,
  UPLOAD_STAGE_UPLOAD: '업로드',
  UPLOAD_STAGE_PARSE: '파싱',
  UPLOAD_STAGE_CHUNK: '청킹',
  UPLOAD_STAGE_EMBED: '임베딩',

  // Upload Error
  UPLOAD_ERROR_GENERIC: '업로드 중 오류가 발생했습니다',
  UPLOAD_RETRY_BUTTON: '다시 시도',
  UPLOAD_ERROR_INVALID_FORMAT: 'PDF 파일만 업로드 가능합니다',
  UPLOAD_ERROR_DUPLICATE: '이미 등록된 책입니다',
  UPLOAD_ERROR_INDEXING: '인덱싱 중 오류가 발생했습니다',

  // Upload Success Toast (AC #1, #2)
  UPLOAD_SUCCESS_TOAST: (bookTitle: string) => `『${bookTitle}』 인덱싱 완료`,

  // Upload Complete Actions (AC #3)
  UPLOAD_ANOTHER_BUTTON: '다른 파일 업로드',

  // Book List
  BOOK_LIST_TITLE: (count: number) => `등록된 책 (${count}권)`,
  BOOK_LIST_EMPTY_TITLE: '등록된 책이 없습니다',
  BOOK_LIST_EMPTY_DESCRIPTION: 'PDF 파일을 업로드하여 책을 추가하세요',
  BOOK_LIST_PAGE_COUNT: (pages: number) => `${pages}p`,
  BOOK_LIST_LOADING: '책 목록을 불러오는 중...',
  BOOK_LIST_ERROR: '책 목록을 불러오는 데 실패했습니다',
  BOOK_LIST_ERROR_HINT: '잠시 후 다시 시도해주세요',

  // Book Delete
  BOOK_DELETE_BUTTON_ARIA_LABEL: '책 삭제',
  BOOK_DELETE_DIALOG_TITLE: '책을 삭제하시겠습니까?',
  BOOK_DELETE_DIALOG_DESCRIPTION: (bookTitle: string) =>
    `『${bookTitle}』을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`,
  BOOK_DELETE_CANCEL: '취소',
  BOOK_DELETE_CONFIRM: '삭제',
  BOOK_DELETE_IN_PROGRESS: '삭제 중...',
  BOOK_DELETE_SUCCESS: (bookTitle: string) => `『${bookTitle}』이 삭제되었습니다`,
  BOOK_DELETE_ERROR: '삭제 중 오류가 발생했습니다',
} as const;
