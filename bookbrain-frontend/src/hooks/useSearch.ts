import { useQuery } from '@tanstack/react-query';
import { searchBooks } from '@/api/client';
import { CACHE_CONFIG } from '@/constants/config';

/**
 * Hook for searching books using semantic search.
 * Uses TanStack Query useQuery with proper caching (staleTime: 5 minutes).
 *
 * @param query - The committed search query. Pass null to skip fetching.
 */
export function useSearch(query: string | null) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      const result = await searchBooks(query!);
      return result;
    },
    enabled: !!query,
    staleTime: CACHE_CONFIG.STALE_TIME,
    gcTime: CACHE_CONFIG.GC_TIME,
  });
}
