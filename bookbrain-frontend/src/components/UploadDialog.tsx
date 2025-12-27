import { useState, useCallback } from 'react';
import { Upload, X, FileText } from 'lucide-react';
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
import { STRINGS } from '@/constants/strings';
import { formatFileSize } from '@/lib/utils';

export function UploadDialog() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
  }, []);

  const handleRemoveFile = useCallback(() => {
    setSelectedFile(null);
  }, []);

  const handleUpload = useCallback(() => {
    if (!selectedFile) return;
    // TODO: Story 3.3 will implement actual upload logic
    console.log('Uploading file:', selectedFile.name);
  }, [selectedFile]);

  const handleOpenChange = useCallback((open: boolean) => {
    // Reset state when dialog closes
    if (!open) {
      setSelectedFile(null);
    }
  }, []);

  return (
    <Dialog onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          aria-label={STRINGS.UPLOAD_BUTTON_ARIA_LABEL}
        >
          <Upload className="mr-2 h-4 w-4" />
          {STRINGS.UPLOAD_BUTTON}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[560px]">
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

        {/* File not selected: Show DropZone */}
        {!selectedFile && <DropZone onFileSelect={handleFileSelect} />}

        {/* File selected: Show file info and upload button */}
        {selectedFile && (
          <div className="space-y-4">
            {/* Selected file card */}
            <div className="flex items-center gap-3 p-4 border rounded-lg bg-muted/30">
              <FileText className="h-8 w-8 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRemoveFile}
                aria-label={STRINGS.UPLOAD_FILE_REMOVE_ARIA_LABEL}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Upload button */}
            <Button onClick={handleUpload} className="w-full">
              <Upload className="mr-2 h-4 w-4" />
              {STRINGS.UPLOAD_SUBMIT_BUTTON}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
