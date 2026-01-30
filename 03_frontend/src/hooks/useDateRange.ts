import { useState, useMemo, useCallback } from 'react';

export type DateRangePreset =
  | 'today'
  | 'last_7_days'
  | 'last_30_days'
  | 'this_month'
  | 'last_month'
  | 'custom';

export interface DateRangePresetOption {
  value: DateRangePreset;
  label: string;
}

export interface UseDateRangeOptions {
  initialPreset?: DateRangePreset;
}

export interface UseDateRangeReturn {
  preset: DateRangePreset;
  startDate: Date;
  endDate: Date;
  startDateISO: string;
  endDateISO: string;
  startDateDisplay: string;
  endDateDisplay: string;
  rangeLabel: string;
  presetOptions: DateRangePresetOption[];
  setPreset: (preset: DateRangePreset) => void;
  setCustomRange: (startDate: Date, endDate: Date) => void;
}

const PRESET_LABELS: Record<DateRangePreset, string> = {
  today: 'Today',
  last_7_days: 'Last 7 days',
  last_30_days: 'Last 30 days',
  this_month: 'This month',
  last_month: 'Last month',
  custom: 'Custom',
};

const PRESET_OPTIONS: DateRangePresetOption[] = [
  { value: 'today', label: 'Today' },
  { value: 'last_7_days', label: 'Last 7 days' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'this_month', label: 'This month' },
  { value: 'last_month', label: 'Last month' },
  { value: 'custom', label: 'Custom' },
];

function startOfDay(date: Date): Date {
  const d = new Date(date);
  d.setUTCHours(0, 0, 0, 0);
  return d;
}

function endOfDay(date: Date): Date {
  const d = new Date(date);
  d.setUTCHours(23, 59, 59, 999);
  return d;
}

function startOfMonth(date: Date): Date {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
  return startOfDay(d);
}

function endOfMonth(date: Date): Date {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0));
  return endOfDay(d);
}

function subtractDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setUTCDate(d.getUTCDate() - days);
  return d;
}

function formatDisplayDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/**
 * Calculate date range based on preset and current date.
 */
function calculatePresetRange(preset: DateRangePreset, now: Date): { start: Date; end: Date } {
  switch (preset) {
    case 'today':
      return { start: startOfDay(now), end: endOfDay(now) };

    case 'last_7_days':
      return { start: startOfDay(subtractDays(now, 7)), end: endOfDay(now) };

    case 'last_30_days':
      return { start: startOfDay(subtractDays(now, 30)), end: endOfDay(now) };

    case 'this_month':
      return { start: startOfMonth(now), end: endOfDay(now) };

    case 'last_month': {
      const lastMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1));
      return { start: startOfMonth(lastMonth), end: endOfMonth(lastMonth) };
    }

    case 'custom':
    default:
      // For custom, return current day as fallback
      return { start: startOfDay(now), end: endOfDay(now) };
  }
}

/**
 * Hook for managing date range selection with presets.
 *
 * Provides preset date ranges (Today, Last 7 days, etc.) and custom range support.
 * All dates are normalized to UTC with start of day/end of day times.
 *
 * @param options - Configuration options including initial preset
 * @returns Date range state and controls
 */
export function useDateRange(options: UseDateRangeOptions = {}): UseDateRangeReturn {
  const { initialPreset = 'last_30_days' } = options;

  const [preset, setPresetState] = useState<DateRangePreset>(initialPreset);
  const [customRange, setCustomRangeState] = useState<{ start: Date; end: Date } | null>(null);

  const { startDate, endDate } = useMemo(() => {
    if (preset === 'custom' && customRange) {
      return { startDate: customRange.start, endDate: customRange.end };
    }
    const now = new Date();
    const range = calculatePresetRange(preset, now);
    return { startDate: range.start, endDate: range.end };
  }, [preset, customRange]);

  const startDateISO = useMemo(() => startDate.toISOString(), [startDate]);
  const endDateISO = useMemo(() => endDate.toISOString(), [endDate]);

  const startDateDisplay = useMemo(() => formatDisplayDate(startDate), [startDate]);
  const endDateDisplay = useMemo(() => formatDisplayDate(endDate), [endDate]);

  const rangeLabel = useMemo(() => {
    if (preset === 'custom') {
      return `${startDateDisplay} - ${endDateDisplay}`;
    }
    return PRESET_LABELS[preset];
  }, [preset, startDateDisplay, endDateDisplay]);

  const setPreset = useCallback((newPreset: DateRangePreset) => {
    setPresetState(newPreset);
    if (newPreset !== 'custom') {
      setCustomRangeState(null);
    }
  }, []);

  const setCustomRange = useCallback((start: Date, end: Date) => {
    setPresetState('custom');
    setCustomRangeState({
      start: startOfDay(start),
      end: endOfDay(end),
    });
  }, []);

  return {
    preset,
    startDate,
    endDate,
    startDateISO,
    endDateISO,
    startDateDisplay,
    endDateDisplay,
    rangeLabel,
    presetOptions: PRESET_OPTIONS,
    setPreset,
    setCustomRange,
  };
}
