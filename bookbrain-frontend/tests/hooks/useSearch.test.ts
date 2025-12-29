import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { useSearch } from '@/hooks/useSearch';

// Mock the API client
vi.mock('@/api/client', () => ({
  searchBooks: vi.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // Disable cache for tests
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns query state with correct initial values when query is null', () => {
    const { result } = renderHook(() => useSearch(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
    // When enabled is false, status is 'pending' but fetchStatus is 'idle'
    expect(result.current.isError).toBe(false);
    expect(result.current.isFetching).toBe(false); // Not actively fetching
  });

  it('does not fetch when query is null', async () => {
    const { searchBooks } = await import('@/api/client');

    renderHook(() => useSearch(null), {
      wrapper: createWrapper(),
    });

    expect(searchBooks).not.toHaveBeenCalled();
  });

  it('fetches when query is provided', async () => {
    const { searchBooks } = await import('@/api/client');
    const mockResponse = {
      results: [
        {
          book_id: 1,
          title: 'Test Book',
          author: 'Author',
          page: 100,
          content: 'Test content',
          score: 0.9,
        },
      ],
      total: 1,
      query_time_ms: 150,
    };
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useSearch('test query'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(searchBooks).toHaveBeenCalledWith('test query', 10, 0.3);
    expect(result.current.data).toEqual(mockResponse);
  });

  it('sets isFetching while fetching', async () => {
    const { searchBooks } = await import('@/api/client');
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    (searchBooks as ReturnType<typeof vi.fn>).mockReturnValue(promise);

    const { result } = renderHook(() => useSearch('test'), {
      wrapper: createWrapper(),
    });

    // Should be fetching
    await waitFor(() => {
      expect(result.current.isFetching).toBe(true);
    });

    // Resolve the promise
    resolvePromise!({ results: [], total: 0, query_time_ms: 10 });

    await waitFor(() => {
      expect(result.current.isFetching).toBe(false);
    });
  });

  it('sets isError on failure', async () => {
    const { searchBooks } = await import('@/api/client');
    const error = new Error('Search failed');
    (searchBooks as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() => useSearch('test'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('caches results with staleTime of 5 minutes', async () => {
    const { searchBooks } = await import('@/api/client');
    const mockResponse = {
      results: [],
      total: 0,
      query_time_ms: 50,
    };
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Use a custom QueryClient to test staleTime
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);

    // First render with query
    const { result, rerender } = renderHook(
      ({ query }: { query: string | null }) => useSearch(query),
      {
        wrapper,
        initialProps: { query: 'cached query' },
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(searchBooks).toHaveBeenCalledTimes(1);

    // Re-render with same query - should use cache
    rerender({ query: 'cached query' });

    // Should still have data and not refetch (staleTime is 5 minutes)
    expect(result.current.data).toEqual(mockResponse);
    expect(searchBooks).toHaveBeenCalledTimes(1); // Still 1, no refetch
  });

  it('refetches when query changes', async () => {
    const { searchBooks } = await import('@/api/client');
    const mockResponse1 = {
      results: [{ book_id: 1, title: 'Book 1', author: null, page: 1, content: 'Content 1', score: 0.9 }],
      total: 1,
      query_time_ms: 50,
    };
    const mockResponse2 = {
      results: [{ book_id: 2, title: 'Book 2', author: null, page: 2, content: 'Content 2', score: 0.8 }],
      total: 1,
      query_time_ms: 60,
    };
    (searchBooks as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    const { result, rerender } = renderHook(
      ({ query }: { query: string | null }) => useSearch(query),
      {
        wrapper: createWrapper(),
        initialProps: { query: 'query1' },
      }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockResponse1);
    });

    expect(searchBooks).toHaveBeenCalledWith('query1', 10, 0.3);

    // Change query
    rerender({ query: 'query2' });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockResponse2);
    });

    expect(searchBooks).toHaveBeenCalledWith('query2', 10, 0.3);
    expect(searchBooks).toHaveBeenCalledTimes(2);
  });
});
