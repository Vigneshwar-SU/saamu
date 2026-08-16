import React, { useEffect, useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useIncomeList, useIncomeSummary } from '../hooks/useFinance';
import {
  PAYMENT_METHODS,
  PAYMENT_METHOD_LABELS,
  PAYMENT_TYPES,
  PAYMENT_TYPE_LABELS,
} from '../types/finance';
import type { PaymentMethod, PaymentType } from '../types/finance';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { TableStateRow } from '../components/ui/TableStateRow';
import { StatCard } from '../components/ui/StatCard';
import { SectionCard } from '../components/ui/SectionCard';
import { StatusBadge } from '../components/ui/StatusBadge';

const PAGE_SIZE = 6;

export const Income: React.FC = () => {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [paymentMethodFilter, setPaymentMethodFilter] = useState<PaymentMethod | ''>('');
  const [paymentTypeFilter, setPaymentTypeFilter] = useState<PaymentType | ''>('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [dateFrom, dateTo, paymentMethodFilter, paymentTypeFilter]);

  const filterParams = {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    payment_method: paymentMethodFilter || undefined,
    payment_type: paymentTypeFilter || undefined,
  };

  const { data, isLoading, isError, error, isFetching, refetch } = useIncomeList({
    ...filterParams,
    page,
  });

  const summaryQuery = useIncomeSummary(filterParams);
  const summary = summaryQuery.data;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Income"
        subtitle="Track income from customer payments. Refunds reduce net income."
        icon={<AccountBalanceWalletIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Income' }]}
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
        }}
      >
        <StatCard
          label="Total Income"
          value={formatCurrency(summary?.total_income ?? 0)}
          sublabel="Net customer receipts in the selected range"
          icon={<AccountBalanceWalletIcon />}
          tone="success"
        />
        <StatCard
          label="Payments"
          value={String(summary?.payment_count ?? 0)}
          sublabel="Customer payments in the selected range"
          tone="gold"
        />
        <StatCard
          label="Refunds"
          value={formatCurrency(summary?.total_refunds ?? 0)}
          sublabel={`${summary?.refund_count ?? 0} refund(s) in the selected range`}
          tone="error"
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
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={paymentTypeFilter}
              label="Payment Type"
              onChange={(event) => setPaymentTypeFilter(event.target.value as PaymentType | '')}
            >
              <MenuItem value="">All types</MenuItem>
              {PAYMENT_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {PAYMENT_TYPE_LABELS[type]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(income) => income.id}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No customer payments found"
        columns={[
          {
            label: 'Date',
            render: (income) => (
              <Typography variant="body2">{formatDate(income.payment_date)}</Typography>
            ),
          },
          {
            label: 'Type',
            render: (income) => (
              <StatusBadge
                label={income.payment_type_display}
                tone={income.payment_type === 'REFUND' ? 'error' : 'success'}
              />
            ),
          },
          {
            label: 'Method',
            render: (income) => (
              <Typography variant="body2">{income.payment_method_display}</Typography>
            ),
          },
          {
            label: 'Amount',
            primary: true,
            render: (income) => (
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: income.payment_type === 'REFUND' ? '#8F2F22' : '#1F5C3C',
                }}
              >
                {formatCurrency(income.net_amount)}
              </Typography>
            ),
          },
          {
            label: 'Customer',
            render: (income) => <Typography variant="body2">{income.customer_name}</Typography>,
          },
          {
            label: 'Invoice',
            render: (income) => <Typography variant="body2">{income.invoice_number}</Typography>,
          },
          {
            label: 'Recorded By',
            render: (income) => (
              <Typography variant="body2">{income.recorded_by_name || '-'}</Typography>
            ),
          },
        ]}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
        }}
      >
        <SectionCard title="Income by Payment Method" noPadding>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Method</TableCell>
                <TableCell>Net Income</TableCell>
                <TableCell>Payments</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summary && summary.by_payment_method.length === 0 ? (
                <TableStateRow
                  colSpan={3}
                  state="empty"
                  emptyTitle="No payments in the selected range"
                />
              ) : (
                summary?.by_payment_method.map((row) => (
                  <TableRow key={row.payment_method}>
                    <TableCell>{row.payment_method_display}</TableCell>
                    <TableCell
                      sx={{ fontWeight: 600, color: row.total < 0 ? '#8F2F22' : '#1F5C3C' }}
                    >
                      {formatCurrency(row.total)}
                    </TableCell>
                    <TableCell>{row.count}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </SectionCard>

        <SectionCard title="Income by Payment Type" noPadding>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Net Income</TableCell>
                <TableCell>Count</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summary && summary.by_payment_type.length === 0 ? (
                <TableStateRow
                  colSpan={3}
                  state="empty"
                  emptyTitle="No payments in the selected range"
                />
              ) : (
                summary?.by_payment_type.map((row) => {
                  const isRefund = row.payment_type === 'REFUND';
                  return (
                    <TableRow key={row.payment_type}>
                      <TableCell>{row.payment_type_display}</TableCell>
                      <TableCell sx={{ fontWeight: 600, color: isRefund ? '#8F2F22' : '#1F5C3C' }}>
                        {formatCurrency(row.total)}
                      </TableCell>
                      <TableCell>{row.count}</TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </SectionCard>
      </Box>
    </Box>
  );
};

export default Income;
