import { ThemeToggle } from '@/components/ThemeToggle';
import { STRINGS } from '@/constants/strings';

export function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border">
      <h1 className="text-xl font-semibold text-foreground">{STRINGS.APP_NAME}</h1>
      <ThemeToggle />
    </header>
  );
}
