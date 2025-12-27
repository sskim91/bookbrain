import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBooks } from '@/hooks/useBooks';
import * as booksApi from '@/api/books';
import React from 'react';

// Mock the books API
vi.mock('@/api/books', () => ({
  getBooks: vi.fn(),
  uploadBook: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
};

describe('useBooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('loading state', () => {
    it('should start with loading state', () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { result } = renderHook(() => useBooks(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('success state', () => {
    it('should return book list on success', async () => {
      const mockBooks = {
        books: [
          {
            id: 1,
            title: 'Test Book',
            author: 'Test Author',
            file_path: '/path/to/book.pdf',
            total_pages: 100,
            embedding_model: 'text-embedding-3-small',
            created_at: '2025-12-27T10:00:00Z',
          },
        ],
        total: 1,
      };

      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      const { result } = renderHook(() => useBooks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockBooks);
      expect(result.current.data?.books).toHaveLength(1);
      expect(result.current.data?.books[0].title).toBe('Test Book');
    });

    it('should return empty list when no books', async () => {
      const mockBooks = {
        books: [],
        total: 0,
      };

      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      const { result } = renderHook(() => useBooks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.books).toHaveLength(0);
    });
  });

  describe('error state', () => {
    it('should handle API error', async () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBooks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeDefined();
    });
  });
});
