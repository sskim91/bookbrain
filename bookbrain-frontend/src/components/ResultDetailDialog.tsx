import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Copy, Check, Loader2, X } from 'lucide-react';
import { useClipboard } from '@/hooks/useClipboard';
import { formatMarkdown } from '@/lib/formatMarkdown';
import { STRINGS } from '@/constants/strings';
import type { SearchResultItem } from '@/types';

interface ResultDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: SearchResultItem | null;
}

/**
 * Displays full search result content in a modal dialog.
 * Features: scrollable content area, copy button, Esc/X/backdrop close.
 */
export function ResultDetailDialog({
  open,
  onOpenChange,
  result,
}: ResultDetailDialogProps) {
  const { copy, isCopying, isCopied } = useClipboard();

  if (!result) return null;

  const handleCopy = () => {
    const markdown = formatMarkdown(result);
    copy(markdown);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[560px] max-h-[80vh] flex flex-col overflow-hidden">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>
            {result.title} · p.{result.page}
          </DialogTitle>
          <DialogDescription className="sr-only">
            {result.title}{STRINGS.DIALOG_DESCRIPTION_SUFFIX}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-y-auto">
          <p className="text-sm whitespace-pre-wrap pr-2">{result.content}</p>
        </div>

        <div className="flex-shrink-0 flex items-center justify-between pt-4 border-t">
          <span className="text-sm text-muted-foreground">
            {Math.round((result.score ?? 0) * 100)}%
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={handleCopy}
              disabled={isCopying}
              aria-label={STRINGS.COPY_BUTTON_LABEL}
            >
              {isCopying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isCopied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              <span className="ml-2">
                {isCopying ? STRINGS.COPYING : isCopied ? STRINGS.COPIED : STRINGS.COPY}
              </span>
            </Button>
            <DialogClose asChild>
              <Button variant="outline" aria-label={STRINGS.DIALOG_CLOSE}>
                <X className="h-4 w-4" />
                <span className="ml-2">{STRINGS.DIALOG_CLOSE}</span>
              </Button>
            </DialogClose>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
