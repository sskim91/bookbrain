import { BookOpen } from 'lucide-react';
import { STRINGS } from '@/constants/strings';

/**
 * Empty state component displayed when no books are registered.
 * Shows a message prompting the user to upload their first book.
 */
export function BookListEmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center py-8 text-center"
      role="status"
      aria-label={STRINGS.BOOK_LIST_EMPTY_TITLE}
    >
      <BookOpen
        className="h-12 w-12 text-muted-foreground/50 mb-3"
        aria-hidden="true"
      />
      <p className="text-sm font-medium text-muted-foreground">
        {STRINGS.BOOK_LIST_EMPTY_TITLE}
      </p>
      <p className="text-xs text-muted-foreground/70 mt-1">
        {STRINGS.BOOK_LIST_EMPTY_DESCRIPTION}
      </p>
    </div>
  );
}
