'use client';
import { isValidElement, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import ChartBlock from './ChartBlock';
import { colorizeStatusChildren as colorizeChildren } from '@/lib/statusColors';

const inlineCodeSx = {
  px: 0.5, py: 0.1, borderRadius: 0.5, bgcolor: 'action.hover',
  fontFamily: 'monospace', fontSize: '0.8em',
};

const blockCodeSx = {
  p: 1, my: 1, borderRadius: 1, bgcolor: 'action.hover', overflowX: 'auto',
  fontFamily: 'monospace', fontSize: '0.75rem', lineHeight: 1.5, maxWidth: '100%',
};

const tableCellSx = { fontSize: '0.72rem', py: 0.5, px: 0.75, whiteSpace: 'nowrap' };

function MarkdownMessage({ content }: { content: string }) {
  return (
    <Box dir="auto" sx={{ maxWidth: '100%', fontSize: '0.875rem', lineHeight: 1.6, '& > :first-of-type': { mt: 0 } }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }: any) => <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main', mt: 1.5, mb: 0.5 }}>{children}</Typography>,
          h2: ({ children }: any) => <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main', mt: 1.5, mb: 0.5 }}>{children}</Typography>,
          h3: ({ children }: any) => <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 1.25, mb: 0.5 }}>{children}</Typography>,
          h4: ({ children }: any) => <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 1, mb: 0.5 }}>{children}</Typography>,
          p: ({ children }: any) => <Typography component="p" variant="body2" sx={{ mb: 0.75, lineHeight: 1.6 }}>{colorizeChildren(children)}</Typography>,
          strong: ({ children }: any) => <Box component="strong" sx={{ fontWeight: 700 }}>{colorizeChildren(children)}</Box>,
          em: ({ children }: any) => <Box component="em">{children}</Box>,
          ul: ({ children }: any) => <Box component="ul" sx={{ pl: 2.5, my: 0.5 }}>{children}</Box>,
          ol: ({ children }: any) => <Box component="ol" sx={{ pl: 2.5, my: 0.5 }}>{children}</Box>,
          li: ({ children }: any) => <Box component="li" sx={{ mb: 0.25, '&::marker': { color: 'primary.main' } }}>{colorizeChildren(children)}</Box>,
          blockquote: ({ children }: any) => (
            <Box sx={{ borderLeft: 3, borderColor: 'primary.main', pl: 1.5, my: 1, color: 'text.secondary' }}>{children}</Box>
          ),
          hr: () => <Box component="hr" sx={{ border: 0, borderTop: 1, borderColor: 'divider', my: 1.5 }} />,
          a: ({ href, children }: any) => {
            const url = href || '#';
            if (url.startsWith('/')) {
              return <Link href={url} style={{ color: 'inherit', textDecoration: 'underline' }}>{children}</Link>;
            }
            return <a href={url} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>{children}</a>;
          },
          img: ({ src, alt }: any) => (
            <Box component="img" src={src} alt={alt || ''} sx={{ maxWidth: '100%', borderRadius: 1, my: 1, display: 'block' }} />
          ),
          code: ({ className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const text = String(children ?? '').replace(/\n$/, '');
            if (match?.[1] === 'chart') {
              try {
                return <ChartBlock spec={JSON.parse(text)} />;
              } catch {
                return (
                  <Box sx={{ my: 1, p: 1, border: 1, borderColor: 'divider', borderRadius: 1, color: 'text.secondary' }}>
                    <Typography variant="caption">Preparing chart…</Typography>
                  </Box>
                );
              }
            }
            if (match) return <code className={className} {...props}>{children}</code>;
            return <Box component="code" sx={inlineCodeSx} {...props}>{children}</Box>;
          },
          pre: ({ children }: any) => {
            const child: any = Array.isArray(children) ? children[0] : children;
            if (isValidElement(child) && child.type === ChartBlock) return <>{child}</>;
            return <Box component="pre" sx={blockCodeSx}>{children}</Box>;
          },
          table: ({ children }: any) => (
            <TableContainer component={Paper} variant="outlined" sx={{ width: '100%', my: 1, overflowX: 'auto' }}>
              <Table size="small" sx={{ '& th, & td': tableCellSx }}>{children}</Table>
            </TableContainer>
          ),
          thead: ({ children }: any) => <TableHead>{children}</TableHead>,
          tbody: ({ children }: any) => <TableBody>{children}</TableBody>,
          tr: ({ children }: any) => <TableRow>{children}</TableRow>,
          th: ({ children }: any) => <TableCell sx={{ fontWeight: 700, bgcolor: 'action.hover' }}>{colorizeChildren(children)}</TableCell>,
          td: ({ children }: any) => <TableCell>{colorizeChildren(children)}</TableCell>,
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
}

export default memo(MarkdownMessage);
