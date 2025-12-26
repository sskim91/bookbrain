import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  SearchResultSkeleton,
  SearchResultSkeletonList,
} from '@/components/SearchResultSkeleton';

describe('SearchResultSkeleton', () => {
  it('renders a skeleton card', () => {
    const { container } = render(<SearchResultSkeleton />);

    // Should have Card wrapper
    expect(container.querySelector('[data-slot="card"]')).toBeInTheDocument();

    // Should have multiple skeleton elements
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('has same structure as SearchResultCard', () => {
    const { container } = render(<SearchResultSkeleton />);

    // Title skeleton area
    expect(container.querySelector('.h-5.w-48')).toBeInTheDocument();

    // Score skeleton area
    expect(container.querySelector('.h-4.w-10')).toBeInTheDocument();

    // Content skeleton lines
    expect(container.querySelector('.h-4.w-full')).toBeInTheDocument();
    expect(container.querySelector('.h-4.w-3\\/4')).toBeInTheDocument();

    // Copy button skeleton
    expect(container.querySelector('.h-8.w-20')).toBeInTheDocument();
  });

  it('has p-5 padding matching SearchResultCard', () => {
    const { container } = render(<SearchResultSkeleton />);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveClass('p-5');
  });
});

describe('SearchResultSkeletonList', () => {
  it('renders 3 skeleton cards by default', () => {
    const { container } = render(<SearchResultSkeletonList />);

    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards).toHaveLength(3);
  });

  it('renders custom number of skeleton cards', () => {
    const { container } = render(<SearchResultSkeletonList count={5} />);

    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards).toHaveLength(5);
  });

  it('has role="status" for accessibility', () => {
    render(<SearchResultSkeletonList />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has aria-label for screen readers', () => {
    render(<SearchResultSkeletonList />);
    expect(screen.getByLabelText('검색 결과 로딩 중')).toBeInTheDocument();
  });

  it('has max-w-[800px] matching SearchResultList', () => {
    const { container } = render(<SearchResultSkeletonList />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('max-w-[800px]');
  });

  it('has gap-3 spacing matching SearchResultList', () => {
    const { container } = render(<SearchResultSkeletonList />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('gap-3');
  });
});
