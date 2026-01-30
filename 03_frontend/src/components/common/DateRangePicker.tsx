import { useState, useRef, useEffect, useCallback } from 'react';
import type { DateRangePreset } from '../../hooks/useDateRange';

export interface DateRangePickerProps {
  preset: DateRangePreset;
  rangeLabel: string;
  startDate: Date;
  endDate: Date;
  onPresetChange: (preset: DateRangePreset) => void;
  onCustomRangeChange: (startDate: Date, endDate: Date) => void;
  disabled?: boolean;
}

const PRESET_OPTIONS: { value: DateRangePreset; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: 'last_7_days', label: 'Last 7 days' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'this_month', label: 'This month' },
  { value: 'last_month', label: 'Last month' },
  { value: 'custom', label: 'Custom' },
];

function formatDateForInput(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function DateRangePicker({
  preset,
  rangeLabel,
  startDate,
  endDate,
  onPresetChange,
  onCustomRangeChange,
  disabled = false,
}: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCustomInputs, setShowCustomInputs] = useState(false);
  const [customStart, setCustomStart] = useState(formatDateForInput(startDate));
  const [customEnd, setCustomEnd] = useState(formatDateForInput(endDate));

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Update custom inputs when dates change externally
  useEffect(() => {
    setCustomStart(formatDateForInput(startDate));
    setCustomEnd(formatDateForInput(endDate));
  }, [startDate, endDate]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowCustomInputs(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleToggle = useCallback(() => {
    if (!disabled) {
      setIsOpen((prev) => !prev);
      if (isOpen) {
        setShowCustomInputs(false);
      }
    }
  }, [disabled, isOpen]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleToggle();
      } else if (e.key === 'Escape') {
        setIsOpen(false);
        setShowCustomInputs(false);
      }
    },
    [handleToggle]
  );

  const handleListKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setShowCustomInputs(false);
    }
  }, []);

  const handlePresetClick = useCallback(
    (presetValue: DateRangePreset) => {
      if (presetValue === 'custom') {
        setShowCustomInputs(true);
      } else {
        onPresetChange(presetValue);
        setIsOpen(false);
        setShowCustomInputs(false);
      }
    },
    [onPresetChange]
  );

  const isValidRange = useCallback(() => {
    return customStart && customEnd && new Date(customStart) <= new Date(customEnd);
  }, [customStart, customEnd]);

  const handleApplyCustomRange = useCallback(() => {
    if (isValidRange()) {
      onCustomRangeChange(new Date(customStart), new Date(customEnd));
      setIsOpen(false);
      setShowCustomInputs(false);
    }
  }, [customStart, customEnd, onCustomRangeChange, isValidRange]);

  return (
    <div ref={dropdownRef} className="date-range-picker" style={{ position: 'relative', display: 'inline-block' }}>
      <button
        type="button"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-label="Date range selector"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        style={{
          padding: '8px 16px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          background: disabled ? '#f5f5f5' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          minWidth: '200px',
        }}
      >
        <span>{rangeLabel}</span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          style={{ marginLeft: 'auto', transform: isOpen ? 'rotate(180deg)' : 'none' }}
        >
          <path d="M2 4L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>

      {isOpen && (
        <div
          role="listbox"
          onKeyDown={handleListKeyDown}
          tabIndex={-1}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '4px',
            background: 'white',
            border: '1px solid #ccc',
            borderRadius: '4px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            minWidth: '200px',
            zIndex: 1000,
          }}
        >
          {!showCustomInputs ? (
            <ul style={{ listStyle: 'none', margin: 0, padding: '4px 0' }}>
              {PRESET_OPTIONS.map((option) => (
                <li
                  key={option.value}
                  role="option"
                  aria-selected={preset === option.value}
                  onClick={() => handlePresetClick(option.value)}
                  style={{
                    padding: '8px 16px',
                    cursor: 'pointer',
                    background: preset === option.value ? '#e6f7ff' : 'transparent',
                    fontWeight: preset === option.value ? 600 : 400,
                  }}
                  onMouseEnter={(e) => {
                    if (preset !== option.value) {
                      e.currentTarget.style.background = '#f5f5f5';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = preset === option.value ? '#e6f7ff' : 'transparent';
                  }}
                >
                  {option.label}
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ padding: '16px' }}>
              <div style={{ marginBottom: '12px' }}>
                <label htmlFor="date-range-start" style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>
                  Start date
                </label>
                <input
                  id="date-range-start"
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                  }}
                />
              </div>
              <div style={{ marginBottom: '12px' }}>
                <label htmlFor="date-range-end" style={{ display: 'block', marginBottom: '4px', fontSize: '14px' }}>
                  End date
                </label>
                <input
                  id="date-range-end"
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                  }}
                />
              </div>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowCustomInputs(false)}
                  style={{
                    padding: '8px 16px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    background: 'white',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleApplyCustomRange}
                  disabled={!isValidRange()}
                  style={{
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '4px',
                    background: isValidRange() ? '#1890ff' : '#d9d9d9',
                    color: 'white',
                    cursor: isValidRange() ? 'pointer' : 'not-allowed',
                  }}
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
