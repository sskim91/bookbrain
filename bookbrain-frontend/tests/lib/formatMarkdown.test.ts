import { describe, it, expect } from 'vitest';
import { formatMarkdown } from '@/lib/formatMarkdown';
import type { SearchResultItem } from '@/types';

describe('formatMarkdown', () => {
  it('formats result as markdown blockquote', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: 'Test Book',
      author: 'Test Author',
      page: 42,
      content: 'This is the content.',
      score: 0.95,
    };

    const markdown = formatMarkdown(result);

    // Each line of content should have `> ` prefix
    expect(markdown).toBe(`> **Test Book** (p.42)
>
> This is the content.`);
  });

  it('handles Korean book title and content', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: '토비의 스프링',
      author: '이일민',
      page: 423,
      content: 'Spring Security는 인증과 권한을 담당합니다.',
      score: 0.92,
    };

    const markdown = formatMarkdown(result);

    expect(markdown).toContain('**토비의 스프링**');
    expect(markdown).toContain('(p.423)');
    expect(markdown).toContain('Spring Security는 인증과 권한을 담당합니다.');
  });

  it('handles null author gracefully', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: 'Unknown Author Book',
      author: null,
      page: 1,
      content: 'Some content.',
      score: 0.5,
    };

    // Should not throw
    const markdown = formatMarkdown(result);
    expect(markdown).toBeDefined();
    expect(markdown).toContain('**Unknown Author Book**');
  });

  it('preserves content with special characters', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: 'Code Examples',
      author: 'Developer',
      page: 100,
      content: 'Use `const` and `let`. Avoid `var`.',
      score: 0.8,
    };

    const markdown = formatMarkdown(result);

    expect(markdown).toContain('`const`');
    expect(markdown).toContain('`let`');
  });

  it('handles title with markdown special characters', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: '**Bold** and *italic* title',
      author: null,
      page: 1,
      content: 'Content with > blockquote chars',
      score: 0.5,
    };

    const markdown = formatMarkdown(result);

    // Title should be preserved as-is (note: may cause formatting issues)
    expect(markdown).toContain('****Bold** and *italic* title**');
    expect(markdown).toContain('> blockquote chars');
  });

  it('handles multiline content with proper blockquote prefix', () => {
    const result: SearchResultItem = {
      book_id: 1,
      title: 'Multiline Book',
      author: null,
      page: 50,
      content: 'First line.\nSecond line.\nThird line.',
      score: 0.7,
    };

    const markdown = formatMarkdown(result);

    // Each line of content should have `> ` prefix for proper Obsidian blockquote
    expect(markdown).toBe(`> **Multiline Book** (p.50)
>
> First line.
> Second line.
> Third line.`);
  });
});
