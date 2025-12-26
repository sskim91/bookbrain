import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { UploadDialog } from '@/components/UploadDialog';
import { STRINGS } from '@/constants/strings';

describe('UploadDialog', () => {
  describe('AC1: Upload 버튼 표시', () => {
    it('renders Upload button', () => {
      render(<UploadDialog />);

      const button = screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent(STRINGS.UPLOAD_BUTTON);
    });

    it('Upload button has correct aria-label', () => {
      render(<UploadDialog />);

      const button = screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL });
      expect(button).toHaveAttribute('aria-label', STRINGS.UPLOAD_BUTTON_ARIA_LABEL);
    });

    it('Upload button has Upload icon', () => {
      render(<UploadDialog />);

      const button = screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL });
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('AC2: 모달 열기', () => {
    it('opens dialog when Upload button is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      const button = screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL });
      await user.click(button);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(STRINGS.UPLOAD_DIALOG_TITLE)).toBeInTheDocument();
      expect(screen.getByText(STRINGS.UPLOAD_DIALOG_DESCRIPTION)).toBeInTheDocument();
    });

    it('dialog has correct structure with title and description', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();

      // Check title and description
      expect(screen.getByText(STRINGS.UPLOAD_DIALOG_TITLE)).toBeInTheDocument();
      expect(screen.getByText(STRINGS.UPLOAD_DIALOG_DESCRIPTION)).toBeInTheDocument();
      expect(screen.getByText(STRINGS.UPLOAD_DIALOG_PLACEHOLDER)).toBeInTheDocument();
    });

    it('moves focus to dialog content when opened', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));

      await waitFor(() => {
        const dialog = screen.getByRole('dialog');
        expect(dialog).toBeInTheDocument();
        // Focus should be within dialog
        expect(dialog.contains(document.activeElement)).toBe(true);
      });
    });
  });

  describe('AC3: 모달 닫기', () => {
    it('closes dialog when X button is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      // Open dialog
      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Close via X button
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('closes dialog when Esc key is pressed', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      // Open dialog
      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Close via Esc
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('closes dialog when backdrop is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      // Open dialog
      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Click on the overlay (backdrop)
      const overlay = document.querySelector('[data-slot="dialog-overlay"]');
      expect(overlay).toBeInTheDocument();

      if (overlay) {
        await user.click(overlay);
      }

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('dialog has correct aria attributes', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));

      const dialog = screen.getByRole('dialog');
      // Radix Dialog automatically associates aria-describedby with DialogDescription
      expect(dialog).toHaveAttribute('aria-describedby');
      expect(dialog).toHaveAttribute('aria-labelledby');
    });

    it('includes screen reader instructions for context', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      await user.click(screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL }));

      // Check that sr-only instructions are present in the DOM
      const srInstructions = document.querySelector('.sr-only');
      expect(srInstructions).toBeInTheDocument();
      expect(srInstructions?.textContent).toContain(STRINGS.UPLOAD_DIALOG_SR_INSTRUCTIONS);
    });

    it('dialog can be opened and closed with keyboard only', async () => {
      const user = userEvent.setup();
      render(<UploadDialog />);

      // Focus and activate button with keyboard
      const button = screen.getByRole('button', { name: STRINGS.UPLOAD_BUTTON_ARIA_LABEL });
      button.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close with Esc
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });
});
