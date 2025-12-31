import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useClipboard } from '@/hooks/useClipboard';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('useClipboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns copy function and state values', () => {
    const { result } = renderHook(() => useClipboard());

    expect(result.current.copy).toBeDefined();
    expect(typeof result.current.copy).toBe('function');
    expect(result.current.isCopied).toBe(false);
  });

  it('copies text to clipboard', async () => {
    const { result } = renderHook(() => useClipboard());

    await act(async () => {
      await result.current.copy('test text');
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test text');
  });

  it('sets isCopied to true after copy', async () => {
    const { result } = renderHook(() => useClipboard());

    expect(result.current.isCopied).toBe(false);

    await act(async () => {
      await result.current.copy('test');
    });

    expect(result.current.isCopied).toBe(true);
  });

  it('resets isCopied after timeout', async () => {
    const { result } = renderHook(() => useClipboard(1000));

    await act(async () => {
      await result.current.copy('test');
    });

    expect(result.current.isCopied).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(result.current.isCopied).toBe(false);
  });

  it('shows success toast on copy', async () => {
    const { toast } = await import('sonner');
    const { result } = renderHook(() => useClipboard());

    await act(async () => {
      await result.current.copy('test');
    });

    expect(toast.success).toHaveBeenCalled();
  });

  it('shows error toast on clipboard failure', async () => {
    const { toast } = await import('sonner');
    (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Clipboard not available')
    );

    const { result } = renderHook(() => useClipboard());

    await act(async () => {
      await result.current.copy('test');
    });

    expect(toast.error).toHaveBeenCalled();
    expect(result.current.isCopied).toBe(false);
  });

  it('uses custom timeout', async () => {
    const { result } = renderHook(() => useClipboard(500));

    await act(async () => {
      await result.current.copy('test');
    });

    expect(result.current.isCopied).toBe(true);

    act(() => {
      vi.advanceTimersByTime(499);
    });
    expect(result.current.isCopied).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current.isCopied).toBe(false);
  });
});
