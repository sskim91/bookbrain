import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BookList } from '@/components/BookList';
import * as booksApi from '@/api/books';
import { STRINGS } from '@/constants/strings';

// Mock the books API
vi.mock('@/api/books', () => ({
  getBooks: vi.fn(),
  uploadBook: vi.fn(),
  deleteBook: vi.fn(),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
};

describe('BookList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('loading state', () => {
    it('shows skeleton while loading', () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<BookList />, { wrapper: createWrapper() });

      expect(
        screen.getByLabelText(STRINGS.BOOK_LIST_LOADING)
      ).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('shows empty state when no books', async () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue({ books: [], total: 0 });

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(STRINGS.BOOK_LIST_EMPTY_TITLE)
        ).toBeInTheDocument();
      });
    });
  });

  describe('book list', () => {
    it('renders book list with title and count', async () => {
      const mockBooks = {
        books: [
          {
            id: 1,
            title: '토비의 스프링',
            author: '이일민',
            file_path: '/path/to/spring.pdf',
            total_pages: 423,
            embedding_model: 'text-embedding-3-small',
            created_at: '2025-12-25T10:00:00Z',
          },
          {
            id: 2,
            title: '클린 코드',
            author: 'Robert C. Martin',
            file_path: '/path/to/clean.pdf',
            total_pages: 312,
            embedding_model: 'text-embedding-3-small',
            created_at: '2025-12-23T10:00:00Z',
          },
        ],
        total: 2,
      };

      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(STRINGS.BOOK_LIST_TITLE(2))
        ).toBeInTheDocument();
      });

      expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      expect(screen.getByText('클린 코드')).toBeInTheDocument();
    });

    it('displays page count for each book', async () => {
      const mockBooks = {
        books: [
          {
            id: 1,
            title: 'Test Book',
            author: null,
            file_path: '/path/to/test.pdf',
            total_pages: 100,
            embedding_model: null,
            created_at: '2025-12-27T10:00:00Z',
          },
        ],
        total: 1,
      };

      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/100p/)).toBeInTheDocument();
      });
    });

    it('sorts books by created_at descending (most recent first)', async () => {
      const mockBooks = {
        books: [
          {
            id: 1,
            title: 'Older Book',
            author: null,
            file_path: '/path/to/older.pdf',
            total_pages: 100,
            embedding_model: null,
            created_at: '2025-12-20T10:00:00Z',
          },
          {
            id: 2,
            title: 'Newer Book',
            author: null,
            file_path: '/path/to/newer.pdf',
            total_pages: 200,
            embedding_model: null,
            created_at: '2025-12-27T10:00:00Z',
          },
        ],
        total: 2,
      };

      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Newer Book')).toBeInTheDocument();
      });

      // Check order: Newer Book should appear before Older Book
      const bookItems = screen.getAllByRole('article');
      expect(bookItems[0]).toHaveAttribute('aria-label', 'Newer Book');
      expect(bookItems[1]).toHaveAttribute('aria-label', 'Older Book');
    });
  });

  describe('error state', () => {
    it('shows error message on API error', async () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockRejectedValue(new Error('Network error'));

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(STRINGS.BOOK_LIST_ERROR)).toBeInTheDocument();
      });
    });
  });

  describe('delete functionality', () => {
    const mockBooks = {
      books: [
        {
          id: 1,
          title: '토비의 스프링',
          author: '이일민',
          file_path: '/path/to/spring.pdf',
          total_pages: 423,
          embedding_model: 'text-embedding-3-small',
          created_at: '2025-12-25T10:00:00Z',
        },
      ],
      total: 1,
    };

    it('shows delete button on hover', async () => {
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      });

      // Delete button should exist (though may be hidden via CSS)
      const deleteButton = screen.getByLabelText(STRINGS.BOOK_DELETE_BUTTON_ARIA_LABEL);
      expect(deleteButton).toBeInTheDocument();
    });

    it('shows confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      });

      const deleteButton = screen.getByLabelText(STRINGS.BOOK_DELETE_BUTTON_ARIA_LABEL);
      await user.click(deleteButton);

      // Confirmation dialog should appear
      await waitFor(() => {
        expect(screen.getByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).toBeInTheDocument();
      });

      expect(
        screen.getByText(STRINGS.BOOK_DELETE_DIALOG_DESCRIPTION('토비의 스프링'))
      ).toBeInTheDocument();
    });

    it('closes dialog when cancel is clicked', async () => {
      const user = userEvent.setup();
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      mockGetBooks.mockResolvedValue(mockBooks);

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      });

      // Open dialog
      const deleteButton = screen.getByLabelText(STRINGS.BOOK_DELETE_BUTTON_ARIA_LABEL);
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).toBeInTheDocument();
      });

      // Click cancel
      const cancelButton = screen.getByText(STRINGS.BOOK_DELETE_CANCEL);
      await user.click(cancelButton);

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).not.toBeInTheDocument();
      });
    });

    it('calls deleteBook API when confirm is clicked', async () => {
      const user = userEvent.setup();
      const mockGetBooks = vi.mocked(booksApi.getBooks);
      const mockDeleteBook = vi.mocked(booksApi.deleteBook);
      mockGetBooks.mockResolvedValue(mockBooks);
      mockDeleteBook.mockResolvedValue({ deleted: true });

      render(<BookList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('토비의 스프링')).toBeInTheDocument();
      });

      // Open dialog
      const deleteButton = screen.getByLabelText(STRINGS.BOOK_DELETE_BUTTON_ARIA_LABEL);
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(STRINGS.BOOK_DELETE_DIALOG_TITLE)).toBeInTheDocument();
      });

      // Click confirm
      const confirmButton = screen.getByText(STRINGS.BOOK_DELETE_CONFIRM);
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteBook).toHaveBeenCalledWith(1);
      });
    });
  });
});
