import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from '@/components/ui/command';
import { ScoreIndicator } from './ScoreIndicator';
import { useDebounce } from '@/hooks/useDebounce';
import { useSearch } from '@/hooks/useSearch';
import { useClipboard } from '@/hooks/useClipboard';
import { formatMarkdown } from '@/lib/formatMarkdown';
import { STRINGS } from '@/constants/strings';
import type { SearchResultItem } from '@/types';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Command Palette for quick search via ⌘K.
 * Provides real-time search with debounce, keyboard navigation,
 * and one-click markdown copy functionality.
 *
 * Uses useSearch hook for TanStack Query caching and consistent error handling.
 */
export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const { copy } = useClipboard();

  // Use TanStack Query via useSearch hook for caching and error handling
  const query = debouncedSearch.trim() || null;
  const { data, isFetching, isError } = useSearch(query);

  // Show error toast when search fails
  useEffect(() => {
    if (isError) {
      toast.error(STRINGS.SEARCH_ERROR);
    }
  }, [isError]);

  // Handle open state change with search reset
  const handleOpenChange = useCallback(
    (newOpen: boolean) => {
      if (!newOpen) {
        setSearch('');
      }
      onOpenChange(newOpen);
    },
    [onOpenChange]
  );

  const handleSelect = (result: SearchResultItem) => {
    const markdown = formatMarkdown(result);
    copy(markdown);
    handleOpenChange(false);
  };

  const results = data?.results ?? [];
  const hasSearched = query !== null;

  return (
    <CommandDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={STRINGS.COMMAND_PALETTE_TITLE}
      description={STRINGS.COMMAND_PALETTE_DESCRIPTION}
      showCloseButton={true}
    >
      <CommandInput
        placeholder={STRINGS.COMMAND_PALETTE_PLACEHOLDER}
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        {isFetching && (
          <div className="py-6 text-center text-sm text-muted-foreground">
            {STRINGS.COMMAND_PALETTE_LOADING}
          </div>
        )}
        {!isFetching && hasSearched && results.length === 0 && (
          <CommandEmpty>{STRINGS.COMMAND_PALETTE_EMPTY}</CommandEmpty>
        )}
        {!isFetching && results.length > 0 && (
          <CommandGroup>
            {results.map((result) => (
              <CommandItem
                key={`${result.book_id}-${result.page}`}
                value={`${result.title} ${result.content}`}
                onSelect={() => handleSelect(result)}
                className="flex flex-col items-start gap-1 py-3"
              >
                <div className="flex justify-between items-center w-full">
                  <div>
                    <span className="font-medium">{result.title}</span>
                    <span className="text-muted-foreground mx-2">·</span>
                    <span className="text-sm text-muted-foreground">
                      p.{result.page}
                    </span>
                  </div>
                  <ScoreIndicator score={result.score} />
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 w-full">
                  {result.content}
                </p>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  );
}
