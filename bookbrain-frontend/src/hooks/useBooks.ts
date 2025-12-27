import { useQuery } from '@tanstack/react-query';
import { getBooks } from '@/api/books';
import type { BookListResponse } from '@/types/book';

/**
 * Hook to fetch and manage the list of indexed books.
 * Uses TanStack Query for caching and state management.
 *
 * @returns Query result with books data, loading, and error states
 */
export function useBooks() {
  return useQuery<BookListResponse>({
    queryKey: ['books'],
    queryFn: () => getBooks(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
