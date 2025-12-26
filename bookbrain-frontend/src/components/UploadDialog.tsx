import { Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { STRINGS } from '@/constants/strings';

export function UploadDialog() {
  return (
    <Dialog>
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
        <div className="py-8 text-center text-muted-foreground">
          {STRINGS.UPLOAD_DIALOG_PLACEHOLDER}
        </div>
      </DialogContent>
    </Dialog>
  );
}
