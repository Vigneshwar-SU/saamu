import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import AddCardIcon from '@mui/icons-material/AddCard';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { ExpenseFormDialog } from '../components/ExpenseFormDialog';
import { useCreateExpense, useExpenseList, useExpenseSummary } from '../hooks/useFinance';
import {
  EXPENSE_CATEGORIES,
  EXPENSE_CATEGORY_LABELS,
  PAYMENT_METHODS,
  PAYMENT_METHOD_LABELS,
} from '../types/finance';
import type { ExpenseCategory, ExpensePayload, PaymentMethod } from '../types/finance';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatCard } from '../components/ui/StatCard';
import { StatusBadge } from '../components/ui/StatusBadge';

const PAGE_SIZE = 6;

export const Expenses: React.FC = () => {
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<ExpenseCategory | ''>('');
  const [paymentMethodFilter, setPaymentMethodFilter] = useState<PaymentMethod | ''>('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [dateFrom, dateTo, categoryFilter, paymentMethodFilter]);

  const filterParams = {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    category: categoryFilter || undefined,
    payment_method: paymentMethodFilter || undefined,
  };

  const { data, isLoading, isError, error, isFetching, refetch } = useExpenseList({
    ...filterParams,
    page,
  });

  const summaryQuery = useExpenseSummary(filterParams);

  const createMutation = useCreateExpense();

  const handleCreate = (payload: ExpensePayload) => createMutation.mutateAsync(payload);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Expenses"
        subtitle="Record and track shop expenses."
        icon={<ReceiptLongIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Expenses' }]}
        actions={
          isStaff && (
            <Button
              variant="contained"
              startIcon={<AddCardIcon />}
              onClick={() => setDialogOpen(true)}
            >
              Add Expense
            </Button>
          )
        }
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
        }}
      >
        <StatCard
          label="Total Expenses"
          value={formatCurrency(summaryQuery.data?.total_expenses ?? 0)}
          sublabel="Sum of expenses in the selected range"
          icon={<ReceiptLongIcon />}
          tone="error"
        />
        <StatCard
          label="Expense Count"
          value={String(summaryQuery.data?.expense_count ?? 0)}
          sublabel="Records in the selected range"
          tone="gold"
        />
        <StatCard
          label="Largest Category"
          value={
            summaryQuery.data?.by_category[0]
              ? `${summaryQuery.data.by_category[0].category_display}: ${formatCurrency(
                  summaryQuery.data.by_category[0].total
                )}`
              : '-'
          }
          sublabel="Top expense category in the selected range"
          tone="info"
        />
      </Box>

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
          <TextField
            label="From"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              label="Category"
              onChange={(event) => setCategoryFilter(event.target.value as ExpenseCategory | '')}
            >
              <MenuItem value="">All categories</MenuItem>
              {EXPENSE_CATEGORIES.map((category) => (
                <MenuItem key={category} value={category}>
                  {EXPENSE_CATEGORY_LABELS[category]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Payment Method</InputLabel>
            <Select
              value={paymentMethodFilter}
              label="Payment Method"
              onChange={(event) => setPaymentMethodFilter(event.target.value as PaymentMethod | '')}
            >
              <MenuItem value="">All methods</MenuItem>
              {PAYMENT_METHODS.map((method) => (
                <MenuItem key={method} value={method}>
                  {PAYMENT_METHOD_LABELS[method]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(expense) => expense.id}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No expense records found"
        columns={[
          {
            label: 'Date',
            render: (expense) => (
              <Typography variant="body2">{formatDate(expense.expense_date)}</Typography>
            ),
          },
          {
            label: 'Category',
            render: (expense) => <StatusBadge label={expense.category_display} tone="neutral" />,
          },
          {
            label: 'Amount',
            primary: true,
            render: (expense) => (
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {formatCurrency(expense.amount)}
              </Typography>
            ),
          },
          {
            label: 'Payment Method',
            render: (expense) => (
              <Typography variant="body2">{expense.payment_method_display}</Typography>
            ),
          },
          {
            label: 'Reference',
            render: (expense) => (
              <Typography variant="body2">{expense.reference || '-'}</Typography>
            ),
          },
          {
            label: 'Description',
            render: (expense) => (
              <Typography variant="body2">{expense.description || '-'}</Typography>
            ),
          },
          {
            label: 'Recorded By',
            render: (expense) => (
              <Typography variant="body2">{expense.recorded_by_name || '-'}</Typography>
            ),
          },
        ]}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <ExpenseFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleCreate}
      />
    </Box>
  );
};

export default Expenses;
