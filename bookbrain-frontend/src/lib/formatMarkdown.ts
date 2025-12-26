import type { SearchResultItem } from '@/types';

/**
 * Formats a search result as a markdown blockquote for Obsidian.
 * Format:
 * > **Title** (p.123)
 * >
 * > Content line 1...
 * > Content line 2...
 *
 * Each line of content is prefixed with `> ` to maintain proper blockquote
 * formatting in Obsidian, even for multiline content.
 */
export function formatMarkdown(result: SearchResultItem): string {
  const { title, page, content } = result;

  // Add `> ` prefix to each line for proper Obsidian blockquote
  const formattedContent = content
    .split('\n')
    .map((line) => `> ${line}`)
    .join('\n');

  return `> **${title}** (p.${page})
>
${formattedContent}`;
}
