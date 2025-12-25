import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Header } from '@/components/Header';
import { STRINGS } from '@/constants/strings';

describe('Header', () => {
  it('renders the logo text', () => {
    render(<Header />);
    expect(screen.getByText(STRINGS.APP_NAME)).toBeInTheDocument();
  });

  it('renders the theme toggle button', () => {
    render(<Header />);
    // Theme toggle button has aria-label
    expect(
      screen.getByRole('button', { name: /switch to/i })
    ).toBeInTheDocument();
  });

  it('uses semantic header element', () => {
    render(<Header />);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});
