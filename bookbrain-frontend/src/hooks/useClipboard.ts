import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { STRINGS } from '@/constants/strings';

interface UseClipboardReturn {
  copy: (text: string) => Promise<void>;
  isCopied: boolean;
}

/**
 * Hook for copying text to clipboard with toast feedback.
 * @param timeout - Time in ms to show "copied" state (default: 2000)
 */
export function useClipboard(timeout = 2000): UseClipboardReturn {
  const [isCopied, setIsCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup timeout on unmount to prevent memory leak
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const copy = useCallback(
    async (text: string) => {
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      try {
        await navigator.clipboard.writeText(text);
        setIsCopied(true);
        toast.success(STRINGS.TOAST_COPIED);

        timeoutRef.current = setTimeout(() => setIsCopied(false), timeout);
      } catch (error) {
        toast.error(STRINGS.TOAST_COPY_FAILED);
        console.error('Failed to copy:', error);
      }
    },
    [timeout]
  );

  return { copy, isCopied };
}
