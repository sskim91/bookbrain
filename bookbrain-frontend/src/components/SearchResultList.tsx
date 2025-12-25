import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';

interface SearchResultListProps {
  results: SearchResultItem[];
  isLoading?: boolean;
  hasSearched?: boolean;
}

export function SearchResultList({
  results,
  isLoading = false,
  hasSearched = false,
}: SearchResultListProps) {
  // Before any search, show nothing
  if (!hasSearched && !isLoading) {
    return null;
  }

  // Loading state - will be implemented in future story
  if (isLoading) {
    return (
      <div className="w-full max-w-[600px] mt-8">
        <div className="text-center text-muted-foreground">
          {STRINGS.SEARCH_LOADING}
        </div>
      </div>
    );
  }

  // Empty results after search
  if (results.length === 0) {
    return (
      <div className="w-full max-w-[600px] mt-8">
        <div className="text-center text-muted-foreground">
          {STRINGS.SEARCH_NO_RESULTS}
        </div>
      </div>
    );
  }

  // Results list - placeholder for future story (2.3)
  return (
    <div className="w-full max-w-[600px] mt-8 space-y-3">
      {results.map((result, index) => (
        <div
          key={`${result.book_id}-${result.page}-${index}`}
          className="p-4 border border-border rounded-lg bg-card"
        >
          <div className="flex justify-between items-start mb-2">
            <div className="font-medium text-foreground">{result.title}</div>
            <div className="text-sm text-muted-foreground">
              p.{result.page}
            </div>
          </div>
          <div className="text-sm text-muted-foreground line-clamp-2">
            {result.content}
          </div>
        </div>
      ))}
    </div>
  );
}
