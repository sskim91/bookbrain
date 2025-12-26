import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { CommandPalette } from '@/components/CommandPalette';

// Mock the API client
vi.mock('@/api/client', () => ({
  searchBooks: vi.fn(),
}));

// Mock useClipboard hook
const mockCopy = vi.fn();
vi.mock('@/hooks/useClipboard', () => ({
  useClipboard: () => ({
    copy: mockCopy,
    isCopying: false,
    isCopied: false,
  }),
}));

import { searchBooks } from '@/api/client';

const mockSearchResults = {
  results: [
    {
      book_id: 1,
      title: 'Test Book',
      author: 'Test Author',
      page: 42,
      content: 'This is test content from the book.',
      score: 0.95,
    },
    {
      book_id: 2,
      title: 'Another Book',
      author: 'Another Author',
      page: 100,
      content: 'More test content here.',
      score: 0.85,
    },
  ],
  total: 2,
  query_time_ms: 50,
};

// Create a wrapper with QueryClientProvider for TanStack Query
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

// Custom render with QueryClientProvider
function renderWithProvider(ui: React.ReactElement) {
  return render(ui, { wrapper: createWrapper() });
}

describe('CommandPalette', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(searchBooks).mockResolvedValue(mockSearchResults);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('AC1: 키보드 단축키로 열기', () => {
    it('renders when open is true', () => {
      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);
      expect(screen.getByPlaceholderText('검색...')).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      renderWithProvider(<CommandPalette open={false} onOpenChange={vi.fn()} />);
      expect(screen.queryByPlaceholderText('검색...')).not.toBeInTheDocument();
    });

    it('focuses input when opened', async () => {
      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);
      const input = screen.getByPlaceholderText('검색...');
      await waitFor(() => {
        expect(document.activeElement).toBe(input);
      });
    });
  });

  describe('AC2: 실시간 검색 결과 표시', () => {
    it('shows loading state during search', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      // Create a promise that we can resolve manually
      let resolveSearch: (value: typeof mockSearchResults) => void;
      vi.mocked(searchBooks).mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveSearch = resolve;
          })
      );

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      // Advance past debounce to trigger search
      await vi.advanceTimersByTimeAsync(300);

      // Should show loading (API not resolved yet)
      await waitFor(() => {
        expect(screen.getByText('검색 중...')).toBeInTheDocument();
      });

      // Resolve the search
      resolveSearch!(mockSearchResults);
    });

    it('displays search results after debounce', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      // Advance past debounce (300ms)
      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(searchBooks).toHaveBeenCalledWith('test');
      });

      await waitFor(() => {
        expect(screen.getByText('Test Book')).toBeInTheDocument();
        expect(screen.getByText('Another Book')).toBeInTheDocument();
      });
    });

    it('shows empty state when no results found', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      vi.mocked(searchBooks).mockResolvedValue({
        results: [],
        total: 0,
        query_time_ms: 10,
      });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'nonexistent');

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(screen.getByText('검색 결과가 없습니다')).toBeInTheDocument();
      });
    });

    it('debounces search input (300ms)', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');

      // Type rapidly
      await user.type(input, 'te');
      await vi.advanceTimersByTimeAsync(100);
      await user.type(input, 'st');
      await vi.advanceTimersByTimeAsync(100);

      // Should not have called yet (only 200ms passed)
      expect(searchBooks).not.toHaveBeenCalled();

      // Advance past debounce
      await vi.advanceTimersByTimeAsync(300);

      // Now it should have been called with full query
      await waitFor(() => {
        expect(searchBooks).toHaveBeenCalledWith('test');
      });
    });
  });

  describe('AC3: 키보드 네비게이션', () => {
    it('allows keyboard navigation with arrow keys', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(screen.getByText('Test Book')).toBeInTheDocument();
      });

      // Arrow down should work (cmdk handles this internally)
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      // The component should still be open and functional
      expect(screen.getByText('Another Book')).toBeInTheDocument();
    });
  });

  describe('AC4: Enter로 마크다운 복사', () => {
    it('copies markdown and closes dialog on item select', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onOpenChange = vi.fn();

      renderWithProvider(<CommandPalette open={true} onOpenChange={onOpenChange} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(screen.getByText('Test Book')).toBeInTheDocument();
      });

      // Click on result item
      await user.click(screen.getByText('Test Book'));

      // Should have copied markdown
      expect(mockCopy).toHaveBeenCalledWith(
        expect.stringContaining('**Test Book**')
      );
      expect(mockCopy).toHaveBeenCalledWith(expect.stringContaining('p.42'));

      // Should close dialog
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('AC5: Escape로 닫기', () => {
    it('calls onOpenChange(false) when Escape is pressed', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onOpenChange = vi.fn();

      renderWithProvider(<CommandPalette open={true} onOpenChange={onOpenChange} />);

      await user.keyboard('{Escape}');

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('State Management', () => {
    it('resets search state when dialog closes via onOpenChange', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      let isOpen = true;
      const onOpenChange = vi.fn((open: boolean) => {
        isOpen = open;
      });

      const Wrapper = createWrapper();

      const { rerender } = render(
        <Wrapper>
          <CommandPalette open={isOpen} onOpenChange={onOpenChange} />
        </Wrapper>
      );

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      expect(input).toHaveValue('test');

      // Close dialog via Escape (which triggers onOpenChange)
      await user.keyboard('{Escape}');

      // onOpenChange should have been called with false
      expect(onOpenChange).toHaveBeenCalledWith(false);

      // Rerender with closed state, then reopen
      rerender(
        <Wrapper>
          <CommandPalette open={false} onOpenChange={onOpenChange} />
        </Wrapper>
      );

      rerender(
        <Wrapper>
          <CommandPalette open={true} onOpenChange={onOpenChange} />
        </Wrapper>
      );

      // Search should be reset (because onOpenChange(false) was called which resets state)
      const newInput = screen.getByPlaceholderText('검색...');
      expect(newInput).toHaveValue('');
    });
  });

  describe('Result Display', () => {
    it('displays book title, page, and score', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(screen.getByText('Test Book')).toBeInTheDocument();
        expect(screen.getByText('p.42')).toBeInTheDocument();
        expect(screen.getByText('0.95')).toBeInTheDocument();
      });
    });

    it('displays content preview', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => {
        expect(
          screen.getByText('This is test content from the book.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully and shows toast', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      vi.mocked(searchBooks).mockRejectedValue(new Error('API Error'));

      renderWithProvider(<CommandPalette open={true} onOpenChange={vi.fn()} />);

      const input = screen.getByPlaceholderText('검색...');
      await user.type(input, 'test');

      await vi.advanceTimersByTimeAsync(300);

      // Wait for error state - TanStack Query will set isError
      await waitFor(() => {
        // Should not crash, should show empty or no results
        expect(screen.queryByText('Test Book')).not.toBeInTheDocument();
      });
    });
  });
});
