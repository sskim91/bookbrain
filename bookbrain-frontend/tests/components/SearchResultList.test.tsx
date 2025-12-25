import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SearchResultList } from '@/components/SearchResultList';
import type { SearchResultItem } from '@/types';
import { STRINGS } from '@/constants/strings';

describe('SearchResultList', () => {
  it('renders nothing before search (hasSearched=false)', () => {
    const { container } = render(
      <SearchResultList results={[]} hasSearched={false} isLoading={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('shows loading state when isLoading is true', () => {
    render(<SearchResultList results={[]} hasSearched={true} isLoading={true} />);
    expect(screen.getByText(STRINGS.SEARCH_LOADING)).toBeInTheDocument();
  });

  it('shows empty message when no results after search', () => {
    render(<SearchResultList results={[]} hasSearched={true} isLoading={false} />);
    expect(
      screen.getByText(STRINGS.SEARCH_NO_RESULTS)
    ).toBeInTheDocument();
  });

  it('renders results when provided', () => {
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
      <SearchResultList results={mockResults} hasSearched={true} isLoading={false} />
    );

    expect(screen.getByText('Test Book')).toBeInTheDocument();
    expect(screen.getByText('p.42')).toBeInTheDocument();
    expect(
      screen.getByText('This is test content from the book.')
    ).toBeInTheDocument();
  });

  it('renders multiple results', () => {
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
      <SearchResultList results={mockResults} hasSearched={true} isLoading={false} />
    );

    expect(screen.getByText('First Book')).toBeInTheDocument();
    expect(screen.getByText('Second Book')).toBeInTheDocument();
  });
});
