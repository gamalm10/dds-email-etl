import type { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime';

export function navigate(router: AppRouterInstance, path: string) {
  router.push(path);
}
