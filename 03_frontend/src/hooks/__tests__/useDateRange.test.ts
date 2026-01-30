import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDateRange, DateRangePreset } from '../useDateRange';

describe('useDateRange', () => {
  const mockDate = new Date('2025-01-15T12:00:00Z');

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(mockDate);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should default to "last_30_days" preset', () => {
      const { result } = renderHook(() => useDateRange());

      expect(result.current.preset).toBe('last_30_days');
    });

    it('should calculate correct range for last_30_days', () => {
      const { result } = renderHook(() => useDateRange());

      expect(result.current.startDate).toEqual(new Date('2024-12-16T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-15T23:59:59.999Z'));
    });

    it('should allow custom initial preset', () => {
      const { result } = renderHook(() => useDateRange({ initialPreset: 'today' }));

      expect(result.current.preset).toBe('today');
    });
  });

  describe('preset changes', () => {
    it('should update range when preset changes to today', () => {
      const { result } = renderHook(() => useDateRange());

      act(() => {
        result.current.setPreset('today');
      });

      expect(result.current.preset).toBe('today');
      expect(result.current.startDate).toEqual(new Date('2025-01-15T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-15T23:59:59.999Z'));
    });

    it('should update range when preset changes to last_7_days', () => {
      const { result } = renderHook(() => useDateRange());

      act(() => {
        result.current.setPreset('last_7_days');
      });

      expect(result.current.preset).toBe('last_7_days');
      expect(result.current.startDate).toEqual(new Date('2025-01-08T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-15T23:59:59.999Z'));
    });

    it('should update range when preset changes to this_month', () => {
      const { result } = renderHook(() => useDateRange());

      act(() => {
        result.current.setPreset('this_month');
      });

      expect(result.current.preset).toBe('this_month');
      expect(result.current.startDate).toEqual(new Date('2025-01-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-15T23:59:59.999Z'));
    });

    it('should update range when preset changes to last_month', () => {
      const { result } = renderHook(() => useDateRange());

      act(() => {
        result.current.setPreset('last_month');
      });

      expect(result.current.preset).toBe('last_month');
      expect(result.current.startDate).toEqual(new Date('2024-12-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2024-12-31T23:59:59.999Z'));
    });
  });

  describe('custom date range', () => {
    it('should allow setting custom date range', () => {
      const { result } = renderHook(() => useDateRange());

      const customStart = new Date('2025-01-01');
      const customEnd = new Date('2025-01-10');

      act(() => {
        result.current.setCustomRange(customStart, customEnd);
      });

      expect(result.current.preset).toBe('custom');
      expect(result.current.startDate).toEqual(new Date('2025-01-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-10T23:59:59.999Z'));
    });

    it('should normalize custom start date to start of day', () => {
      const { result } = renderHook(() => useDateRange());

      const customStart = new Date('2025-01-01T14:30:00Z');
      const customEnd = new Date('2025-01-10T08:00:00Z');

      act(() => {
        result.current.setCustomRange(customStart, customEnd);
      });

      expect(result.current.startDate.getUTCHours()).toBe(0);
      expect(result.current.startDate.getUTCMinutes()).toBe(0);
      expect(result.current.startDate.getUTCSeconds()).toBe(0);
    });

    it('should normalize custom end date to end of day', () => {
      const { result } = renderHook(() => useDateRange());

      const customStart = new Date('2025-01-01T14:30:00Z');
      const customEnd = new Date('2025-01-10T08:00:00Z');

      act(() => {
        result.current.setCustomRange(customStart, customEnd);
      });

      expect(result.current.endDate.getUTCHours()).toBe(23);
      expect(result.current.endDate.getUTCMinutes()).toBe(59);
      expect(result.current.endDate.getUTCSeconds()).toBe(59);
    });
  });

  describe('formatted output', () => {
    it('should provide formatted start and end dates for API', () => {
      const { result } = renderHook(() => useDateRange({ initialPreset: 'today' }));

      // ISO format for API calls
      expect(result.current.startDateISO).toBe('2025-01-15T00:00:00.000Z');
      expect(result.current.endDateISO).toBe('2025-01-15T23:59:59.999Z');
    });

    it('should provide display-friendly date strings', () => {
      const { result } = renderHook(() => useDateRange({ initialPreset: 'today' }));

      expect(result.current.startDateDisplay).toBe('Jan 15, 2025');
      expect(result.current.endDateDisplay).toBe('Jan 15, 2025');
    });

    it('should provide range label for current preset', () => {
      const { result } = renderHook(() => useDateRange({ initialPreset: 'last_7_days' }));

      expect(result.current.rangeLabel).toBe('Last 7 days');
    });

    it('should provide custom range label for custom preset', () => {
      const { result } = renderHook(() => useDateRange());

      act(() => {
        result.current.setCustomRange(new Date('2025-01-01'), new Date('2025-01-10'));
      });

      expect(result.current.rangeLabel).toBe('Jan 1, 2025 - Jan 10, 2025');
    });
  });

  describe('preset options', () => {
    it('should provide list of available presets', () => {
      const { result } = renderHook(() => useDateRange());

      expect(result.current.presetOptions).toEqual([
        { value: 'today', label: 'Today' },
        { value: 'last_7_days', label: 'Last 7 days' },
        { value: 'last_30_days', label: 'Last 30 days' },
        { value: 'this_month', label: 'This month' },
        { value: 'last_month', label: 'Last month' },
        { value: 'custom', label: 'Custom' },
      ]);
    });
  });

  describe('edge cases', () => {
    it('should handle month boundaries correctly for this_month at end of month', () => {
      vi.setSystemTime(new Date('2025-01-31T12:00:00Z'));

      const { result } = renderHook(() => useDateRange({ initialPreset: 'this_month' }));

      expect(result.current.startDate).toEqual(new Date('2025-01-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-01-31T23:59:59.999Z'));
    });

    it('should handle February correctly for last_month', () => {
      vi.setSystemTime(new Date('2025-03-15T12:00:00Z'));

      const { result } = renderHook(() => useDateRange({ initialPreset: 'last_month' }));

      expect(result.current.startDate).toEqual(new Date('2025-02-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2025-02-28T23:59:59.999Z'));
    });

    it('should handle leap year February correctly', () => {
      vi.setSystemTime(new Date('2024-03-15T12:00:00Z'));

      const { result } = renderHook(() => useDateRange({ initialPreset: 'last_month' }));

      expect(result.current.startDate).toEqual(new Date('2024-02-01T00:00:00.000Z'));
      expect(result.current.endDate).toEqual(new Date('2024-02-29T23:59:59.999Z'));
    });
  });
});
