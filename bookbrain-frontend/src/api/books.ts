import { apiFetch, ApiError } from './client';
import type { BookListResponse, DeleteBookResponse } from '@/types/book';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch the list of indexed books.
 *
 * @param limit - Maximum number of books to return (default: 100)
 * @param offset - Number of books to skip (default: 0)
 * @returns Promise resolving to the book list response
 */
export async function getBooks(
  limit = 100,
  offset = 0
): Promise<BookListResponse> {
  return apiFetch<BookListResponse>(
    `/api/books?limit=${limit}&offset=${offset}`
  );
}

/**
 * Response from the book upload/indexing endpoint
 */
export interface UploadBookResponse {
  status: 'indexed';
  book_id: number;
  chunks_count: number;
}

/**
 * Options for the uploadBook function
 */
export interface UploadBookOptions {
  title?: string;
  author?: string;
  onProgress?: (percent: number) => void;
}

/**
 * Upload a PDF book file for indexing.
 * Uses XMLHttpRequest for upload progress tracking.
 *
 * @param file - The PDF file to upload
 * @param options - Optional title, author, and progress callback
 * @returns Promise resolving to the upload response
 * @throws ApiError on server or network errors
 */
export function uploadBook(
  file: File,
  options?: UploadBookOptions
): Promise<UploadBookResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        options?.onProgress?.(percent);
      }
    });

    // Handle successful response
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText) as UploadBookResponse;
          resolve(response);
        } catch {
          reject(
            new ApiError('PARSE_ERROR', 'Failed to parse server response')
          );
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          reject(
            new ApiError(
              errorData.error?.code || 'UPLOAD_FAILED',
              errorData.error?.message || 'Upload failed',
              errorData.error?.details
            )
          );
        } catch {
          reject(
            new ApiError(
              'UPLOAD_FAILED',
              `Upload failed with status ${xhr.status}`
            )
          );
        }
      }
    });

    // Handle network errors
    xhr.addEventListener('error', () => {
      reject(new ApiError('NETWORK_ERROR', 'Network error occurred'));
    });

    // Build FormData
    const formData = new FormData();
    formData.append('file', file);
    if (options?.title) {
      formData.append('title', options.title);
    }
    if (options?.author) {
      formData.append('author', options.author);
    }

    // Send request
    xhr.open('POST', `${API_BASE_URL}/api/books`);
    xhr.send(formData);
  });
}

/**
 * Delete a book by ID.
 * Removes the book record, associated chunks, and PDF file.
 *
 * @param bookId - The ID of the book to delete
 * @returns Promise resolving to the delete response
 * @throws ApiError on server or network errors (404 if book not found)
 */
export async function deleteBook(bookId: number): Promise<DeleteBookResponse> {
  return apiFetch<DeleteBookResponse>(`/api/books/${bookId}`, {
    method: 'DELETE',
  });
}
