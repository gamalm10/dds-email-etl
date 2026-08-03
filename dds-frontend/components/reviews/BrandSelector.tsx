'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
  TextField,
  Autocomplete,
  CircularProgress,
  Box,
  Chip,
} from '@mui/material';

interface Brand {
  id: number;
  division: string;
  brand_category: string;
}

interface Props {
  value: Brand | null;
  onChange: (brand: Brand | null) => void;
}

export default function BrandSelector({ value, onChange }: Props) {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [divisionFilter, setDivisionFilter] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const params = divisionFilter ? `?division=${encodeURIComponent(divisionFilter)}` : '';
    api.get(`v1/brands${params}`)
      .then((res) => setBrands(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [divisionFilter]);

  const divisions = Array.from(new Set(brands.map((b) => b.division))).sort();

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap' }}>
      <Autocomplete
        value={value}
        onChange={(_, v) => onChange(v)}
        options={brands}
        getOptionLabel={(b) => `${b.division} / ${b.brand_category}`}
        groupBy={(b) => b.division}
        loading={loading}
        sx={{ minWidth: 320, flex: 1 }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Select Brand/Category"
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <>
                  {loading ? <CircularProgress size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
      />
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', pt: 1 }}>
        <Chip
          label="All"
          color={divisionFilter === null ? 'primary' : 'default'}
          onClick={() => setDivisionFilter(null)}
          variant={divisionFilter === null ? 'filled' : 'outlined'}
        />
        {divisions.map((d) => (
          <Chip
            key={d}
            label={d}
            color={divisionFilter === d ? 'primary' : 'default'}
            onClick={() => setDivisionFilter(d)}
            variant={divisionFilter === d ? 'filled' : 'outlined'}
          />
        ))}
      </Box>
    </Box>
  );
}
