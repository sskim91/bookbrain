import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { STRINGS } from '@/constants/strings';

/**
 * ThemeToggle Test Suite
 *
 * NOTE: This file overrides the global next-themes mock from setup.ts
 * because we need fine-grained control over useTheme return values per test.
 * The global mock in setup.ts provides a basic static mock for other components,
 * while this file uses vi.fn() to enable mockReturnValue() for different scenarios.
 */

// Shared mock function for setTheme - allows verification across all tests
const mockSetTheme = vi.fn();

// Override global mock with controllable version
vi.mock('next-themes', () => ({
  useTheme: vi.fn(() => ({
    theme: 'light',
    setTheme: mockSetTheme,
    themes: ['light', 'dark', 'system'],
    systemTheme: 'light',
    resolvedTheme: 'light',
    forcedTheme: undefined,
  })),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => children,
}));

import { useTheme } from 'next-themes';
import { ThemeToggle } from '@/components/ThemeToggle';

// Helper to create mock return value with defaults
function createThemeMock(overrides: Partial<ReturnType<typeof useTheme>> = {}) {
  return {
    theme: 'light',
    setTheme: mockSetTheme,
    themes: ['light', 'dark', 'system'],
    systemTheme: 'light',
    resolvedTheme: 'light',
    forcedTheme: undefined,
    ...overrides,
  };
}

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useTheme).mockReturnValue(createThemeMock());
  });

  describe('Rendering', () => {
    it('renders without crashing', () => {
      render(<ThemeToggle />);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders with correct aria-label for light mode', () => {
      render(<ThemeToggle />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_DARK
      );
    });

    it('renders Sun and Moon icons', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      const svgs = button.querySelectorAll('svg');
      expect(svgs.length).toBe(2);
    });
  });

  describe('AC1: 테마 토글 버튼', () => {
    it('calls setTheme with "dark" when clicked in light mode', async () => {
      const user = userEvent.setup();

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledTimes(1);
      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('calls setTheme with "light" when clicked in dark mode', async () => {
      const user = userEvent.setup();
      vi.mocked(useTheme).mockReturnValue(createThemeMock({ theme: 'dark', resolvedTheme: 'dark' }));

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledTimes(1);
      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });
  });

  describe('Accessibility', () => {
    it('has correct aria-label for dark mode', () => {
      vi.mocked(useTheme).mockReturnValue(createThemeMock({ theme: 'dark', resolvedTheme: 'dark' }));

      render(<ThemeToggle />);

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_LIGHT
      );
    });

    it('button is focusable', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it('can be activated with keyboard (Enter)', async () => {
      const user = userEvent.setup();

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      button.focus();
      await user.keyboard('{Enter}');

      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('can be activated with keyboard (Space)', async () => {
      const user = userEvent.setup();

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      button.focus();
      await user.keyboard(' ');

      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });
  });

  describe('Visual Appearance', () => {
    it('renders as a button with icon styling', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button.className).toBeTruthy();
      expect(button.className).toContain('size-9');
    });

    it('has hover styles applied', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      expect(button.className).toContain('hover:bg-accent');
    });
  });

  describe('Icon Structure', () => {
    it('contains both Sun and Moon SVG icons', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      const svgs = button.querySelectorAll('svg');
      expect(svgs.length).toBe(2);
    });

    it('icons are rendered with proper lucide-react structure', () => {
      render(<ThemeToggle />);
      const button = screen.getByRole('button');
      const svgs = button.querySelectorAll('svg');
      svgs.forEach((svg) => {
        expect(svg.getAttribute('xmlns')).toBe('http://www.w3.org/2000/svg');
      });
    });
  });

  describe('AC3: Theme Persistence', () => {
    it('uses next-themes useTheme hook for theme management', () => {
      render(<ThemeToggle />);
      expect(useTheme).toHaveBeenCalled();
    });

    it('setTheme is called on toggle which triggers next-themes persistence', async () => {
      const user = userEvent.setup();

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('respects current theme from next-themes (system theme detection)', () => {
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: 'dark', systemTheme: 'dark', resolvedTheme: 'dark' })
      );

      render(<ThemeToggle />);

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_LIGHT
      );
    });
  });

  describe('System Theme Behavior', () => {
    /**
     * Note: The current ThemeToggle implementation uses `theme` directly
     * (not `resolvedTheme`) for toggle logic. When theme='system':
     * - aria-label shows "switch to dark" (because 'system' !== 'dark')
     * - clicking toggles to 'dark' (because 'system' !== 'dark' → setTheme('dark'))
     *
     * This is the documented behavior per current implementation.
     * If UX requires resolvedTheme-based toggle, component should be updated.
     */

    it('system theme shows "switch to dark" option', () => {
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: 'system', systemTheme: 'light', resolvedTheme: 'light' })
      );

      render(<ThemeToggle />);

      // Current impl: theme='system' !== 'dark', so shows "switch to dark"
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_DARK
      );
    });

    it('system theme (dark resolved) still shows "switch to dark" option', () => {
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: 'system', systemTheme: 'dark', resolvedTheme: 'dark' })
      );

      render(<ThemeToggle />);

      // Current impl: theme='system' !== 'dark', so shows "switch to dark"
      // (uses theme value, not resolvedTheme)
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_DARK
      );
    });

    it('toggles from system theme to explicit dark', async () => {
      const user = userEvent.setup();
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: 'system', systemTheme: 'light', resolvedTheme: 'light' })
      );

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      // From system, toggles to dark (because 'system' !== 'dark')
      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('toggles from system theme (dark resolved) to explicit dark', async () => {
      const user = userEvent.setup();
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: 'system', systemTheme: 'dark', resolvedTheme: 'dark' })
      );

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      // Current impl: theme='system' !== 'dark', so toggles to 'dark'
      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('handles undefined theme gracefully (defaults to light behavior)', () => {
      vi.mocked(useTheme).mockReturnValue(
        createThemeMock({ theme: undefined as unknown as string })
      );

      render(<ThemeToggle />);

      // Should not crash and should show switch to dark (undefined !== 'dark')
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        STRINGS.THEME_SWITCH_TO_DARK
      );
    });
  });
});
