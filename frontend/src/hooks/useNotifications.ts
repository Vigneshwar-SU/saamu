import { useMemo } from 'react';
import { useReminderV1List, useReminderV1Summary } from './useReminderV1';
import type { ReminderV1Candidate, ReminderV1Type } from '../types/remindersV1';
import type { StatusTone } from '../components/ui/StatusBadge';

export interface NotificationGroup {
  reminderType: ReminderV1Type;
  label: string;
  count: number;
  subtitle: string;
  tone: StatusTone;
  path: string;
  items: ReminderV1Candidate[];
}

const REMINDER_V1_DISPLAY_ORDER: ReminderV1Type[] = [
  'OVERDUE_ORDER',
  'ORDER_DUE_TODAY',
  'ORDER_DUE_TOMORROW',
  'READY_FOR_PICKUP',
  'PAYMENT_OUTSTANDING',
  'TAILOR_WORKLOAD',
  'MEASUREMENT_MISSING',
  'CUSTOMER_FOLLOW_UP',
  'MANUAL_REMINDER',
];

const REMINDER_V1_META: Record<
  ReminderV1Type,
  { label: string; pluralLabel: string; subtitle: string; tone: StatusTone }
> = {
  OVERDUE_ORDER: {
    label: 'Overdue Order',
    pluralLabel: 'Overdue Orders',
    subtitle: 'Orders requiring immediate attention',
    tone: 'error',
  },
  ORDER_DUE_TODAY: {
    label: 'Order Due Today',
    pluralLabel: 'Orders Due Today',
    subtitle: "Check today's deliveries",
    tone: 'warning',
  },
  ORDER_DUE_TOMORROW: {
    label: 'Order Due Tomorrow',
    pluralLabel: 'Orders Due Tomorrow',
    subtitle: 'Expected deliveries tomorrow',
    tone: 'warning',
  },
  READY_FOR_PICKUP: {
    label: 'Ready for Pickup',
    pluralLabel: 'Ready for Pickup',
    subtitle: 'Customers can be contacted',
    tone: 'success',
  },
  PAYMENT_OUTSTANDING: {
    label: 'Payment Outstanding',
    pluralLabel: 'Payments Outstanding',
    subtitle: 'Payments requiring attention',
    tone: 'warning',
  },
  TAILOR_WORKLOAD: {
    label: 'Tailor Workload Pending',
    pluralLabel: 'Tailor Workload Pending',
    subtitle: 'Tailors with unfinished pieces',
    tone: 'warning',
  },
  MEASUREMENT_MISSING: {
    label: 'Measurement Missing',
    pluralLabel: 'Measurements Missing',
    subtitle: 'Orders missing measurement data',
    tone: 'warning',
  },
  CUSTOMER_FOLLOW_UP: {
    label: 'Customer Follow-up',
    pluralLabel: 'Customer Follow-ups',
    subtitle: 'Customers due a follow-up',
    tone: 'info',
  },
  MANUAL_REMINDER: {
    label: 'Manual Reminder',
    pluralLabel: 'Manual Reminders',
    subtitle: 'Manual reminders to action',
    tone: 'warning',
  },
};

function resolveNavigationPath(reminderType: ReminderV1Type, items: ReminderV1Candidate[]): string {
  const single = items.length === 1 ? items[0] : null;
  switch (reminderType) {
    case 'OVERDUE_ORDER':
    case 'ORDER_DUE_TODAY':
    case 'ORDER_DUE_TOMORROW':
    case 'READY_FOR_PICKUP':
    case 'MEASUREMENT_MISSING':
      if (single?.order) return `/orders/${single.order.id}`;
      return '/orders';
    case 'PAYMENT_OUTSTANDING':
      if (single?.order) return `/orders/${single.order.id}`;
      return '/payments';
    case 'TAILOR_WORKLOAD':
      if (single?.tailor) return `/tailors/${single.tailor.id}`;
      return '/tailors';
    case 'CUSTOMER_FOLLOW_UP':
      if (single?.customer) return `/customers/${single.customer.id}`;
      return '/customers';
    case 'MANUAL_REMINDER':
      return '/reminders';
  }
}

/**
 * Notification data for the header bell, derived entirely from the backend
 * Reminders V1 endpoints (never computed on the client).
 *
 * Group counts come from the authoritative summary endpoint; the list results
 * only provide the individual records used for direct navigation when a group
 * has exactly one candidate.
 */
export const useNotifications = () => {
  const summaryQuery = useReminderV1Summary();
  const listQuery = useReminderV1List();

  const groups = useMemo<NotificationGroup[]>(() => {
    const itemsByType = new Map<ReminderV1Type, ReminderV1Candidate[]>();
    for (const item of listQuery.data?.results ?? []) {
      const existing = itemsByType.get(item.reminder_type) ?? [];
      existing.push(item);
      itemsByType.set(item.reminder_type, existing);
    }

    const derived: NotificationGroup[] = [];
    for (const reminderType of REMINDER_V1_DISPLAY_ORDER) {
      const count = summaryQuery.data?.by_type[reminderType] ?? 0;
      if (count <= 0) continue;
      const items = itemsByType.get(reminderType) ?? [];
      const meta = REMINDER_V1_META[reminderType];
      derived.push({
        reminderType,
        label: count > 1 ? meta.pluralLabel : meta.label,
        count,
        subtitle: meta.subtitle,
        tone: meta.tone,
        path: resolveNavigationPath(reminderType, items),
        items,
      });
    }
    return derived;
  }, [listQuery.data, summaryQuery.data]);

  const badgeCount = summaryQuery.data?.total ?? 0;

  const isLoading =
    !summaryQuery.data && !listQuery.data && (summaryQuery.isLoading || listQuery.isLoading);
  const isError =
    !summaryQuery.data && !listQuery.data && (summaryQuery.isError || listQuery.isError);

  return {
    groups,
    badgeCount,
    isLoading,
    isError,
    refetch: () => {
      void summaryQuery.refetch();
      void listQuery.refetch();
    },
  };
};
