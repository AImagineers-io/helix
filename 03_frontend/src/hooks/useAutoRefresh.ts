import { useState, useEffect, useCallback, useRef } from 'react';

export interface UseAutoRefreshOptions {
  /** Interval in milliseconds (default: 60000 = 60 seconds) */
  intervalMs?: number;
  /** Whether auto-refresh is enabled initially (default: true) */
  enabled?: boolean;
}

export interface UseAutoRefreshReturn {
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
  /** Whether auto-refresh is enabled */
  isEnabled: boolean;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Enable or disable auto-refresh */
  setEnabled: (enabled: boolean) => void;
}

const DEFAULT_INTERVAL_MS = 60000;

/**
 * Hook for auto-refreshing data at regular intervals.
 *
 * Features:
 * - Configurable refresh interval (default: 60 seconds)
 * - Manual refresh with automatic timer reset
 * - Pause when tab is hidden, resume when visible
 * - Immediate refresh when returning to stale tab
 * - Error resilience (continues refreshing after failures)
 *
 * @param onRefresh - Async function to call on each refresh
 * @param options - Configuration options
 * @returns Object with refresh state and controls
 */
export function useAutoRefresh(
  onRefresh: () => Promise<void>,
  options: UseAutoRefreshOptions = {}
): UseAutoRefreshReturn {
  const { intervalMs = DEFAULT_INTERVAL_MS, enabled: initialEnabled = true } = options;

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isEnabled, setIsEnabled] = useState(initialEnabled);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastRefreshRef = useRef<number>(Date.now());
  const onRefreshRef = useRef(onRefresh);

  // Keep onRefresh ref updated to avoid stale closures
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  const clearRefreshInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await onRefreshRef.current();
      lastRefreshRef.current = Date.now();
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const startRefreshInterval = useCallback(() => {
    clearRefreshInterval();
    intervalRef.current = setInterval(async () => {
      try {
        await refresh();
      } catch {
        // Continue auto-refresh even if one refresh fails
      }
    }, intervalMs);
  }, [clearRefreshInterval, refresh, intervalMs]);

  // Handle visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab is hidden - stop auto-refresh
        clearRefreshInterval();
      } else if (isEnabled) {
        // Tab is visible again
        const timeSinceLastRefresh = Date.now() - lastRefreshRef.current;
        if (timeSinceLastRefresh >= intervalMs) {
          // Data is stale, refresh immediately
          refresh().catch(() => {
            // Ignore errors, auto-refresh will continue
          });
        }
        // Restart the interval
        startRefreshInterval();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isEnabled, intervalMs, clearRefreshInterval, startRefreshInterval, refresh]);

  // Start/stop auto-refresh based on enabled state
  useEffect(() => {
    if (isEnabled && !document.hidden) {
      startRefreshInterval();
    } else {
      clearRefreshInterval();
    }

    return () => {
      clearRefreshInterval();
    };
  }, [isEnabled, startRefreshInterval, clearRefreshInterval]);

  // Reset interval after manual refresh
  const refreshWithReset = useCallback(async () => {
    await refresh();
    if (isEnabled && !document.hidden) {
      startRefreshInterval();
    }
  }, [refresh, isEnabled, startRefreshInterval]);

  return {
    isRefreshing,
    isEnabled,
    refresh: refreshWithReset,
    setEnabled: setIsEnabled,
  };
}
