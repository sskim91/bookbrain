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
} as const;
