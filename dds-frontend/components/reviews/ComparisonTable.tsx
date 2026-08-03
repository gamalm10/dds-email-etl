'use client';

import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Skeleton,
} from '@mui/material';
import ArrowForward from '@mui/icons-material/ArrowForward';

interface Props {
  comparison: any;
  loading: boolean;
}

const COLOR_CHIP: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  green: 'success',
  yellow: 'warning',
  red: 'error',
  blue: 'info',
  unknown: 'default',
};

export default function ComparisonTable({ comparison, loading }: Props) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} variant="rectangular" height={40} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!comparison) return null;

  const { summary, report_1, report_2 } = comparison;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <Chip label={`Total: ${summary.total_brands} brands`} variant="outlined" />
          <Chip label={`Changed: ${summary.changed_count}`} color="warning" variant="outlined" />
          <Chip label={`Unchanged: ${summary.unchanged_count}`} color="success" variant="outlined" />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {report_1.report_date} ({report_1.subject.slice(0, 60)}) vs {report_2.report_date} ({report_2.subject.slice(0, 60)})
        </Typography>

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Brand</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Report 1 Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}></TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Report 2 Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Change</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparison.comparison.map((row: any, i: number) => {
                const avail1 = row.report_1?.availability;
                const avail2 = row.report_2?.availability;
                const ms1 = row.report_1?.milestone;
                const ms2 = row.report_2?.milestone;

                return (
                  <TableRow
                    key={i}
                    sx={{
                      backgroundColor: row.changed ? 'action.hover' : 'inherit',
                    }}
                  >
                    <TableCell sx={{ fontWeight: 500 }}>{row.brand_category}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
                        {avail1 && <Chip size="small" color={COLOR_CHIP[avail1] || 'default'} label={avail1} />}
                        {ms1 && <Typography variant="caption">{ms1.slice(0, 20)}</Typography>}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ textAlign: 'center' }}>
                      {row.changed && <ArrowForward color="warning" fontSize="small" />}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
                        {avail2 && <Chip size="small" color={COLOR_CHIP[avail2] || 'default'} label={avail2} />}
                        {ms2 && <Typography variant="caption">{ms2.slice(0, 20)}</Typography>}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {row.changed ? (
                        <Chip size="small" color="warning" label="Changed" />
                      ) : (
                        <Chip size="small" variant="outlined" label="Same" />
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}
