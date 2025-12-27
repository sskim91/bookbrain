import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from '@/components/Header';
import { STRINGS } from '@/constants/strings';
import React from 'react';

// Mock the books API to prevent actual network calls
vi.mock('@/api/books', () => ({
  uploadBook: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
};

const renderWithWrapper = (ui: React.ReactElement) => {
  return render(ui, { wrapper: createWrapper() });
};

describe('Header', () => {
  it('renders the logo text', () => {
    renderWithWrapper(<Header />);
    expect(screen.getByText(STRINGS.APP_NAME)).toBeInTheDocument();
  });

  it('renders the theme toggle button', () => {
    renderWithWrapper(<Header />);
    // Theme toggle button has aria-label
    expect(
      screen.getByRole('button', { name: /switch to/i })
    ).toBeInTheDocument();
  });

  it('uses semantic header element', () => {
    renderWithWrapper(<Header />);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});
