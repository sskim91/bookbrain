import { useState } from 'react';
import { BookOpen, Trash2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { BookListEmptyState } from '@/components/BookListEmptyState';
import { DeleteBookDialog } from '@/components/DeleteBookDialog';
import { useBooks } from '@/hooks/useBooks';
import { useDeleteBook } from '@/hooks/useDeleteBook';
import { STRINGS } from '@/constants/strings';
import { formatDate } from '@/lib/utils';
import type { Book } from '@/types/book';

interface BookItemProps {
  book: Book;
  onDelete: (book: Book) => void;
}

/**
 * Individual book item in the list.
 * Displays book title, page count, registration date, and delete button on hover.
 */
function BookItem({ book, onDelete }: BookItemProps) {
  return (
    <div
      className="group flex items-start gap-3 p-3 rounded-md hover:bg-muted/50 transition-colors"
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
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
        onClick={() => onDelete(book)}
        aria-label={STRINGS.BOOK_DELETE_BUTTON_ARIA_LABEL}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
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
 * - Delete functionality with confirmation dialog
 */
export function BookList() {
  const { data, isLoading, isError } = useBooks();
  const deleteBook = useDeleteBook();
  const [bookToDelete, setBookToDelete] = useState<Book | null>(null);

  const handleDeleteClick = (book: Book) => {
    setBookToDelete(book);
  };

  const handleDeleteConfirm = () => {
    if (bookToDelete) {
      deleteBook.mutate(
        { bookId: bookToDelete.id, bookTitle: bookToDelete.title },
        {
          onSettled: () => {
            setBookToDelete(null);
          },
        }
      );
    }
  };

  const handleDialogClose = (open: boolean) => {
    if (!open && !deleteBook.isPending) {
      setBookToDelete(null);
    }
  };

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
            <BookItem key={book.id} book={book} onDelete={handleDeleteClick} />
          ))}
        </div>
      </ScrollArea>

      <DeleteBookDialog
        open={bookToDelete !== null}
        onOpenChange={handleDialogClose}
        bookTitle={bookToDelete?.title ?? ''}
        onConfirm={handleDeleteConfirm}
        isDeleting={deleteBook.isPending}
      />
    </div>
  );
}
