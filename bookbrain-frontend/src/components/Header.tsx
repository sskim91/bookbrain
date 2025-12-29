import { ThemeToggle } from '@/components/ThemeToggle';
import { UploadDialog } from '@/components/UploadDialog';
import { STRINGS } from '@/constants/strings';

export function Header() {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-0 border-b border-border bg-background">
      <div className="flex items-center gap-2">
        <img src="/logo.png" alt="BookBrain" className="h-20 w-20" />
        <h1 className="text-xl font-semibold text-foreground">{STRINGS.APP_NAME}</h1>
      </div>
      <div className="flex items-center gap-2">
        <UploadDialog />
        <ThemeToggle />
      </div>
    </header>
  );
}
