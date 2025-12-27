import { Progress } from '@/components/ui/progress';
import {
  Upload,
  FileSearch,
  Scissors,
  Sparkles,
  Check,
  Loader2,
} from 'lucide-react';
import { STRINGS } from '@/constants/strings';
import { cn } from '@/lib/utils';
import { UPLOAD_STAGES_ORDER, type UploadStage } from '@/hooks/useUploadBook';

interface UploadProgressProps {
  stage: UploadStage;
  progress: number;
}

const STAGE_CONFIG: Record<
  UploadStage,
  {
    icon: React.ElementType;
    text: string;
    showProgress: boolean;
  }
> = {
  idle: { icon: Upload, text: '', showProgress: false },
  uploading: {
    icon: Upload,
    text: STRINGS.UPLOAD_STAGE_UPLOADING,
    showProgress: true,
  },
  parsing: {
    icon: FileSearch,
    text: STRINGS.UPLOAD_STAGE_PARSING,
    showProgress: false,
  },
  chunking: {
    icon: Scissors,
    text: STRINGS.UPLOAD_STAGE_CHUNKING,
    showProgress: false,
  },
  embedding: {
    icon: Sparkles,
    text: STRINGS.UPLOAD_STAGE_EMBEDDING,
    showProgress: false,
  },
  done: { icon: Check, text: STRINGS.UPLOAD_STAGE_COMPLETE, showProgress: false },
  error: { icon: Upload, text: '', showProgress: false },
};

function isStageComplete(currentStage: UploadStage, checkStage: UploadStage): boolean {
  const currentIndex = UPLOAD_STAGES_ORDER.indexOf(currentStage);
  const checkIndex = UPLOAD_STAGES_ORDER.indexOf(checkStage);

  if (currentStage === 'done') return true;
  if (currentIndex === -1 || checkIndex === -1) return false;

  return currentIndex > checkIndex;
}

function isStageActive(currentStage: UploadStage, checkStage: UploadStage): boolean {
  return currentStage === checkStage;
}

interface StageIndicatorProps {
  active: boolean;
  done: boolean;
  children: React.ReactNode;
}

function StageIndicator({ active, done, children }: StageIndicatorProps) {
  return (
    <span
      className={cn(
        'transition-colors',
        active && 'text-primary font-medium',
        done && 'text-green-500'
      )}
    >
      {done && '✓ '}
      {children}
    </span>
  );
}

export function UploadProgress({ stage, progress }: UploadProgressProps) {
  const config = STAGE_CONFIG[stage];
  const Icon = config.icon;
  const isIndeterminate = !config.showProgress && stage !== 'done';

  return (
    <div className="space-y-4 py-4" role="status" aria-live="polite">
      <div className="flex items-center justify-center gap-3">
        {isIndeterminate ? (
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        ) : (
          <Icon className="h-6 w-6 text-primary" />
        )}
        <span className="text-sm font-medium">{config.text}</span>
        {config.showProgress && (
          <span className="text-sm text-muted-foreground">{progress}%</span>
        )}
      </div>

      <Progress
        value={config.showProgress ? progress : (stage === 'done' ? 100 : undefined)}
        className="h-2"
        aria-label={STRINGS.UPLOAD_PROGRESS_ARIA_LABEL(progress)}
        aria-valuenow={config.showProgress ? progress : undefined}
      />

      {/* Stage indicators */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <StageIndicator
          active={isStageActive(stage, 'uploading')}
          done={isStageComplete(stage, 'uploading')}
        >
          {STRINGS.UPLOAD_STAGE_UPLOAD}
        </StageIndicator>
        <StageIndicator
          active={isStageActive(stage, 'parsing')}
          done={isStageComplete(stage, 'parsing')}
        >
          {STRINGS.UPLOAD_STAGE_PARSE}
        </StageIndicator>
        <StageIndicator
          active={isStageActive(stage, 'chunking')}
          done={isStageComplete(stage, 'chunking')}
        >
          {STRINGS.UPLOAD_STAGE_CHUNK}
        </StageIndicator>
        <StageIndicator
          active={isStageActive(stage, 'embedding')}
          done={isStageComplete(stage, 'embedding')}
        >
          {STRINGS.UPLOAD_STAGE_EMBED}
        </StageIndicator>
      </div>
    </div>
  );
}
