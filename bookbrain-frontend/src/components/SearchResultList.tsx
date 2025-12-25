import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';
import { SearchResultCard } from './SearchResultCard';

interface SearchResultListProps {
  results: SearchResultItem[];
  isLoading?: boolean;
  hasSearched?: boolean;
  onResultClick?: (result: SearchResultItem) => void;
}

export function SearchResultList({
  results,
  isLoading = false,
  hasSearched = false,
  onResultClick,
}: SearchResultListProps) {
  // Before any search, show nothing
  if (!hasSearched && !isLoading) {
    return null;
  }

  // Loading state - will be enhanced in Story 2.4 with skeleton
  if (isLoading) {
    return (
      <div className="w-full max-w-[800px] mt-8">
        <div className="text-center text-muted-foreground">
          {STRINGS.SEARCH_LOADING}
        </div>
      </div>
    );
  }

  // Empty results after search
  if (results.length === 0) {
    return (
      <div className="w-full max-w-[800px] mt-8">
        <div className="text-center text-muted-foreground">
          {STRINGS.SEARCH_NO_RESULTS}
        </div>
      </div>
    );
  }

  // Results list with SearchResultCard components
  return (
    <div className="w-full max-w-[800px] mt-8 flex flex-col gap-3">
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
