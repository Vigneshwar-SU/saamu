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

export interface CustomerNameSource {
  full_name: string;
  notes?: string | null;
}

/**
 * Staff-facing customer name with the internal note appended in parentheses.
 *
 * Centralised so every internal screen (orders, invoices, payments, work
 * assignments, reminders, reports) labels a customer identically. This is
 * intentionally for staff/owner screens only: `notes` are internal working
 * notes and must never leak into customer-facing output such as printed bills
 * or WhatsApp messages.
 */
export const formatCustomerNameWithNotes = (customer: CustomerNameSource): string => {
  const name = (customer?.full_name ?? '').trim();
  const notes = (customer?.notes ?? '').trim();
  if (!notes) return name;
  return `${name} (${notes})`;
};

/** Convenience overload for screens that already hold name and notes apart. */
export const formatNameWithNotes = (fullName: string, notes?: string | null): string =>
  formatCustomerNameWithNotes({ full_name: fullName, notes });
