/**
 * UI string constants for the bookbrain frontend.
 * Centralized location for all user-facing text.
 */

export const STRINGS = {
  // Search
  SEARCH_PLACEHOLDER: '책 내용을 검색하세요...',
  SEARCH_ARIA_LABEL: '책 내용 검색',
  SEARCH_LOADING: '검색 중...',
  SEARCH_NO_RESULTS: '검색 결과가 없습니다. 다른 키워드로 시도해보세요.',

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
} as const;
