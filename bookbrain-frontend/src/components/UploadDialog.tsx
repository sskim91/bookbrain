import { useState, useCallback } from 'react';
import { Upload, X, FileText, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { DropZone } from '@/components/DropZone';
import { UploadProgress } from '@/components/UploadProgress';
import { UploadErrorState } from '@/components/UploadErrorState';
import { BookList } from '@/components/BookList';
import { Kbd } from '@/components/ui/kbd';
import { STRINGS } from '@/constants/strings';
import { formatFileSize } from '@/lib/utils';
import { useUploadBook } from '@/hooks/useUploadBook';

interface UploadDialogProps {
  /** Controlled open state (optional) */
  open?: boolean;
  /** Controlled open change handler (optional) */
  onOpenChange?: (open: boolean) => void;
}

export function UploadDialog({ open: controlledOpen, onOpenChange }: UploadDialogProps = {}) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [internalOpen, setInternalOpen] = useState(false);

  // Use controlled state if provided, otherwise use internal state
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;

  // Safe state change handler - works for both controlled and uncontrolled modes
  const setOpen = (newOpen: boolean) => {
    if (isControlled) {
      onOpenChange?.(newOpen);
    } else {
      setInternalOpen(newOpen);
    }
  };

  const {
    upload,
    stage,
    progress,
    isError,
    error,
    reset: resetUpload,
  } = useUploadBook();

  const isUploading = stage !== 'idle' && stage !== 'done' && stage !== 'error';

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
  }, []);

  const handleRemoveFile = useCallback(() => {
    setSelectedFile(null);
  }, []);

  const handleUpload = useCallback(() => {
    if (!selectedFile) return;
    upload(selectedFile);
  }, [selectedFile, upload]);

  const handleRetry = useCallback(() => {
    resetUpload();
    if (selectedFile) {
      upload(selectedFile);
    }
  }, [resetUpload, selectedFile, upload]);

  const handleUploadAnother = useCallback(() => {
    setSelectedFile(null);
    resetUpload();
  }, [resetUpload]);

  const handleOpenChange = useCallback(
    (newOpen: boolean) => {
      // Prevent closing dialog during upload
      if (!newOpen && isUploading) {
        return;
      }

      setOpen(newOpen);

      // Reset state when dialog closes
      if (!newOpen) {
        setSelectedFile(null);
        resetUpload();
      }
    },
    [isUploading, resetUpload]
  );

  // Determine what to render based on state
  const renderContent = () => {
    // Error state
    if (isError) {
      return (
        <UploadErrorState
          message={error?.message}
          onRetry={handleRetry}
        />
      );
    }

    // Uploading/processing state
    if (isUploading) {
      return <UploadProgress stage={stage} progress={progress} />;
    }

    // Done state - show progress with upload another button (AC #3)
    if (stage === 'done') {
      return (
        <div className="space-y-4">
          <UploadProgress stage={stage} progress={progress} />
          <Button
            variant="outline"
            onClick={handleUploadAnother}
            className="w-full"
            aria-label={STRINGS.UPLOAD_ANOTHER_BUTTON}
          >
            <Plus className="mr-2 h-4 w-4" />
            {STRINGS.UPLOAD_ANOTHER_BUTTON}
          </Button>
        </div>
      );
    }

    // Idle state - no file selected
    if (!selectedFile) {
      return <DropZone onFileSelect={handleFileSelect} />;
    }

    // Idle state - file selected, ready to upload
    return (
      <div className="space-y-4">
        {/* Selected file card */}
        <div className="flex items-center gap-3 p-4 border rounded-lg bg-muted/30">
          <FileText className="h-8 w-8 text-muted-foreground flex-shrink-0" />
          <div className="flex-1 min-w-0 overflow-hidden">
            <p className="font-medium truncate">{selectedFile.name}</p>
            <p className="text-sm text-muted-foreground">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRemoveFile}
            disabled={isUploading}
            aria-label={STRINGS.UPLOAD_FILE_REMOVE_ARIA_LABEL}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Upload button */}
        <Button
          onClick={handleUpload}
          className="w-full"
          disabled={isUploading}
        >
          <Upload className="mr-2 h-4 w-4" />
          {STRINGS.UPLOAD_SUBMIT_BUTTON}
        </Button>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          aria-label={STRINGS.UPLOAD_BUTTON_ARIA_LABEL}
          className="h-9 gap-2 px-3"
        >
          <Upload className="h-4 w-4" />
          <span className="hidden sm:inline">{STRINGS.UPLOAD_BUTTON}</span>
          <Kbd showModifier size="sm" className="hidden sm:inline-flex">U</Kbd>
        </Button>
      </DialogTrigger>
      <DialogContent
        className="sm:max-w-[560px] overflow-hidden"
        onPointerDownOutside={(e) => {
          // Prevent closing on outside click during upload
          if (isUploading) {
            e.preventDefault();
          }
        }}
        onEscapeKeyDown={(e) => {
          // Prevent closing on escape during upload
          if (isUploading) {
            e.preventDefault();
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>{STRINGS.UPLOAD_DIALOG_TITLE}</DialogTitle>
          <DialogDescription>
            {STRINGS.UPLOAD_DIALOG_DESCRIPTION}
            <span className="sr-only">
              {'. '}
              {STRINGS.UPLOAD_DIALOG_SR_INSTRUCTIONS}
            </span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 min-w-0">
          {/* Book List Section (FR5, FR21) */}
          <BookList />

          {/* Separator */}
          <div className="border-t" />

          {/* Upload Section */}
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
}
