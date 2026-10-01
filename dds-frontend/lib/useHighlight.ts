'use client';
import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

// Deep-link target highlighting. A link appends `?hl=<type>-<id>` and the
// destination page tags the target element with `id="hl-<type>-<id>"`.
//
// The target blinks a few times (`hl-flash`), then keeps a persistent static
// highlight (`hl-mark`) until the user navigates away or clicks another link.
// It is scrolled to the top of the view (just below the fixed header) and
// re-aligned for a short settle window if late data/layout shifts move it.
const SETTLE_MS = 2500;
const TOP_MARGIN = 88; // fixed AppBar (64px) + breathing room
const ALIGN_TOLERANCE = 100;

export function useHighlightTarget(param = 'hl', timeoutMs = 15000) {
  const value = useSearchParams().get(param);

  useEffect(() => {
    if (!value) return;
    const targetId = `hl-${value}`;
    let cancelled = false;
    let foundAt = 0;
    let lastScrollAt = 0;
    let lastObserve = 0;
    let realigns = 0;
    const intervals: ReturnType<typeof setInterval>[] = [];
    const timeouts: ReturnType<typeof setTimeout>[] = [];

    const clearMarks = () => {
      document.querySelectorAll('.hl-mark, .hl-flash').forEach((el) => el.classList.remove('hl-mark', 'hl-flash'));
    };

    // "Aligned" means the target's top is at (or near) the top of the usable view.
    const isAligned = (el: HTMLElement) => {
      const r = el.getBoundingClientRect();
      if (r.height <= 0) return false;
      return r.top >= TOP_MARGIN - 8 && r.top <= TOP_MARGIN + ALIGN_TOLERANCE;
    };

    const scrollTopAlign = (el: HTMLElement) => {
      const r = el.getBoundingClientRect();
      const scroller = document.scrollingElement || document.documentElement;
      const top = (scroller.scrollTop || window.scrollY) + r.top - TOP_MARGIN;
      window.scrollTo({ top: Math.max(top, 0), behavior: 'smooth' });
    };

    const bringIntoView = (el: HTMLElement) => {
      lastScrollAt = Date.now();
      // Scroll ancestors first (nested containers), then align under the header.
      el.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
      timeouts.push(setTimeout(() => {
        if (cancelled || isAligned(el)) return;
        scrollTopAlign(el);
      }, 350));
    };

    const ensure = () => {
      const el = document.getElementById(targetId);
      if (!el) return false;

      const first = foundAt === 0;
      if (first) {
        foundAt = Date.now();
        bringIntoView(el);
      }

      if (!el.classList.contains('hl-mark')) el.classList.add('hl-mark');
      // Blink only once (not on every re-render that recreates the node).
      if (first && !el.classList.contains('hl-flash')) el.classList.add('hl-flash');

      // Keep it at the top while the page settles (capped so it can't loop at
      // the bottom of the page where the target can't reach the top).
      if (Date.now() - foundAt < SETTLE_MS && !isAligned(el) && Date.now() - lastScrollAt > 500 && realigns < 4) {
        realigns++;
        bringIntoView(el);
      }
      return true;
    };

    clearMarks();
    if (!ensure()) {
      const started = Date.now();
      const poll = setInterval(() => {
        if (cancelled || ensure() || Date.now() - started > timeoutMs) clearInterval(poll);
      }, 150);
      intervals.push(poll);
    }

    const observer = new MutationObserver(() => {
      const now = Date.now();
      if (now - lastObserve < 200) return;
      lastObserve = now;
      if (!cancelled) ensure();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Clicking a link back to the same target keeps the URL unchanged, so the
    // effect would not re-run; re-blink and re-scroll explicitly in that case.
    const onClick = (e: MouseEvent) => {
      const anchor = (e.target as HTMLElement | null)?.closest?.('a[href]') as HTMLAnchorElement | null;
      if (!anchor) return;
      const match = (anchor.getAttribute('href') || '').match(/[?&]hl=([^&]+)/);
      if (match && decodeURIComponent(match[1]) === value) {
        foundAt = 0;
        realigns = 0;
        clearMarks();
        ensure();
      }
    };
    document.addEventListener('click', onClick);

    return () => {
      cancelled = true;
      intervals.forEach(clearInterval);
      timeouts.forEach(clearTimeout);
      observer.disconnect();
      document.removeEventListener('click', onClick);
      clearMarks();
    };
  }, [value, param, timeoutMs]);
}
