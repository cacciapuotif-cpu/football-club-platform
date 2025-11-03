/**
 * Error handling utility to prevent React #31 (rendering non-string objects)
 * Converts errors to user-friendly messages
 */

import { AxiosError } from 'axios';

/**
 * Converts any error to a user-friendly string message
 * @param err - The error to convert
 * @returns User-friendly error message
 */
export function toUserMessage(err: unknown): string {
  const anyErr = err as any;

  // Handle Axios errors
  if (anyErr?.isAxiosError) {
    const e = err as AxiosError<any>;
    const status = e.response?.status;
    const detail = e.response?.data?.detail;
    const message = e.response?.data?.message;
    const errorMsg = detail || message || e.message || 'Request failed';

    if (status) {
      return `${status} – ${errorMsg}`;
    }
    return errorMsg;
  }

  // Handle standard Error objects
  if (err instanceof Error) {
    return err.message;
  }

  // Handle objects with message property
  if (anyErr && typeof anyErr === 'object' && 'message' in anyErr) {
    return String(anyErr.message);
  }

  // Handle strings
  if (typeof err === 'string') {
    return err;
  }

  // Fallback: try to stringify or convert to string
  try {
    return JSON.stringify(anyErr);
  } catch {
    return String(anyErr);
  }
}

/**
 * Safe error renderer for React components
 * Usage: {error && <div>{renderError(error)}</div>}
 */
export function renderError(err: unknown): string {
  return toUserMessage(err);
}

export default { toUserMessage, renderError };
