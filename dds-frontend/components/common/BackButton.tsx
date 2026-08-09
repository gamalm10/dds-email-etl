'use client';
import { useRouter } from 'next/navigation';
import { IconButton } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';

export default function BackButton({ fallback = '/' }: { fallback?: string }) {
  const router = useRouter();

  const handleBack = () => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push(fallback);
    }
  };

  return (
    <IconButton onClick={handleBack}><ArrowBack /></IconButton>
  );
}
