import { useState, useRef, useCallback } from 'react';
import { Upload } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { STRINGS } from '@/constants/strings';

/**
 * Validates if a file is a valid PDF.
 * Checks both MIME type and file extension for security.
 */
function isValidPDF(file: File): boolean {
  const validTypes = ['application/pdf'];
  const validExtension = file.name.toLowerCase().endsWith('.pdf');
  return validTypes.includes(file.type) && validExtension;
}

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  onError?: (message: string) => void;
}

export function DropZone({ onFileSelect, onError }: DropZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Prevent flicker when dragging over child elements
    if (
      containerRef.current &&
      e.relatedTarget instanceof Node &&
      containerRef.current.contains(e.relatedTarget)
    ) {
      return;
    }

    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const file = e.dataTransfer.files[0];
      if (!file) return;

      if (isValidPDF(file)) {
        onFileSelect(file);
      } else {
        const errorMessage = STRINGS.DROPZONE_ERROR_INVALID_TYPE;
        if (onError) {
          onError(errorMessage);
        } else {
          toast.error(errorMessage);
        }
      }
    },
    [onFileSelect, onError]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (isValidPDF(file)) {
        onFileSelect(file);
      } else {
        const errorMessage = STRINGS.DROPZONE_ERROR_INVALID_TYPE;
        if (onError) {
          onError(errorMessage);
        } else {
          toast.error(errorMessage);
        }
      }

      // Reset input to allow selecting the same file again
      e.target.value = '';
    },
    [onFileSelect, onError]
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        inputRef.current?.click();
      }
    },
    []
  );

  return (
    <div
      ref={containerRef}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      aria-label={STRINGS.DROPZONE_ARIA_LABEL}
      className={cn(
        'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/25 hover:border-muted-foreground/50'
      )}
    >
      <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
      <p className="text-muted-foreground">
        {isDragActive
          ? STRINGS.DROPZONE_ACTIVE_TEXT
          : STRINGS.DROPZONE_DEFAULT_TEXT}
      </p>
      <span className="sr-only">
        {isDragActive ? 'Drop file now' : 'Click or press Enter to select file'}
      </span>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
        aria-hidden="true"
      />
    </div>
  );
}
