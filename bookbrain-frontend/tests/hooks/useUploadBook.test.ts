import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUploadBook } from '@/hooks/useUploadBook';
import * as booksApi from '@/api/books';
import { ApiError } from '@/api/client';
import React from 'react';

// Mock the books API
vi.mock('@/api/books', () => ({
  uploadBook: vi.fn(),
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

describe('useUploadBook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should start with idle stage', () => {
      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      expect(result.current.stage).toBe('idle');
      expect(result.current.progress).toBe(0);
      expect(result.current.isUploading).toBe(false);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);
    });
  });

  describe('upload flow', () => {
    it('should transition to uploading stage on mutate', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      mockUpload.mockImplementation(
        () =>
          new Promise((resolve) => {
            // Delay resolution to keep the mutation in pending state
            setTimeout(() => {
              resolve({ status: 'indexed', book_id: 1, chunks_count: 10 });
            }, 100);
          })
      );

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
        // Small delay to let state update
        await new Promise((r) => setTimeout(r, 10));
      });

      expect(result.current.stage).toBe('uploading');
      expect(result.current.isUploading).toBe(true);
    });

    it('should update progress during upload', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      let capturedOnProgress: ((percent: number) => void) | undefined;

      mockUpload.mockImplementation((file, options) => {
        capturedOnProgress = options?.onProgress;
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve({ status: 'indexed', book_id: 1, chunks_count: 10 });
          }, 100);
        });
      });

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
        await new Promise((r) => setTimeout(r, 10));
      });

      // Simulate progress update
      await act(async () => {
        capturedOnProgress?.(50);
      });

      expect(result.current.progress).toBe(50);
    });

    it('should transition to parsing stage after upload completes (100%)', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      let capturedOnProgress: ((percent: number) => void) | undefined;

      mockUpload.mockImplementation((file, options) => {
        capturedOnProgress = options?.onProgress;
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve({ status: 'indexed', book_id: 1, chunks_count: 10 });
          }, 100);
        });
      });

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
        await new Promise((r) => setTimeout(r, 10));
      });

      // Simulate upload reaching 100%
      await act(async () => {
        capturedOnProgress?.(100);
      });

      expect(result.current.stage).toBe('parsing');
    });

    it('should transition to done stage on success', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      mockUpload.mockResolvedValue({
        status: 'indexed',
        book_id: 1,
        chunks_count: 10,
      });

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
      });

      await waitFor(() => {
        expect(result.current.stage).toBe('done');
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual({
        status: 'indexed',
        book_id: 1,
        chunks_count: 10,
      });
    });

    it('should transition to error stage on failure', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      mockUpload.mockRejectedValue(
        new ApiError('UPLOAD_FAILED', 'Upload failed')
      );

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
      });

      await waitFor(() => {
        expect(result.current.stage).toBe('error');
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeInstanceOf(ApiError);
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', async () => {
      const mockUpload = vi.mocked(booksApi.uploadBook);
      mockUpload.mockResolvedValue({
        status: 'indexed',
        book_id: 1,
        chunks_count: 10,
      });

      const { result } = renderHook(() => useUploadBook(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      await act(async () => {
        result.current.upload(file);
      });

      await waitFor(() => {
        expect(result.current.stage).toBe('done');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.stage).toBe('idle');
      expect(result.current.progress).toBe(0);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);
    });
  });
});
