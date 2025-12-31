import { cn } from '@/lib/utils';
import { useModifierKey } from '@/hooks/useOS';

interface KbdProps {
  /** The key to display (e.g., 'K', 'U') */
  children: React.ReactNode;
  /** Show modifier key (⌘ on Mac, Ctrl on Windows) */
  showModifier?: boolean;
  /** Size variant */
  size?: 'sm' | 'default';
  /** Additional CSS classes */
  className?: string;
  /** Hide from screen readers (when parent already has aria-label) */
  'aria-hidden'?: boolean;
}

/**
 * Keyboard shortcut display component.
 * Automatically shows ⌘ on macOS and Ctrl on Windows/Linux.
 *
 * @example
 * <Kbd showModifier>K</Kbd>  // Shows "⌘K" on Mac, "Ctrl+K" on Windows
 * <Kbd>Enter</Kbd>           // Shows "Enter"
 */
export function Kbd({ children, showModifier = false, size = 'default', className, 'aria-hidden': ariaHidden = true }: KbdProps) {
  const modifier = useModifierKey();

  return (
    <kbd
      aria-hidden={ariaHidden}
      className={cn(
        'pointer-events-none inline-flex select-none items-center gap-0.5 rounded border bg-muted font-mono font-medium text-muted-foreground',
        size === 'sm' ? 'h-5 px-1 text-[10px]' : 'h-6 px-1.5 text-xs',
        className
      )}
    >
      {showModifier && (
        <>
          <span>{modifier}</span>
          {modifier !== '⌘' && <span>+</span>}
        </>
      )}
      <span>{children}</span>
    </kbd>
  );
}
