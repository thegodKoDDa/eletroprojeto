'use client';
import { useLayoutEffect, useRef } from 'react';

/** Hold the last settled geometry only while async work is pending; user disclosures stay natural. */
export function useStableHeight(scope: string, pending: boolean) {
  const ref = useRef<HTMLElement>(null);
  const measured = useRef({ scope, width: 0, height: 0 });
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (measured.current.scope !== scope) measured.current = { scope, width: 0, height: 0 };
    const width = element.getBoundingClientRect().width;
    if (Math.abs(width - measured.current.width) > 1)
      measured.current = { scope, width, height: 0 };
    if (pending) {
      if (measured.current.height) element.style.minHeight = `${measured.current.height}px`;
      return () => {
        element.style.minHeight = '';
      };
    }
    element.style.minHeight = '';
    const measure = () => {
      measured.current = {
        scope,
        width: element.getBoundingClientRect().width,
        height: element.getBoundingClientRect().height,
      };
    };
    measure();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [scope, pending]);
  return ref;
}
