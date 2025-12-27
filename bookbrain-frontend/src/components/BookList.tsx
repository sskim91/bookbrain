import { BookOpen } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { BookListEmptyState } from '@/components/BookListEmptyState';
import { useBooks } from '@/hooks/useBooks';
import { STRINGS } from '@/constants/strings';
import { formatDate } from '@/lib/utils';
import type { Book } from '@/types/book';

interface BookItemProps {
  book: Book;
}

/**
 * Individual book item in the list.
 * Displays book title, page count, and registration date.
 */
function BookItem({ book }: BookItemProps) {
  return (
    <div
      className="flex items-start gap-3 p-3 rounded-md hover:bg-muted/50 transition-colors"
      role="article"
      aria-label={book.title}
    >
      <BookOpen
        className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{book.title}</p>
        <p className="text-xs text-muted-foreground">
          {STRINGS.BOOK_LIST_PAGE_COUNT(book.total_pages)} · {formatDate(book.created_at)}
        </p>
      </div>
    </div>
  );
}

/**
 * Loading skeleton for the book list.
 */
function BookListSkeleton() {
  return (
    <div className="space-y-2 py-2" aria-label={STRINGS.BOOK_LIST_LOADING}>
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-start gap-3 p-3">
          <Skeleton className="h-5 w-5 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Book list component that displays all registered books.
 * Features:
 * - Scrollable list with max height
 * - Loading skeleton while fetching
 * - Empty state when no books exist
 * - Error handling
 */
export function BookList() {
  const { data, isLoading, isError } = useBooks();

  if (isLoading) {
    return <BookListSkeleton />;
  }

  if (isError) {
    return (
      <div className="py-4 text-center text-sm text-destructive">
        {STRINGS.BOOK_LIST_ERROR}
      </div>
    );
  }

  const books = data?.books ?? [];

  if (books.length === 0) {
    return <BookListEmptyState />;
  }

  // Sort by created_at descending (most recent first)
  const sortedBooks = [...books].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground px-1">
        {STRINGS.BOOK_LIST_TITLE(books.length)}
      </h3>
      <ScrollArea className="h-[200px] rounded-md border">
        <div className="p-1">
          {sortedBooks.map((book) => (
            <BookItem key={book.id} book={book} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
