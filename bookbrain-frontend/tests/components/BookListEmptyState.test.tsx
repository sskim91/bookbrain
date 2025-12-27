import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BookListEmptyState } from '@/components/BookListEmptyState';
import { STRINGS } from '@/constants/strings';

describe('BookListEmptyState', () => {
  it('renders empty state message', () => {
    render(<BookListEmptyState />);

    expect(screen.getByText(STRINGS.BOOK_LIST_EMPTY_TITLE)).toBeInTheDocument();
    expect(
      screen.getByText(STRINGS.BOOK_LIST_EMPTY_DESCRIPTION)
    ).toBeInTheDocument();
  });

  it('has correct aria label for accessibility', () => {
    render(<BookListEmptyState />);

    expect(
      screen.getByRole('status', { name: STRINGS.BOOK_LIST_EMPTY_TITLE })
    ).toBeInTheDocument();
  });

  it('renders book icon', () => {
    const { container } = render(<BookListEmptyState />);

    // Check for the lucide icon (SVG)
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
