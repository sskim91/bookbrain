import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDeleteBook } from '@/hooks/useDeleteBook';
import * as booksApi from '@/api/books';
import { toast } from 'sonner';
import React from 'react';

// Mock the books API
vi.mock('@/api/books', () => ({
  getBooks: vi.fn(),
  uploadBook: vi.fn(),
  deleteBook: vi.fn(),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
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

describe('useDeleteBook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('successful deletion', () => {
    it('should delete book and show success toast', async () => {
      const mockDeleteBook = vi.mocked(booksApi.deleteBook);
      mockDeleteBook.mockResolvedValue({ deleted: true });

      const { result } = renderHook(() => useDeleteBook(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ bookId: 1, bookTitle: '테스트 책' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockDeleteBook).toHaveBeenCalledWith(1);
      expect(toast.success).toHaveBeenCalledWith("『테스트 책』이 삭제되었습니다");
    });

    it('should be in pending state while deleting', async () => {
      const mockDeleteBook = vi.mocked(booksApi.deleteBook);
      let resolvePromise: (value: { deleted: boolean }) => void;
      mockDeleteBook.mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      const { result } = renderHook(() => useDeleteBook(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.mutate({ bookId: 1, bookTitle: '테스트 책' });
      });

      // Wait for mutation to start
      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });

      await act(async () => {
        resolvePromise!({ deleted: true });
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });
  });

  describe('failed deletion', () => {
    it('should show error toast on failure', async () => {
      const mockDeleteBook = vi.mocked(booksApi.deleteBook);
      mockDeleteBook.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useDeleteBook(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ bookId: 999, bookTitle: '없는 책' });
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(toast.error).toHaveBeenCalledWith('삭제 중 오류가 발생했습니다');
    });
  });
});
