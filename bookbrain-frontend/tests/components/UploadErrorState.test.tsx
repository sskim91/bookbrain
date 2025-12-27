import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadErrorState } from '@/components/UploadErrorState';
import { STRINGS } from '@/constants/strings';

describe('UploadErrorState', () => {
  it('displays default error message', () => {
    render(<UploadErrorState onRetry={vi.fn()} />);

    expect(screen.getByText(STRINGS.UPLOAD_ERROR_GENERIC)).toBeInTheDocument();
  });

  it('displays custom error message', () => {
    render(<UploadErrorState message="Custom error" onRetry={vi.fn()} />);

    expect(screen.getByText('Custom error')).toBeInTheDocument();
  });

  it('shows retry button', () => {
    render(<UploadErrorState onRetry={vi.fn()} />);

    expect(
      screen.getByRole('button', { name: STRINGS.UPLOAD_RETRY_BUTTON })
    ).toBeInTheDocument();
  });

  it('calls onRetry when retry button clicked', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(<UploadErrorState onRetry={onRetry} />);

    await user.click(
      screen.getByRole('button', { name: STRINGS.UPLOAD_RETRY_BUTTON })
    );

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('has role="alert" for accessibility', () => {
    render(<UploadErrorState onRetry={vi.fn()} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('displays AlertCircle icon', () => {
    render(<UploadErrorState onRetry={vi.fn()} />);

    // The AlertCircle icon should have a test id or be identifiable
    const container = screen.getByRole('alert');
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
