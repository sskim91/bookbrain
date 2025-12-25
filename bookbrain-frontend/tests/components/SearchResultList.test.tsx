import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { SearchResultList } from '@/components/SearchResultList';
import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';

// Mock useClipboard hook
vi.mock('@/hooks/useClipboard', () => ({
  useClipboard: () => ({
    copy: vi.fn(),
    isCopying: false,
    isCopied: false,
  }),
}));

describe('SearchResultList', () => {
  it('renders nothing before search (hasSearched=false)', () => {
    const { container } = render(
      <SearchResultList results={[]} hasSearched={false} isLoading={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('shows loading state when isLoading is true', () => {
    render(
      <SearchResultList results={[]} hasSearched={true} isLoading={true} />
    );
    expect(screen.getByText(STRINGS.SEARCH_LOADING)).toBeInTheDocument();
  });

  it('shows empty message when no results after search', () => {
    render(
      <SearchResultList results={[]} hasSearched={true} isLoading={false} />
    );
    expect(screen.getByText(STRINGS.SEARCH_NO_RESULTS)).toBeInTheDocument();
  });

  it('renders results using SearchResultCard components', () => {
    const mockResults: SearchResultItem[] = [
      {
        book_id: 1,
        title: 'Test Book',
        author: 'Test Author',
        page: 42,
        content: 'This is test content from the book.',
        score: 0.95,
      },
    ];

    render(
      <SearchResultList
        results={mockResults}
        hasSearched={true}
        isLoading={false}
      />
    );

    // SearchResultCard renders these elements
    expect(screen.getByText('Test Book')).toBeInTheDocument();
    expect(screen.getByText('p.42')).toBeInTheDocument();
    expect(
      screen.getByText('This is test content from the book.')
    ).toBeInTheDocument();
    expect(screen.getByText('0.95')).toBeInTheDocument(); // Score from ScoreIndicator
  });

  it('renders multiple results with SearchResultCard', () => {
    const mockResults: SearchResultItem[] = [
      {
        book_id: 1,
        title: 'First Book',
        author: null,
        page: 10,
        content: 'First content',
        score: 0.9,
      },
      {
        book_id: 2,
        title: 'Second Book',
        author: 'Author',
        page: 20,
        content: 'Second content',
        score: 0.8,
      },
    ];

    render(
      <SearchResultList
        results={mockResults}
        hasSearched={true}
        isLoading={false}
      />
    );

    expect(screen.getByText('First Book')).toBeInTheDocument();
    expect(screen.getByText('Second Book')).toBeInTheDocument();
    // Check that each card has a Copy button
    expect(screen.getAllByRole('button', { name: /복사/i })).toHaveLength(2);
  });

  it('calls onResultClick when a card is clicked', async () => {
    const user = userEvent.setup();
    const onResultClick = vi.fn();
    const mockResults: SearchResultItem[] = [
      {
        book_id: 1,
        title: 'Click Test Book',
        author: null,
        page: 1,
        content: 'Content',
        score: 0.5,
      },
    ];

    render(
      <SearchResultList
        results={mockResults}
        hasSearched={true}
        isLoading={false}
        onResultClick={onResultClick}
      />
    );

    await user.click(screen.getByRole('article'));
    expect(onResultClick).toHaveBeenCalledWith(mockResults[0]);
  });

  it('renders results with gap-3 spacing', () => {
    const mockResults: SearchResultItem[] = [
      {
        book_id: 1,
        title: 'First',
        author: null,
        page: 1,
        content: 'Content',
        score: 0.5,
      },
      {
        book_id: 2,
        title: 'Second',
        author: null,
        page: 2,
        content: 'Content',
        score: 0.5,
      },
    ];

    const { container } = render(
      <SearchResultList
        results={mockResults}
        hasSearched={true}
        isLoading={false}
      />
    );

    const listContainer = container.querySelector('.gap-3');
    expect(listContainer).toBeInTheDocument();
  });

  it('each card has role="article"', () => {
    const mockResults: SearchResultItem[] = [
      {
        book_id: 1,
        title: 'Test',
        author: null,
        page: 1,
        content: 'Content',
        score: 0.5,
      },
    ];

    render(
      <SearchResultList
        results={mockResults}
        hasSearched={true}
        isLoading={false}
      />
    );

    expect(screen.getByRole('article')).toBeInTheDocument();
  });
});
