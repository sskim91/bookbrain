import { cn } from '@/lib/utils';
import { STRINGS } from '@/constants/strings';

interface ScoreIndicatorProps {
  score: number;
}

type ScoreLevel = 'high' | 'medium' | 'low';

/**
 * Displays similarity score with level-based styling.
 * - high (≥0.8): foreground color
 * - medium (0.5-0.8): muted color
 * - low (<0.5): faded muted color
 */
export function ScoreIndicator({ score }: ScoreIndicatorProps) {
  const getScoreLevel = (score: number): ScoreLevel => {
    if (score >= 0.8) return 'high';
    if (score >= 0.5) return 'medium';
    return 'low';
  };

  const level = getScoreLevel(score);
  const percent = Math.round(score * 100);

  return (
    <span
      className={cn(
        'text-xs font-medium tabular-nums',
        level === 'high' && 'text-foreground',
        level === 'medium' && 'text-muted-foreground',
        level === 'low' && 'text-muted-foreground/60'
      )}
      aria-label={STRINGS.SCORE_ARIA_LABEL(percent)}
    >
      {score.toFixed(2)}
    </span>
  );
}
