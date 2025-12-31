import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { STRINGS } from '@/constants/strings';

interface ScoreIndicatorProps {
  score: number;
}

type ScoreLevel = 'high' | 'medium' | 'low';

/**
 * Displays similarity score as a colored badge.
 * Thresholds tuned for text-embedding-3-small which produces lower absolute scores.
 * - high (≥35%): green badge - strong semantic match
 * - medium (25-34%): blue badge - moderate match
 * - low (<25%): gray/outline badge - weak match
 */
export function ScoreIndicator({ score }: ScoreIndicatorProps) {
  const getScoreLevel = (score: number): ScoreLevel => {
    if (score >= 0.35) return 'high';
    if (score >= 0.25) return 'medium';
    return 'low';
  };

  const level = getScoreLevel(score);
  const percent = Math.round(score * 100);

  return (
    <Badge
      variant={level === 'low' ? 'outline' : 'secondary'}
      className={cn(
        'font-mono tabular-nums text-xs',
        level === 'high' && 'bg-green-500/15 text-green-600 dark:text-green-400 hover:bg-green-500/20',
        level === 'medium' && 'bg-blue-500/15 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20'
      )}
      aria-label={STRINGS.SCORE_ARIA_LABEL(percent)}
    >
      {percent}%
    </Badge>
  );
}
