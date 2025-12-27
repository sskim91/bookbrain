import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UploadProgress } from '@/components/UploadProgress';
import { STRINGS } from '@/constants/strings';

describe('UploadProgress', () => {
  describe('uploading stage', () => {
    it('shows uploading text and progress', () => {
      render(<UploadProgress stage="uploading" progress={50} />);

      expect(screen.getByText(STRINGS.UPLOAD_STAGE_UPLOADING)).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('has correct aria-label for progress bar', () => {
      render(<UploadProgress stage="uploading" progress={50} />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    });
  });

  describe('parsing stage', () => {
    it('shows parsing text with spinner', () => {
      render(<UploadProgress stage="parsing" progress={100} />);

      expect(screen.getByText(STRINGS.UPLOAD_STAGE_PARSING)).toBeInTheDocument();
      // Should not show percentage in parsing stage
      expect(screen.queryByText('100%')).not.toBeInTheDocument();
    });
  });

  describe('done stage', () => {
    it('shows completion text', () => {
      render(<UploadProgress stage="done" progress={100} />);

      expect(screen.getByText(STRINGS.UPLOAD_STAGE_COMPLETE)).toBeInTheDocument();
    });
  });

  describe('stage indicators', () => {
    it('highlights active stage indicator', () => {
      render(<UploadProgress stage="uploading" progress={50} />);

      const uploadIndicator = screen.getByText(STRINGS.UPLOAD_STAGE_UPLOAD);
      expect(uploadIndicator).toHaveClass('text-primary');
    });

    it('shows checkmark for completed stages', () => {
      render(<UploadProgress stage="parsing" progress={100} />);

      // Upload stage should be marked as done with checkmark
      expect(screen.getByText(/✓.*업로드/)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has role="status" for live updates', () => {
      render(<UploadProgress stage="uploading" progress={50} />);

      const container = screen.getByRole('status');
      expect(container).toBeInTheDocument();
    });

    it('has aria-live="polite" for screen readers', () => {
      render(<UploadProgress stage="uploading" progress={50} />);

      const container = screen.getByRole('status');
      expect(container).toHaveAttribute('aria-live', 'polite');
    });
  });
});
