import { Search } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { UploadDialog } from '@/components/UploadDialog';
import { Kbd } from '@/components/ui/kbd';
import { STRINGS } from '@/constants/strings';

interface HeaderProps {
  /** Open state for upload dialog */
  uploadDialogOpen?: boolean;
  /** Handler for upload dialog open state change */
  onUploadDialogOpenChange?: (open: boolean) => void;
  /** Handler for search shortcut click */
  onSearchClick?: () => void;
}

export function Header({
  uploadDialogOpen,
  onUploadDialogOpenChange,
  onSearchClick
}: HeaderProps = {}) {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-0 border-b border-border bg-background">
      <div className="flex items-center gap-2">
        <img src="/logo.png" alt="BookBrain" className="h-20 w-20" />
        <h1 className="text-xl font-semibold text-foreground">{STRINGS.APP_NAME}</h1>
      </div>
      <div className="flex items-center gap-2">
        {/* Search trigger - looks like a mini search input */}
        <button
          onClick={onSearchClick}
          className="hidden sm:flex h-9 items-center gap-2 rounded-md border border-input bg-background px-3 text-sm text-muted-foreground shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Open search (Cmd+K or Ctrl+K)"
        >
          <Search className="h-4 w-4" />
          <span className="hidden md:inline">검색...</span>
          <Kbd showModifier size="sm">K</Kbd>
        </button>
        <UploadDialog open={uploadDialogOpen} onOpenChange={onUploadDialogOpenChange} />
        <ThemeToggle />
      </div>
    </header>
  );
}
