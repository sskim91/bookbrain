import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ScoreIndicator } from '@/components/ScoreIndicator';

describe('ScoreIndicator', () => {
  it('renders score as percentage', () => {
    render(<ScoreIndicator score={0.9234} />);
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('renders 100% for perfect score', () => {
    render(<ScoreIndicator score={1.0} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders 0% for zero score', () => {
    render(<ScoreIndicator score={0.0} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('has foreground color for high score (≥0.8)', () => {
    render(<ScoreIndicator score={0.85} />);
    const element = screen.getByText('85%');
    expect(element).toHaveClass('text-foreground');
  });

  it('has muted color for medium score (0.5-0.8)', () => {
    render(<ScoreIndicator score={0.65} />);
    const element = screen.getByText('65%');
    expect(element).toHaveClass('text-muted-foreground');
  });

  it('has faded color for low score (<0.5)', () => {
    render(<ScoreIndicator score={0.35} />);
    const element = screen.getByText('35%');
    expect(element).toHaveClass('text-muted-foreground/60');
  });

  it('has correct aria-label with percentage', () => {
    render(<ScoreIndicator score={0.92} />);
    expect(screen.getByLabelText('유사도 92%')).toBeInTheDocument();
  });

  it('rounds percentage in aria-label', () => {
    render(<ScoreIndicator score={0.876} />);
    // 0.876 * 100 = 87.6, rounded to 88%
    expect(screen.getByLabelText('유사도 88%')).toBeInTheDocument();
  });

  it('uses tabular-nums for consistent number width', () => {
    render(<ScoreIndicator score={0.5} />);
    const element = screen.getByText('50%');
    expect(element).toHaveClass('tabular-nums');
  });

  it('boundary: 0.8 is high', () => {
    render(<ScoreIndicator score={0.8} />);
    const element = screen.getByText('80%');
    expect(element).toHaveClass('text-foreground');
  });

  it('boundary: 0.5 is medium', () => {
    render(<ScoreIndicator score={0.5} />);
    const element = screen.getByText('50%');
    expect(element).toHaveClass('text-muted-foreground');
    expect(element).not.toHaveClass('text-foreground');
  });

  it('boundary: 0.49 is low', () => {
    render(<ScoreIndicator score={0.49} />);
    const element = screen.getByText('49%');
    expect(element).toHaveClass('text-muted-foreground/60');
  });
});
