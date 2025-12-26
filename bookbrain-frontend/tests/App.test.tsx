import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '@/App';
import { STRINGS } from '@/constants/strings';

// Mock the API client
vi.mock('@/api/client', () => ({
  searchBooks: vi.fn(),
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    code: string;
    details?: Record<string, unknown>;
    constructor(code: string, message: string, details?: Record<string, unknown>) {
      super(message);
      this.name = 'ApiError';
      this.code = code;
      this.details = details;
    }
  },
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the header with logo', () => {
    renderApp();
    expect(screen.getByText(STRINGS.APP_NAME)).toBeInTheDocument();
  });

  it('renders the search input with auto-focus', () => {
    renderApp();
    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveFocus();
  });

  it('does not show result list before search', () => {
    renderApp();
    // No loading or skeleton shown before search
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(
      screen.queryByText(STRINGS.SEARCH_NO_RESULTS)
    ).not.toBeInTheDocument();
  });

  it('shows loading then results after search', async () => {
    const { searchBooks } = await import('@/api/client');
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue({
      results: [
        {
          book_id: 1,
          title: '토비의 스프링',
          author: '이일민',
          page: 423,
          content: 'Spring Security는 인증...',
          score: 0.92,
        },
        {
          book_id: 2,
          title: '클린 코드',
          author: '로버트 마틴',
          page: 156,
          content: '함수는 한 가지를 해야 한다.',
          score: 0.87,
        },
      ],
      total: 2,
      query_time_ms: 234,
    });

    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
    });

    expect(screen.getByText('클린 코드')).toBeInTheDocument();
    // Should show search meta info
    expect(screen.getByText('2건, 0.23초')).toBeInTheDocument();
  });

  it('shows empty message when no results', async () => {
    const { searchBooks } = await import('@/api/client');
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue({
      results: [],
      total: 0,
      query_time_ms: 50,
    });

    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'nonexistent');
    await user.keyboard('{Enter}');

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText(STRINGS.SEARCH_NO_RESULTS)).toBeInTheDocument();
    });
    expect(screen.getByText(STRINGS.SEARCH_NO_RESULTS_HINT)).toBeInTheDocument();
  });

  it('has theme toggle button', () => {
    renderApp();
    expect(
      screen.getByRole('button', { name: /switch to/i })
    ).toBeInTheDocument();
  });

  it('shows toast when searching with empty query', async () => {
    const { toast } = await import('sonner');
    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    // Focus and press Enter without typing anything
    await user.click(searchInput);
    await user.keyboard('{Enter}');

    expect(toast.info).toHaveBeenCalledWith(STRINGS.SEARCH_EMPTY_QUERY);
  });

  it('shows toast when searching with whitespace only', async () => {
    const { toast } = await import('sonner');
    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, '   ');
    await user.keyboard('{Enter}');

    expect(toast.info).toHaveBeenCalledWith(STRINGS.SEARCH_EMPTY_QUERY);
  });

  it('shows error UI when search fails', async () => {
    const { searchBooks } = await import('@/api/client');
    (searchBooks as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Network error')
    );

    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    expect(screen.getByText(STRINGS.SEARCH_ERROR)).toBeInTheDocument();
    expect(screen.getByText(STRINGS.SEARCH_ERROR_HINT)).toBeInTheDocument();
  });

  it('opens detail dialog when result card is clicked', async () => {
    const { searchBooks } = await import('@/api/client');
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue({
      results: [
        {
          book_id: 1,
          title: '토비의 스프링',
          author: '이일민',
          page: 423,
          content: 'Spring Security는 인증과 권한 부여를 담당합니다.',
          score: 0.92,
        },
      ],
      total: 1,
      query_time_ms: 100,
    });

    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'Spring');
    await user.keyboard('{Enter}');

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
    });

    // Click on the result card
    const resultCard = screen.getByRole('article');
    await user.click(resultCard);

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Dialog should show full content (getAllByText since content appears in both card and dialog)
    const contentElements = screen.getAllByText(/Spring Security는 인증과 권한 부여를 담당합니다\./);
    expect(contentElements.length).toBeGreaterThanOrEqual(2); // One in card, one in dialog
  });

  it('closes detail dialog when Escape is pressed', async () => {
    const { searchBooks } = await import('@/api/client');
    (searchBooks as ReturnType<typeof vi.fn>).mockResolvedValue({
      results: [
        {
          book_id: 1,
          title: '토비의 스프링',
          author: '이일민',
          page: 423,
          content: 'Spring Security는 인증과 권한 부여를 담당합니다.',
          score: 0.92,
        },
      ],
      total: 1,
      query_time_ms: 100,
    });

    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'Spring');
    await user.keyboard('{Enter}');

    // Wait for results and click card
    await waitFor(() => {
      expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
    });

    const resultCard = screen.getByRole('article');
    await user.click(resultCard);

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Press Escape to close
    await user.keyboard('{Escape}');

    // Dialog should be closed
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
