import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { STRINGS } from '@/constants/strings';

interface DeleteBookDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bookTitle: string;
  onConfirm: () => void;
  isDeleting?: boolean;
}

/**
 * Confirmation dialog for deleting a book.
 * Uses AlertDialog for accessible modal behavior.
 */
export function DeleteBookDialog({
  open,
  onOpenChange,
  bookTitle,
  onConfirm,
  isDeleting = false,
}: DeleteBookDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{STRINGS.BOOK_DELETE_DIALOG_TITLE}</AlertDialogTitle>
          <AlertDialogDescription>
            {STRINGS.BOOK_DELETE_DIALOG_DESCRIPTION(bookTitle)}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>
            {STRINGS.BOOK_DELETE_CANCEL}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? STRINGS.BOOK_DELETE_IN_PROGRESS : STRINGS.BOOK_DELETE_CONFIRM}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
