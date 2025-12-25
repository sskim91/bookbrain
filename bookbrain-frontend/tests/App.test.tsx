import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '@/App';
import { STRINGS } from '@/constants/strings';

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
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
    // No loading or empty message shown before search
    expect(screen.queryByText(STRINGS.SEARCH_LOADING)).not.toBeInTheDocument();
    expect(
      screen.queryByText(STRINGS.SEARCH_NO_RESULTS)
    ).not.toBeInTheDocument();
  });

  it('shows loading then results after search', async () => {
    const user = userEvent.setup();
    renderApp();

    const searchInput = screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER);
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    // Should show loading state
    expect(screen.getByText(STRINGS.SEARCH_LOADING)).toBeInTheDocument();

    // Wait for loading to complete (mock 500ms delay)
    await waitFor(
      () => {
        expect(screen.queryByText(STRINGS.SEARCH_LOADING)).not.toBeInTheDocument();
      },
      { timeout: 1000 }
    );

    // Should show dummy results for UI testing
    expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
    expect(screen.getByText('클린 코드')).toBeInTheDocument();
    expect(screen.getByText('도메인 주도 설계')).toBeInTheDocument();
  });

  it('has theme toggle button', () => {
    renderApp();
    expect(
      screen.getByRole('button', { name: /switch to/i })
    ).toBeInTheDocument();
  });
});
