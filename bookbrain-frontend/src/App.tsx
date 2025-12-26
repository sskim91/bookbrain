import { useState, useEffect } from 'react';
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

  const { data, isFetching, isError, error } = useSearch(searchQuery);

  // Handle error with toast
  useEffect(() => {
    if (isError && error) {
      toast.error(STRINGS.SEARCH_ERROR);
    }
  }, [isError, error]);

  // Global ⌘K keyboard shortcut handler with focus guard
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        // Focus guard: skip if in contenteditable or textarea to avoid conflicts
        const target = e.target as HTMLElement;
        const isContentEditable = target.isContentEditable;
        const isTextarea = target.tagName === 'TEXTAREA';

        if (isContentEditable || isTextarea) {
          return;
        }

        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
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
    <MainLayout>
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
