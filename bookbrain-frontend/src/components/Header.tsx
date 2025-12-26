import { ThemeToggle } from '@/components/ThemeToggle';
import { UploadDialog } from '@/components/UploadDialog';
import { STRINGS } from '@/constants/strings';

export function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border">
      <h1 className="text-xl font-semibold text-foreground">{STRINGS.APP_NAME}</h1>
      <div className="flex items-center gap-2">
        <UploadDialog />
        <ThemeToggle />
      </div>
    </header>
  );
}
