import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadBook, type UploadBookResponse } from '@/api/books';
import type { ApiError } from '@/api/client';

/**
 * Upload stage states for tracking the upload process
 */
export type UploadStage =
  | 'idle'
  | 'uploading'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'done'
  | 'error';

/**
 * Ordered stages for progress tracking (excludes idle, done, error)
 */
export const UPLOAD_STAGES_ORDER: UploadStage[] = [
  'uploading',
  'parsing',
  'chunking',
  'embedding',
];

/**
 * Custom hook for uploading books with progress tracking.
 *
 * Features:
 * - Upload progress tracking (0-100%)
 * - Stage transitions (uploading → parsing → done/error)
 * - TanStack Query integration for cache invalidation
 * - Reset functionality
 */
export function useUploadBook() {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<UploadStage>('idle');
  const queryClient = useQueryClient();

  const mutation = useMutation<UploadBookResponse, ApiError, File>({
    mutationFn: async (file: File) => {
      setStage('uploading');
      setProgress(0);

      const result = await uploadBook(file, {
        onProgress: (percent) => {
          setProgress(percent);
          if (percent === 100) {
            // Backend processes: parsing → chunking → embedding
            // These happen server-side, we show indeterminate progress
            setStage('parsing');
          }
        },
      });

      return result;
    },
    onSuccess: () => {
      setStage('done');
      setProgress(100);
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
    onError: () => {
      setStage('error');
    },
  });

  const reset = useCallback(() => {
    setProgress(0);
    setStage('idle');
    mutation.reset();
  }, [mutation]);

  return {
    upload: mutation.mutate,
    isUploading: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    progress,
    stage,
    reset,
    data: mutation.data,
  };
}
