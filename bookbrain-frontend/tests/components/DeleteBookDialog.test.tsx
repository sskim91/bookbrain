import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteBookDialog } from '@/components/DeleteBookDialog';
import { STRINGS } from '@/constants/strings';

describe('DeleteBookDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    bookTitle: '토비의 스프링',
    onConfirm: vi.fn(),
    isDeleting: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders dialog title', () => {
      render(<DeleteBookDialog {...defaultProps} />);

      expect(screen.getByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).toBeInTheDocument();
    });

    it('renders book title in description', () => {
      render(<DeleteBookDialog {...defaultProps} />);

      expect(
        screen.getByText(STRINGS.BOOK_DELETE_DIALOG_DESCRIPTION('토비의 스프링'))
      ).toBeInTheDocument();
    });

    it('renders cancel and confirm buttons', () => {
      render(<DeleteBookDialog {...defaultProps} />);

      expect(screen.getByText(STRINGS.BOOK_DELETE_CANCEL)).toBeInTheDocument();
      expect(screen.getByText(STRINGS.BOOK_DELETE_CONFIRM)).toBeInTheDocument();
    });
  });

  describe('interactions', () => {
    it('calls onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();

      render(<DeleteBookDialog {...defaultProps} onConfirm={onConfirm} />);

      await user.click(screen.getByText(STRINGS.BOOK_DELETE_CONFIRM));

      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    it('calls onOpenChange when cancel button is clicked', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      render(<DeleteBookDialog {...defaultProps} onOpenChange={onOpenChange} />);

      await user.click(screen.getByText(STRINGS.BOOK_DELETE_CANCEL));

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('loading state', () => {
    it('shows loading text when isDeleting is true', () => {
      render(<DeleteBookDialog {...defaultProps} isDeleting={true} />);

      expect(screen.getByText(STRINGS.BOOK_DELETE_IN_PROGRESS)).toBeInTheDocument();
    });

    it('disables buttons when isDeleting is true', () => {
      render(<DeleteBookDialog {...defaultProps} isDeleting={true} />);

      expect(screen.getByText(STRINGS.BOOK_DELETE_CANCEL)).toBeDisabled();
      expect(screen.getByText(STRINGS.BOOK_DELETE_IN_PROGRESS)).toBeDisabled();
    });
  });

  describe('closed state', () => {
    it('does not render content when open is false', () => {
      render(<DeleteBookDialog {...defaultProps} open={false} />);

      expect(screen.queryByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).not.toBeInTheDocument();
    });
  });
});
