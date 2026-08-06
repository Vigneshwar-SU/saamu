export function extractDownloadFilename(
  headers: Record<string, unknown> | undefined,
  fallback: string
): string {
  if (!headers) return fallback;
  const value =
    headers['content-disposition'] ?? headers['Content-Disposition'];
  if (typeof value !== 'string') return fallback;
  const match = value.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : fallback;
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
