/**
 * Build version tracking for diagnostics
 */

export const BUILD_TAG = process.env.NEXT_PUBLIC_BUILD_TAG || 'dev-unknown';
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function logVersionInfo(component: string) {
  console.info(`[${component}] Build: ${BUILD_TAG}, API: ${API_URL}`);
}
