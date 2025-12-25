import type { SearchResultItem } from '@/types';

/**
 * Formats a search result as a markdown blockquote for Obsidian.
 * Format:
 * > **Title** (p.123)
 * >
 * > Content...
 */
export function formatMarkdown(result: SearchResultItem): string {
  const { title, page, content } = result;

  return `> **${title}** (p.${page})
>
> ${content}`;
}
