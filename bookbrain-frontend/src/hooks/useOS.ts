import { useState } from 'react';

type OS = 'mac' | 'windows' | 'linux' | 'unknown';

/**
 * Detects OS from navigator.
 * Uses lazy initialization to prevent hydration flicker.
 */
function detectOS(): OS {
  if (typeof window === 'undefined') return 'unknown'; // SSR safety

  const { userAgent, platform } = window.navigator;
  const ua = userAgent.toLowerCase();
  const plat = platform.toLowerCase();

  if (plat.includes('mac') || ua.includes('mac')) return 'mac';
  if (plat.includes('win') || ua.includes('win')) return 'windows';
  if (plat.includes('linux') || ua.includes('linux')) return 'linux';
  return 'unknown';
}

/**
 * Detects the user's operating system.
 * Returns 'mac' for macOS, 'windows' for Windows, 'linux' for Linux.
 * Used for displaying appropriate keyboard shortcuts (⌘ vs Ctrl).
 *
 * Uses lazy initialization to prevent flicker on initial render.
 */
export function useOS(): OS {
  const [os] = useState<OS>(detectOS);
  return os;
}

/**
 * Returns the modifier key symbol based on OS.
 * ⌘ for macOS, Ctrl for Windows/Linux.
 */
export function useModifierKey(): string {
  const os = useOS();
  return os === 'mac' ? '⌘' : 'Ctrl';
}

/**
 * Check if the current OS is macOS.
 * Useful for keyboard event handlers.
 */
export function isMac(): boolean {
  if (typeof navigator === 'undefined') return false;
  const platform = navigator.platform.toLowerCase();
  const userAgent = navigator.userAgent.toLowerCase();
  return platform.includes('mac') || userAgent.includes('mac');
}
