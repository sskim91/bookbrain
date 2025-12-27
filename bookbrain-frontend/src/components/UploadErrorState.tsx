import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { STRINGS } from '@/constants/strings';

interface UploadErrorStateProps {
  message?: string;
  onRetry: () => void;
}

export function UploadErrorState({
  message = STRINGS.UPLOAD_ERROR_GENERIC,
  onRetry,
}: UploadErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center gap-4 py-6"
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertCircle className="h-6 w-6" />
        <span className="font-medium">{message}</span>
      </div>
      <Button onClick={onRetry} variant="outline">
        {STRINGS.UPLOAD_RETRY_BUTTON}
      </Button>
    </div>
  );
}
