import dayjs from 'dayjs';

export const formatDate = (date: string | Date, format = 'DD MMM YYYY'): string => {
  if (!date) return '';
  return dayjs(date).format(format);
};

export const formatCurrency = (amount: number, currency = 'INR'): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatPieces = (quantity: number): string => {
  const value = Math.trunc(Number(quantity));
  if (!Number.isFinite(value)) return '0 pcs';
  const clamped = Math.max(0, value);
  return `${clamped} pc${clamped === 1 ? '' : 's'}`;
};
