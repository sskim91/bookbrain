import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { SearchInput } from '@/components/SearchInput';
import { STRINGS } from '@/constants/strings';

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    render(
      <SearchInput value="" onChange={vi.fn()} onSearch={vi.fn()} />
    );
    expect(
      screen.getByPlaceholderText(STRINGS.SEARCH_PLACEHOLDER)
    ).toBeInTheDocument();
  });

  it('auto-focuses on mount when autoFocus is true', () => {
    render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        autoFocus={true}
      />
    );
    expect(screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL)).toHaveFocus();
  });

  it('does not auto-focus when autoFocus is false', () => {
    render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        autoFocus={false}
      />
    );
    expect(screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL)).not.toHaveFocus();
  });

  it('calls onChange when typing', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <SearchInput
        value=""
        onChange={onChange}
        onSearch={vi.fn()}
        autoFocus={false}
      />
    );

    const input = screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL);
    await user.type(input, 'test');

    expect(onChange).toHaveBeenCalledTimes(4); // t, e, s, t
  });

  it('calls onSearch when Enter is pressed with non-empty value', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(
      <SearchInput
        value="test query"
        onChange={vi.fn()}
        onSearch={onSearch}
        autoFocus={false}
      />
    );

    const input = screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL);
    await user.click(input);
    await user.keyboard('{Enter}');

    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it('calls onSearch when Enter is pressed with empty value (validation handled by parent)', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    render(
      <SearchInput value="" onChange={vi.fn()} onSearch={onSearch} autoFocus={false} />
    );

    const input = screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL);
    await user.click(input);
    await user.keyboard('{Enter}');

    // onSearch is called, parent handles validation
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it('disables input when isLoading is true', () => {
    render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        isLoading={true}
      />
    );

    expect(screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL)).toBeDisabled();
  });

  it('shows loading spinner when isLoading is true', () => {
    const { container } = render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        isLoading={true}
      />
    );

    // Should have a spinning loader element
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('does not show spinner when isLoading is false', () => {
    const { container } = render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        isLoading={false}
      />
    );

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).not.toBeInTheDocument();
  });

  it('has aria-busy attribute when loading', () => {
    render(
      <SearchInput
        value=""
        onChange={vi.fn()}
        onSearch={vi.fn()}
        isLoading={true}
      />
    );

    expect(screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL)).toHaveAttribute(
      'aria-busy',
      'true'
    );
  });

  it('has accessible aria-label', () => {
    render(
      <SearchInput value="" onChange={vi.fn()} onSearch={vi.fn()} />
    );

    expect(screen.getByLabelText(STRINGS.SEARCH_ARIA_LABEL)).toBeInTheDocument();
  });
});
