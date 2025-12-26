import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Skeleton loading placeholder for SearchResultCard.
 * Matches the same layout structure as SearchResultCard.
 */
export function SearchResultSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex justify-between items-start mb-3">
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
        </div>
        <Skeleton className="h-4 w-10" />
      </div>
      <div className="space-y-2 mb-4">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <div className="flex justify-end">
        <Skeleton className="h-8 w-20" />
      </div>
    </Card>
  );
}

/**
 * Renders multiple skeleton cards for loading state.
 */
export function SearchResultSkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div
      className="w-full max-w-[800px] mt-8 flex flex-col gap-3"
      aria-label="검색 결과 로딩 중"
      role="status"
    >
      {Array.from({ length: count }).map((_, index) => (
        <SearchResultSkeleton key={index} />
      ))}
    </div>
  );
}
