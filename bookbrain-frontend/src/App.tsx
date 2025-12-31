import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { MainLayout } from '@/components/MainLayout';
import { SearchInput } from '@/components/SearchInput';
import { SearchResultList } from '@/components/SearchResultList';
import { ResultDetailDialog } from '@/components/ResultDetailDialog';
import { CommandPalette } from '@/components/CommandPalette';
import { useSearch } from '@/hooks/useSearch';
import { STRINGS } from '@/constants/strings';
import type { SearchResultItem } from '@/types';

function App() {
  const [inputValue, setInputValue] = useState('');
  const [searchQuery, setSearchQuery] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResultItem | null>(null);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  const { data, isFetching, isError, error } = useSearch(searchQuery);

  // Handle error with toast
  useEffect(() => {
    if (isError && error) {
      toast.error(STRINGS.SEARCH_ERROR);
    }
  }, [isError, error]);

  // Global keyboard shortcuts handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const hasModifier = e.metaKey || e.ctrlKey;

      // Global shortcuts with modifier keys work everywhere (including inputs)
      // ⌘K / Ctrl+K - Open command palette
      if (e.key === 'k' && hasModifier) {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
        return;
      }

      // ⌘U / Ctrl+U - Open upload dialog
      if (e.key === 'u' && hasModifier) {
        e.preventDefault();
        setUploadDialogOpen((prev) => !prev);
        return;
      }

      // For non-modifier shortcuts, apply focus guard
      // (currently none, but ready for future shortcuts like Escape)
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearchClick = useCallback(() => {
    setCommandPaletteOpen(true);
  }, []);

  const handleSearch = () => {
    const trimmedQuery = inputValue.trim();
    if (!trimmedQuery) {
      toast.info(STRINGS.SEARCH_EMPTY_QUERY);
      return;
    }

    // Guard: prevent duplicate requests while search is fetching
    if (isFetching) return;

    setSearchQuery(trimmedQuery);
  };

  return (
    <MainLayout
      uploadDialogOpen={uploadDialogOpen}
      onUploadDialogOpenChange={setUploadDialogOpen}
      onSearchClick={handleSearchClick}
    >
      <div className="w-full max-w-[800px] flex flex-col items-center pt-16">
        <SearchInput
          value={inputValue}
          onChange={setInputValue}
          onSearch={handleSearch}
          isLoading={isFetching}
          autoFocus={true}
        />
        <SearchResultList
          results={isError ? [] : (data?.results ?? [])}
          isLoading={isFetching}
          isError={isError}
          hasSearched={searchQuery !== null}
          total={data?.total}
          queryTimeMs={data?.query_time_ms}
          onResultClick={setSelectedResult}
        />
      </div>

      <ResultDetailDialog
        open={selectedResult !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedResult(null);
        }}
        result={selectedResult}
      />

      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
      />
    </MainLayout>
  );
}

export default App;
