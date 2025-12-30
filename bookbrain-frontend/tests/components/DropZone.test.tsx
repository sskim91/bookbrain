import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DropZone } from '@/components/DropZone';
import { STRINGS } from '@/constants/strings';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

/**
 * Creates a mock File object for testing.
 */
function createMockFile(name: string, type: string): File {
  const blob = new Blob([''], { type });
  return new File([blob], name, { type });
}

/**
 * Creates a mock DataTransfer object for drag and drop testing.
 */
function createMockDataTransfer(files: File[]): DataTransfer {
  const dataTransfer = {
    files: files,
    items: files.map((file) => ({
      kind: 'file',
      type: file.type,
      getAsFile: () => file,
    })),
    types: ['Files'],
    getData: () => '',
    setData: () => {},
    clearData: () => {},
    dropEffect: 'none' as DataTransferDropEffect,
    effectAllowed: 'all' as DataTransferEffectAllowed,
  };
  return dataTransfer as unknown as DataTransfer;
}

describe('DropZone', () => {
  let onFileSelect: ReturnType<typeof vi.fn>;
  let onError: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onFileSelect = vi.fn();
    onError = vi.fn();
    vi.clearAllMocks();
  });

  describe('AC1: 드롭존 표시', () => {
    it('renders dropzone with default text and icon', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      expect(screen.getByText(STRINGS.DROPZONE_DEFAULT_TEXT)).toBeInTheDocument();
      // Check for Upload icon (SVG)
      const dropzone = screen.getByRole('button');
      const svg = dropzone.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('has correct aria-label for accessibility', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button', {
        name: STRINGS.DROPZONE_ARIA_LABEL,
      });
      expect(dropzone).toBeInTheDocument();
    });

    it('has proper focus styles', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      expect(dropzone).toHaveAttribute('tabIndex', '0');
      expect(dropzone.className).toContain('focus-visible:ring-2');
    });
  });

  describe('AC2: 파일 선택 다이얼로그', () => {
    it('triggers file input when clicked', async () => {
      const user = userEvent.setup();
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;

      // Spy on click
      const clickSpy = vi.spyOn(fileInput, 'click');

      await user.click(dropzone);

      expect(clickSpy).toHaveBeenCalled();
    });

    it('triggers file input when Enter key pressed', async () => {
      const user = userEvent.setup();
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, 'click');

      dropzone.focus();
      await user.keyboard('{Enter}');

      expect(clickSpy).toHaveBeenCalled();
    });

    it('triggers file input when Space key pressed', async () => {
      const user = userEvent.setup();
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, 'click');

      dropzone.focus();
      await user.keyboard(' ');

      expect(clickSpy).toHaveBeenCalled();
    });

    it('accepts only PDF files via input', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;

      expect(fileInput).toHaveAttribute('accept', '.pdf,application/pdf');
    });

    it('calls onFileSelect when valid PDF file is selected via input', async () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;

      const pdfFile = createMockFile('test.pdf', 'application/pdf');

      // Simulate file selection
      Object.defineProperty(fileInput, 'files', {
        value: [pdfFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      expect(onFileSelect).toHaveBeenCalledWith(pdfFile);
    });
  });

  describe('AC3: 드래그 상태 변경', () => {
    it('changes style when file is dragged over', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      fireEvent.dragEnter(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      // Check for active styles
      expect(dropzone.className).toContain('border-primary');
      expect(dropzone.className).toContain('bg-primary/5');
    });

    it('shows active text when file is dragged over', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      fireEvent.dragEnter(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(screen.getByText(STRINGS.DROPZONE_ACTIVE_TEXT)).toBeInTheDocument();
      expect(screen.queryByText(STRINGS.DROPZONE_DEFAULT_TEXT)).not.toBeInTheDocument();
    });

    it('reverts style when drag leaves', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      // Drag enter
      fireEvent.dragEnter(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(dropzone.className).toContain('border-primary');

      // Drag leave
      fireEvent.dragLeave(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(dropzone.className).not.toContain('border-primary');
      expect(screen.getByText(STRINGS.DROPZONE_DEFAULT_TEXT)).toBeInTheDocument();
    });

    it('maintains dragOver behavior', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      fireEvent.dragOver(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(dropzone.className).toContain('border-primary');
    });
  });

  describe('AC4: 파일 드롭 성공', () => {
    it('calls onFileSelect with valid PDF file', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const pdfFile = createMockFile('document.pdf', 'application/pdf');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([pdfFile]),
      });

      expect(onFileSelect).toHaveBeenCalledWith(pdfFile);
    });

    it('resets drag active state after drop', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      // First drag over
      fireEvent.dragEnter(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(dropzone.className).toContain('border-primary');

      // Then drop
      const pdfFile = createMockFile('document.pdf', 'application/pdf');
      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([pdfFile]),
      });

      expect(dropzone.className).not.toContain('border-primary');
      expect(screen.getByText(STRINGS.DROPZONE_DEFAULT_TEXT)).toBeInTheDocument();
    });
  });

  describe('AC5: 파일 형식 에러', () => {
    it('calls onError with invalid file type (non-PDF MIME)', () => {
      render(<DropZone onFileSelect={onFileSelect} onError={onError} />);

      const dropzone = screen.getByRole('button');
      const txtFile = createMockFile('document.txt', 'text/plain');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([txtFile]),
      });

      expect(onError).toHaveBeenCalledWith(STRINGS.DROPZONE_ERROR_INVALID_TYPE);
      expect(onFileSelect).not.toHaveBeenCalled();
    });

    it('calls onError with invalid file extension (not .pdf)', () => {
      render(<DropZone onFileSelect={onFileSelect} onError={onError} />);

      const dropzone = screen.getByRole('button');
      // File claims to be PDF but has wrong extension
      const fakeFile = createMockFile('document.exe', 'application/pdf');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([fakeFile]),
      });

      expect(onError).toHaveBeenCalledWith(STRINGS.DROPZONE_ERROR_INVALID_TYPE);
      expect(onFileSelect).not.toHaveBeenCalled();
    });

    it('shows toast error when onError is not provided', async () => {
      const { toast } = await import('sonner');
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const txtFile = createMockFile('document.txt', 'text/plain');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([txtFile]),
      });

      expect(toast.error).toHaveBeenCalledWith(STRINGS.DROPZONE_ERROR_INVALID_TYPE);
      expect(onFileSelect).not.toHaveBeenCalled();
    });

    it('does not call onFileSelect with invalid file via input', () => {
      render(<DropZone onFileSelect={onFileSelect} onError={onError} />);

      const dropzone = screen.getByRole('button');
      const fileInput = dropzone.querySelector('input[type="file"]') as HTMLInputElement;

      const txtFile = createMockFile('test.txt', 'text/plain');

      Object.defineProperty(fileInput, 'files', {
        value: [txtFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      expect(onError).toHaveBeenCalledWith(STRINGS.DROPZONE_ERROR_INVALID_TYPE);
      expect(onFileSelect).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Accessibility', () => {
    it('is focusable via tab', async () => {
      const user = userEvent.setup();
      render(
        <>
          <button>Before</button>
          <DropZone onFileSelect={onFileSelect} />
        </>
      );

      // Tab to focus dropzone
      await user.tab();
      await user.tab();

      const dropzone = screen.getByRole('button', {
        name: STRINGS.DROPZONE_ARIA_LABEL,
      });
      expect(dropzone).toHaveFocus();
    });

    it('has sr-only helper text', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const srOnlyText = document.querySelector('.sr-only');
      expect(srOnlyText).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty drop (no files)', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([]),
      });

      expect(onFileSelect).not.toHaveBeenCalled();
    });

    it('handles multiple files (only first is processed)', () => {
      render(<DropZone onFileSelect={onFileSelect} />);

      const dropzone = screen.getByRole('button');
      const file1 = createMockFile('doc1.pdf', 'application/pdf');
      const file2 = createMockFile('doc2.pdf', 'application/pdf');

      fireEvent.drop(dropzone, {
        dataTransfer: createMockDataTransfer([file1, file2]),
      });

      expect(onFileSelect).toHaveBeenCalledTimes(1);
      expect(onFileSelect).toHaveBeenCalledWith(file1);
    });
  });
});
