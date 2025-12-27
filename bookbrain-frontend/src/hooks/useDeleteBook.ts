import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { deleteBook } from '@/api/books';
import { STRINGS } from '@/constants/strings';
import type { DeleteBookResponse } from '@/types/book';

/**
 * Variables for the delete book mutation.
 * Includes bookTitle for toast message.
 */
export interface DeleteBookVariables {
  bookId: number;
  bookTitle: string;
}

/**
 * Hook to delete a book by ID.
 * Uses TanStack Query mutation for state management.
 *
 * Features:
 * - Invalidates books query on success
 * - Shows success/error toast notifications
 *
 * @returns Mutation result with mutate function and loading/error states
 */
export function useDeleteBook() {
  const queryClient = useQueryClient();

  return useMutation<DeleteBookResponse, Error, DeleteBookVariables>({
    mutationFn: ({ bookId }) => deleteBook(bookId),
    onSuccess: (_, { bookTitle }) => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      toast.success(STRINGS.BOOK_DELETE_SUCCESS(bookTitle));
    },
    onError: () => {
      toast.error(STRINGS.BOOK_DELETE_ERROR);
    },
  });
}
