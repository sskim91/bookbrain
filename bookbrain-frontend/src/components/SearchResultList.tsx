import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';
import { SearchResultCard } from './SearchResultCard';
import { SearchResultSkeletonList } from './SearchResultSkeleton';

interface SearchResultListProps {
  results: SearchResultItem[];
  isLoading?: boolean;
  isError?: boolean;
  hasSearched?: boolean;
  total?: number;
  queryTimeMs?: number;
  onResultClick?: (result: SearchResultItem) => void;
}

export function SearchResultList({
  results,
  isLoading = false,
  isError = false,
  hasSearched = false,
  total,
  queryTimeMs,
  onResultClick,
}: SearchResultListProps) {
  // Before any search, show nothing
  if (!hasSearched && !isLoading) {
    return null;
  }

  // Loading state with Skeleton cards
  if (isLoading) {
    return <SearchResultSkeletonList count={3} />;
  }

  // Error state - hide stale data and show error UI
  if (isError) {
    return (
      <div className="w-full max-w-[800px] mt-8">
        <div className="text-center text-destructive" role="alert">
          <p>{STRINGS.SEARCH_ERROR}</p>
          <p className="text-sm mt-1 text-muted-foreground">
            {STRINGS.SEARCH_ERROR_HINT}
          </p>
        </div>
      </div>
    );
  }

  // Empty results after search
  if (results.length === 0) {
    return (
      <div className="w-full max-w-[800px] mt-8">
        <div className="text-center text-muted-foreground" role="status">
          <p>{STRINGS.SEARCH_NO_RESULTS}</p>
          <p className="text-sm mt-1">{STRINGS.SEARCH_NO_RESULTS_HINT}</p>
        </div>
      </div>
    );
  }

  // Results list with SearchResultCard components
  return (
    <div className="w-full max-w-[800px] mt-8 flex flex-col gap-3">
      {total !== undefined && queryTimeMs !== undefined && (
        <div className="text-sm text-muted-foreground mb-2">
          {STRINGS.SEARCH_RESULTS_META(total, queryTimeMs)}
        </div>
      )}
      {results.map((result, index) => (
        <SearchResultCard
          key={`${result.book_id}-${result.page}-${index}`}
          result={result}
          onClick={onResultClick ? () => onResultClick(result) : undefined}
        />
      ))}
    </div>
  );
}
