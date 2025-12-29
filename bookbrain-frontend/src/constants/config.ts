/**
 * Application configuration constants.
 * Centralized location for cache settings and other config values.
 */

export const CACHE_CONFIG = {
  /** Time before data is considered stale (5 minutes) */
  STALE_TIME: 5 * 60 * 1000,
  /** Time before cached data is garbage collected (10 minutes) */
  GC_TIME: 10 * 60 * 1000,
  /** Number of retry attempts for failed queries */
  RETRY_COUNT: 0,
} as const;

export const SEARCH_CONFIG = {
  /** Minimum similarity score threshold (0.0-1.0) */
  MIN_SCORE_THRESHOLD: 0.3,
} as const;
