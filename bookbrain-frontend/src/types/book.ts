export interface Book {
  id: number;
  title: string;
  original_filename: string | null;
  file_name: string | null;
  file_path: string;
  total_pages: number;
  embedding_model: string | null;
  created_at: string;
}

export interface BookListResponse {
  books: Book[];
  total: number;
}

export interface DeleteBookResponse {
  deleted: boolean;
}
