import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, Check } from 'lucide-react';
import { ScoreIndicator } from './ScoreIndicator';
import { useClipboard } from '@/hooks/useClipboard';
import { formatMarkdown } from '@/lib/formatMarkdown';
import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';

interface SearchResultCardProps {
  result: SearchResultItem;
  onClick?: () => void;
}

/**
 * Displays a single search result with title, page, score, content preview, and copy button.
 * Clicking the card triggers onClick (for detail dialog in Story 2.5).
 * Clicking the Copy button copies markdown to clipboard without triggering card click.
 */
export function SearchResultCard({ result, onClick }: SearchResultCardProps) {
  const { copy, isCopied } = useClipboard();

  const handleCopy = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation(); // Prevent card click for both mouse and keyboard events
    const markdown = formatMarkdown(result);
    copy(markdown);
  };

  const handleCopyKeyDown = (e: React.KeyboardEvent) => {
    // Prevent card click when Copy button is activated via keyboard
    if (e.key === 'Enter' || e.key === ' ') {
      e.stopPropagation();
    }
  };

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    }
  };

  const handleCardKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCardClick();
    }
  };

  return (
    <Card
      className="p-5 cursor-pointer hover:bg-muted/50 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 outline-none"
      onClick={handleCardClick}
      onKeyDown={handleCardKeyDown}
      role="article"
      tabIndex={0}
    >
      <div className="flex justify-between items-start gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <span className="font-medium block truncate" title={result.title}>
            {result.title}
          </span>
          <span className="text-sm text-muted-foreground">p.{result.page}</span>
        </div>
        <ScoreIndicator score={result.score} />
      </div>

      <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
        {result.content}
      </p>

      <div className="flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          onKeyDown={handleCopyKeyDown}
          aria-label={STRINGS.COPY_BUTTON_LABEL}
        >
          {isCopied ? (
            <Check className="h-4 w-4 text-green-500" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
          <span className="ml-2">
            {isCopied ? STRINGS.COPIED : STRINGS.COPY}
          </span>
        </Button>
      </div>
    </Card>
  );
}
