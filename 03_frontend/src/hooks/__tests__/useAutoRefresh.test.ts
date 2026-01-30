import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAutoRefresh } from '../useAutoRefresh';

describe('useAutoRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should start with isRefreshing false', () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh));

      expect(result.current.isRefreshing).toBe(false);
    });

    it('should start with auto-refresh enabled by default', () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh));

      expect(result.current.isEnabled).toBe(true);
    });
  });

  describe('auto-refresh behavior', () => {
    it('should call onRefresh after default interval (60 seconds)', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh));

      expect(onRefresh).not.toHaveBeenCalled();

      await act(async () => {
        vi.advanceTimersByTime(60000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('should call onRefresh after custom interval', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 30000 }));

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('should call onRefresh multiple times over intervals', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(3);
    });
  });

  describe('manual refresh', () => {
    it('should allow manual refresh via refresh function', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh));

      await act(async () => {
        await result.current.refresh();
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('should set isRefreshing to true during refresh', async () => {
      let resolveRefresh: () => void;
      const onRefresh = vi.fn().mockImplementation(() => {
        return new Promise<void>((resolve) => {
          resolveRefresh = resolve;
        });
      });

      const { result } = renderHook(() => useAutoRefresh(onRefresh));

      let refreshPromise: Promise<void>;
      act(() => {
        refreshPromise = result.current.refresh();
      });

      expect(result.current.isRefreshing).toBe(true);

      await act(async () => {
        resolveRefresh!();
        await refreshPromise;
      });

      expect(result.current.isRefreshing).toBe(false);
    });

    it('should reset interval timer after manual refresh', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 60000 }));

      // Wait 50 seconds
      await act(async () => {
        vi.advanceTimersByTime(50000);
      });

      // Manual refresh
      await act(async () => {
        await result.current.refresh();
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);

      // Wait another 30 seconds (would have triggered if not reset)
      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);

      // Wait remaining 30 seconds to complete new interval
      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(2);
    });
  });

  describe('enable/disable auto-refresh', () => {
    it('should stop auto-refresh when disabled', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      act(() => {
        result.current.setEnabled(false);
      });

      expect(result.current.isEnabled).toBe(false);

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).not.toHaveBeenCalled();
    });

    it('should resume auto-refresh when re-enabled', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      act(() => {
        result.current.setEnabled(false);
      });

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).not.toHaveBeenCalled();

      act(() => {
        result.current.setEnabled(true);
      });

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('should allow starting with auto-refresh disabled', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() =>
        useAutoRefresh(onRefresh, { intervalMs: 10000, enabled: false })
      );

      expect(result.current.isEnabled).toBe(false);

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).not.toHaveBeenCalled();
    });
  });

  describe('tab visibility handling', () => {
    it('should pause auto-refresh when tab is hidden', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      // Simulate tab becoming hidden
      Object.defineProperty(document, 'hidden', { value: true, writable: true });
      document.dispatchEvent(new Event('visibilitychange'));

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).not.toHaveBeenCalled();

      // Restore visibility
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
    });

    it('should resume auto-refresh when tab becomes visible again', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      // Hide tab for less than interval (so not considered stale)
      Object.defineProperty(document, 'hidden', { value: true, writable: true });
      document.dispatchEvent(new Event('visibilitychange'));

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      expect(onRefresh).not.toHaveBeenCalled();

      // Show tab again
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
      document.dispatchEvent(new Event('visibilitychange'));

      // No immediate refresh (not stale)
      expect(onRefresh).not.toHaveBeenCalled();

      // Wait for interval to trigger
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);

      // Restore
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
    });

    it('should trigger immediate refresh when tab becomes visible if stale', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      // Hide tab
      Object.defineProperty(document, 'hidden', { value: true, writable: true });
      document.dispatchEvent(new Event('visibilitychange'));

      // Time passes while hidden
      await act(async () => {
        vi.advanceTimersByTime(60000);
      });

      // Show tab again - should trigger immediate refresh due to stale data
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
      await act(async () => {
        document.dispatchEvent(new Event('visibilitychange'));
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);

      // Restore
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
    });
  });

  describe('cleanup', () => {
    it('should clear interval on unmount', async () => {
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { unmount } = renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      unmount();

      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      expect(onRefresh).not.toHaveBeenCalled();
    });

    it('should remove visibility listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');
      const onRefresh = vi.fn().mockResolvedValue(undefined);
      const { unmount } = renderHook(() => useAutoRefresh(onRefresh));

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('error handling', () => {
    it('should set isRefreshing to false even if refresh fails', async () => {
      const onRefresh = vi.fn().mockRejectedValue(new Error('Refresh failed'));
      const { result } = renderHook(() => useAutoRefresh(onRefresh));

      await act(async () => {
        try {
          await result.current.refresh();
        } catch {
          // Expected to fail
        }
      });

      expect(result.current.isRefreshing).toBe(false);
    });

    it('should continue auto-refresh after a failed refresh', async () => {
      const onRefresh = vi.fn()
        .mockRejectedValueOnce(new Error('Refresh failed'))
        .mockResolvedValue(undefined);

      renderHook(() => useAutoRefresh(onRefresh, { intervalMs: 10000 }));

      // First interval - fails
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(1);

      // Second interval - succeeds
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(onRefresh).toHaveBeenCalledTimes(2);
    });
  });
});
