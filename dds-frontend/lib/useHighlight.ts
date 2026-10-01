'use client';
import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

// Deep-link target highlighting. A link appends `?hl=<type>-<id>` and the
// destination page tags the target element with `id="hl-<type>-<id>"`. This
// hook waits for that element (data loads async), scrolls it into view and
// flashes the `hl-flash` style for a few seconds.
export function useHighlightTarget(param = 'hl', durationMs = 4000, timeoutMs = 8000) {
  const value = useSearchParams().get(param);

  useEffect(() => {
    if (!value) return;
    let cancelled = false;
    const started = Date.now();
    const timers: ReturnType<typeof setTimeout>[] = [];

    const find = () => {
      if (cancelled) return;
      const el = document.getElementById(`hl-${value}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('hl-flash');
        timers.push(setTimeout(() => el.classList.remove('hl-flash'), durationMs));
      } else if (Date.now() - started < timeoutMs) {
        timers.push(setTimeout(find, 150));
      }
    };

    find();
    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
    };
  }, [value, param, durationMs, timeoutMs]);
}
