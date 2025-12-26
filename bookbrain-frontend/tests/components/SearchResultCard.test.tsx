import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SearchResultCard } from '@/components/SearchResultCard';
import type { SearchResultItem } from '@/types';

// Mock useClipboard hook
vi.mock('@/hooks/useClipboard', () => ({
  useClipboard: () => ({
    copy: vi.fn(),
    isCopying: false,
    isCopied: false,
  }),
}));

const mockResult: SearchResultItem = {
  book_id: 1,
  title: 'Test Book',
  author: 'Test Author',
  page: 42,
  content: 'This is test content from the book.',
  score: 0.95,
};

describe('SearchResultCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AC1: 결과 카드 정보 표시', () => {
    it('renders book title (FR12)', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(screen.getByText('Test Book')).toBeInTheDocument();
    });

    it('renders page number (FR13)', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(screen.getByText('p.42')).toBeInTheDocument();
    });

    it('renders similarity score (FR14)', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(screen.getByText('0.95')).toBeInTheDocument();
    });

    it('renders content preview (FR15)', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(
        screen.getByText('This is test content from the book.')
      ).toBeInTheDocument();
    });
  });

  describe('AC2: 결과 카드 레이아웃', () => {
    it('displays title and page in correct format', () => {
      render(<SearchResultCard result={mockResult} />);

      // Title and page should be on same line with separator
      expect(screen.getByText('Test Book')).toBeInTheDocument();
      expect(screen.getByText('·')).toBeInTheDocument();
      expect(screen.getByText('p.42')).toBeInTheDocument();
    });

    it('displays score in top-right area', () => {
      render(<SearchResultCard result={mockResult} />);

      // ScoreIndicator should be present with correct score
      expect(screen.getByText('0.95')).toBeInTheDocument();
    });

    it('displays Copy button', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(
        screen.getByRole('button', { name: /마크다운으로 복사/i })
      ).toBeInTheDocument();
    });

    it('shows Copy text by default', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(screen.getByText('Copy')).toBeInTheDocument();
    });
  });

  describe('AC3: 결과 카드 hover 상태', () => {
    it('has hover style class', () => {
      render(<SearchResultCard result={mockResult} />);
      const card = screen.getByRole('article');
      expect(card).toHaveClass('hover:bg-muted/50');
    });

    it('has cursor-pointer for clickable indication', () => {
      render(<SearchResultCard result={mockResult} />);
      const card = screen.getByRole('article');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('has transition-colors for smooth hover effect', () => {
      render(<SearchResultCard result={mockResult} />);
      const card = screen.getByRole('article');
      expect(card).toHaveClass('transition-colors');
    });
  });

  describe('Click handling', () => {
    it('calls onClick when card is clicked', async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<SearchResultCard result={mockResult} onClick={onClick} />);

      await user.click(screen.getByRole('article'));
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('does not throw when clicked without onClick prop', async () => {
      const user = userEvent.setup();
      render(<SearchResultCard result={mockResult} />);

      // Should not throw
      await user.click(screen.getByRole('article'));
    });

    it('does not call onClick when Copy button is clicked', async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<SearchResultCard result={mockResult} onClick={onClick} />);

      await user.click(
        screen.getByRole('button', { name: /마크다운으로 복사/i })
      );
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard accessibility', () => {
    it('has tabIndex for keyboard focus', () => {
      render(<SearchResultCard result={mockResult} />);
      const card = screen.getByRole('article');
      expect(card).toHaveAttribute('tabindex', '0');
    });

    it('calls onClick when Enter key is pressed', async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<SearchResultCard result={mockResult} onClick={onClick} />);

      const card = screen.getByRole('article');
      card.focus();
      await user.keyboard('{Enter}');

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('calls onClick when Space key is pressed', async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<SearchResultCard result={mockResult} onClick={onClick} />);

      const card = screen.getByRole('article');
      card.focus();
      await user.keyboard(' ');

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('has focus-visible ring styles', () => {
      render(<SearchResultCard result={mockResult} />);
      const card = screen.getByRole('article');
      expect(card).toHaveClass('focus-visible:ring-2');
    });
  });

  describe('Content preview', () => {
    it('has line-clamp-3 for content truncation', () => {
      render(<SearchResultCard result={mockResult} />);
      const content = screen.getByText('This is test content from the book.');
      expect(content).toHaveClass('line-clamp-3');
    });

    it('renders long content', () => {
      const longContent = 'A'.repeat(500);
      const resultWithLongContent = { ...mockResult, content: longContent };
      render(<SearchResultCard result={resultWithLongContent} />);

      expect(screen.getByText(longContent)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="article"', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(screen.getByRole('article')).toBeInTheDocument();
    });

    it('Copy button has aria-label', () => {
      render(<SearchResultCard result={mockResult} />);
      expect(
        screen.getByRole('button', { name: '마크다운으로 복사' })
      ).toBeInTheDocument();
    });
  });

  describe('Korean content', () => {
    it('renders Korean title and content', () => {
      const koreanResult: SearchResultItem = {
        book_id: 1,
        title: '토비의 스프링',
        author: '이일민',
        page: 423,
        content:
          'Spring Security는 인증(Authentication)과 권한 부여(Authorization)를 담당하는 프레임워크입니다.',
        score: 0.92,
      };

      render(<SearchResultCard result={koreanResult} />);

      expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      expect(screen.getByText('p.423')).toBeInTheDocument();
      expect(screen.getByText(/Spring Security/)).toBeInTheDocument();
    });
  });
});
