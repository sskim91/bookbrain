export interface SearchResultItem {
  book_id: number;
  title: string;
  author: string | null;
  page: number;
  content: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResultItem[];
  total: number;
  query_time_ms: number;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  offset?: number;
  min_score?: number;
}
