const MOBILE_SEPARATORS = /[\s\-()./]+/g;

export function normalizeFullName(value: string): string {
  return value
    .trim()
    .replace(/\s+/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function normalizeMobileNumber(value: string): string {
  const cleaned = value.trim().replace(MOBILE_SEPARATORS, '');
  if (!cleaned) return '';
  if (cleaned.startsWith('+')) {
    const digits = cleaned.slice(1);
    return /^[0-9]{7,15}$/.test(digits) ? `+${digits}` : cleaned;
  }
  if (/^[6-9][0-9]{9}$/.test(cleaned)) {
    return `+91${cleaned}`;
  }
  if (/^0[6-9][0-9]{9}$/.test(cleaned)) {
    return `+91${cleaned.slice(1)}`;
  }
  return cleaned;
}
