'use client';
import { Children, type ReactNode } from 'react';
import { Box } from '@mui/material';

// Status / severity keyword -> MUI colour token. Shared by the markdown renderer
// and the database-verify table so answers are consistently colour-coded.
export const STATUS_COLOR_MAP: Record<string, string> = {
  critical: 'error.main', blocked: 'error.main', overdue: 'error.main', delayed: 'error.main',
  cancelled: 'error.main', canceled: 'error.main', red: 'error.main', black: 'error.main',
  major: 'warning.main', warning: 'warning.main', yellow: 'warning.main', pending: 'warning.main',
  green: 'success.main', completed: 'success.main', ready: 'success.main', done: 'success.main',
  resolved: 'success.main',
  minor: 'info.main', info: 'text.secondary', grey: 'text.secondary', gray: 'text.secondary',
  unknown: 'text.secondary',
};

export function colorizeStatusText(text: string): ReactNode {
  const re = new RegExp(`\\b(${Object.keys(STATUS_COLOR_MAP).join('|')})\\b`, 'gi');
  const parts: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(re)) {
    const idx = m.index ?? 0;
    if (idx > last) parts.push(text.slice(last, idx));
    parts.push(
      <Box component="span" key={`${idx}-${m[0]}`} sx={{ color: STATUS_COLOR_MAP[m[0].toLowerCase()], fontWeight: 600 }}>
        {m[0]}
      </Box>,
    );
    last = idx + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : text;
}

export function colorizeStatusChildren(children: ReactNode): ReactNode {
  return Children.map(children, (child) => (typeof child === 'string' ? colorizeStatusText(child) : child));
}
