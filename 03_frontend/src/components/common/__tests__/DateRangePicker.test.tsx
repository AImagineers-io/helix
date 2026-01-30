import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DateRangePicker } from '../DateRangePicker';
import { DateRangePreset } from '../../../hooks/useDateRange';

describe('DateRangePicker', () => {
  const mockOnPresetChange = vi.fn();
  const mockOnCustomRangeChange = vi.fn();

  const defaultProps = {
    preset: 'last_30_days' as DateRangePreset,
    rangeLabel: 'Last 30 days',
    startDate: new Date('2024-12-16'),
    endDate: new Date('2025-01-15'),
    onPresetChange: mockOnPresetChange,
    onCustomRangeChange: mockOnCustomRangeChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render the current range label', () => {
      render(<DateRangePicker {...defaultProps} />);

      expect(screen.getByText('Last 30 days')).toBeInTheDocument();
    });

    it('should render preset options in dropdown', () => {
      render(<DateRangePicker {...defaultProps} />);

      // Click to open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Get all options from the listbox
      const options = screen.getAllByRole('option');
      const optionTexts = options.map((opt) => opt.textContent);

      expect(optionTexts).toContain('Today');
      expect(optionTexts).toContain('Last 7 days');
      expect(optionTexts).toContain('Last 30 days');
      expect(optionTexts).toContain('This month');
      expect(optionTexts).toContain('Last month');
      expect(optionTexts).toContain('Custom');
    });

    it('should indicate currently selected preset', () => {
      render(<DateRangePicker {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));

      const selectedOption = screen.getByRole('option', { selected: true });
      expect(selectedOption).toHaveTextContent('Last 30 days');
    });
  });

  describe('preset selection', () => {
    it('should call onPresetChange when preset is selected', () => {
      render(<DateRangePicker {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Last 7 days'));

      expect(mockOnPresetChange).toHaveBeenCalledWith('last_7_days');
    });

    it('should close dropdown after selecting preset', () => {
      render(<DateRangePicker {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Last 7 days'));

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });
  });

  describe('custom range selection', () => {
    it('should show date inputs when custom is selected', () => {
      render(<DateRangePicker {...defaultProps} preset="custom" />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Custom'));

      expect(screen.getByLabelText('Start date')).toBeInTheDocument();
      expect(screen.getByLabelText('End date')).toBeInTheDocument();
    });

    it('should call onCustomRangeChange when dates are changed', () => {
      render(<DateRangePicker {...defaultProps} preset="custom" rangeLabel="Jan 1, 2025 - Jan 10, 2025" />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Custom'));

      const startInput = screen.getByLabelText('Start date');
      const endInput = screen.getByLabelText('End date');

      fireEvent.change(startInput, { target: { value: '2025-01-05' } });
      fireEvent.change(endInput, { target: { value: '2025-01-20' } });

      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnCustomRangeChange).toHaveBeenCalled();
    });

    it('should not allow end date before start date', () => {
      render(<DateRangePicker {...defaultProps} preset="custom" rangeLabel="Jan 1, 2025 - Jan 10, 2025" />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Custom'));

      const startInput = screen.getByLabelText('Start date');
      const endInput = screen.getByLabelText('End date');

      fireEvent.change(startInput, { target: { value: '2025-01-20' } });
      fireEvent.change(endInput, { target: { value: '2025-01-05' } });

      const applyButton = screen.getByText('Apply');
      expect(applyButton).toBeDisabled();
    });
  });

  describe('accessibility', () => {
    it('should have accessible button', () => {
      render(<DateRangePicker {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAccessibleName(/date range/i);
    });

    it('should support keyboard navigation', () => {
      render(<DateRangePicker {...defaultProps} />);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('should close on Escape', () => {
      render(<DateRangePicker {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));
      expect(screen.getByRole('listbox')).toBeInTheDocument();

      fireEvent.keyDown(screen.getByRole('listbox'), { key: 'Escape' });
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });
  });

  describe('disabled state', () => {
    it('should not open dropdown when disabled', () => {
      render(<DateRangePicker {...defaultProps} disabled />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('should show disabled styling', () => {
      render(<DateRangePicker {...defaultProps} disabled />);

      expect(screen.getByRole('button')).toBeDisabled();
    });
  });
});
