import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ResultDetailDialog } from '@/components/ResultDetailDialog';
import { STRINGS } from '@/constants/strings';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockResult = {
  book_id: 1,
  title: '토비의 스프링',
  author: '이일민',
  page: 423,
  content: 'Spring Security는 인증(Authentication)과 권한 부여(Authorization)를 담당하는 프레임워크입니다.',
  score: 0.92,
};

describe('ResultDetailDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock clipboard API using vi.stubGlobal
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
      writable: true,
      configurable: true,
    });
  });

  it('renders nothing when result is null', () => {
    const { container } = render(
      <ResultDetailDialog open={true} onOpenChange={vi.fn()} result={null} />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders result details when open', () => {
    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={vi.fn()}
        result={mockResult}
      />
    );

    // Check title and page in header (use heading role to avoid matching sr-only description)
    expect(screen.getByRole('heading', { name: /토비의 스프링 · p\.423/ })).toBeInTheDocument();

    // Check content is displayed
    expect(screen.getByText(/Spring Security는 인증/)).toBeInTheDocument();

    // Check score is displayed
    expect(screen.getByText('0.92')).toBeInTheDocument();

    // Check copy and close buttons exist in dialog
    const dialog = screen.getByRole('dialog');
    expect(
      within(dialog).getByRole('button', { name: STRINGS.COPY_BUTTON_LABEL })
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole('button', { name: STRINGS.DIALOG_CLOSE })
    ).toBeInTheDocument();
  });

  it('does not render dialog when closed', () => {
    render(
      <ResultDetailDialog
        open={false}
        onOpenChange={vi.fn()}
        result={mockResult}
      />
    );

    // Dialog content should not be visible when closed
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onOpenChange with false when Escape is pressed', async () => {
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={onOpenChange}
        result={mockResult}
      />
    );

    await user.keyboard('{Escape}');

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('calls onOpenChange with false when close button is clicked', async () => {
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={onOpenChange}
        result={mockResult}
      />
    );

    // Close button has sr-only "Close" text
    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('has Copy button in dialog that can be clicked', async () => {
    const user = userEvent.setup();

    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={vi.fn()}
        result={mockResult}
      />
    );

    // Get Copy button within dialog using within() helper
    const dialog = screen.getByRole('dialog');
    const copyButton = within(dialog).getByRole('button', {
      name: STRINGS.COPY_BUTTON_LABEL,
    });

    // Clicking should not throw and should change the button state
    await user.click(copyButton);

    // After clicking, button text should change to "Copied"
    expect(within(dialog).getByText(STRINGS.COPIED)).toBeInTheDocument();
  });

  it('shows copied state after successful copy', async () => {
    const user = userEvent.setup();

    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={vi.fn()}
        result={mockResult}
      />
    );

    const dialog = screen.getByRole('dialog');
    const copyButton = within(dialog).getByRole('button', {
      name: STRINGS.COPY_BUTTON_LABEL,
    });
    await user.click(copyButton);

    // Button should show "Copied" text
    expect(within(dialog).getByText(STRINGS.COPIED)).toBeInTheDocument();
  });

  it('has accessible dialog structure', () => {
    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={vi.fn()}
        result={mockResult}
      />
    );

    // Dialog should be accessible
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();

    // Should have a title accessible to screen readers (use heading role)
    expect(screen.getByRole('heading', { name: /토비의 스프링 · p\.423/ })).toBeInTheDocument();
  });

  it('displays score with two decimal places', () => {
    const resultWithPreciseScore = {
      ...mockResult,
      score: 0.8765,
    };

    render(
      <ResultDetailDialog
        open={true}
        onOpenChange={vi.fn()}
        result={resultWithPreciseScore}
      />
    );

    expect(screen.getByText('0.88')).toBeInTheDocument();
  });
});
