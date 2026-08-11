import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import GroupsIcon from '@mui/icons-material/Groups';
import HandymanIcon from '@mui/icons-material/Handyman';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { formatCurrency } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { downloadBlob } from '../utils/download';
import { useReportsSummary, useReportExport } from '../hooks/useReports';
import type { ReportExportFormat } from '../hooks/useReports';
import { ORDER_STATUSES, ORDER_STATUS_LABELS, ORDER_STATUS_COLORS } from '../types/orders';
import { EXPENSE_CATEGORY_LABELS, PAYMENT_TYPE_LABELS } from '../types/finance';
import type { ReportsSummary } from '../types/reports';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { StatCard } from '../components/ui/StatCard';
import { SectionCard } from '../components/ui/SectionCard';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { ErrorState } from '../components/ui/ErrorState';

const emptySummary: ReportsSummary = {
  success: true,
  range: { date_from: null, date_to: null },
  orders: {
    total: 0,
    status_distribution: {
      total: 0,
      NEW: 0,
      CUTTING: 0,
      STITCHING: 0,
      READY: 0,
      COLLECTED: 0,
      CANCELLED: 0,
    },
    revenue: 0,
    garment_quantities: {},
  },
  customers: { active_customers: 0, new_customers: 0, customers_with_orders: 0 },
  tailors: {
    active_tailors: 0,
    workload: {
      assigned_quantity: 0,
      completed_quantity: 0,
      outstanding_quantity: 0,
      earned_amount: 0,
    },
  },
  financial: {
    income: {
      total_income: 0,
      payment_count: 0,
      refund_count: 0,
      total_refunds: 0,
      by_payment_method: [],
      by_payment_type: [],
    },
    expenses: {
      total_expenses: 0,
      expense_count: 0,
      by_category: [],
      by_payment_method: [],
    },
    net_position: 0,
    payroll_paid: 0,
    salary_advances: 0,
    order_revenue: 0,
  },
};

export const Reports: React.FC = () => {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [appliedFrom, setAppliedFrom] = useState('');
  const [appliedTo, setAppliedTo] = useState('');

  const filterParams = {
    date_from: appliedFrom || undefined,
    date_to: appliedTo || undefined,
  };

  const { data, isLoading, isError, error, isFetching, refetch } = useReportsSummary(filterParams);

  const summary = data ?? emptySummary;

  const exportMutation = useReportExport();
  const [exportError, setExportError] = useState<string | null>(null);

  const applyFilters = () => {
    setAppliedFrom(dateFrom);
    setAppliedTo(dateTo);
  };

  const resetFilters = () => {
    setDateFrom('');
    setDateTo('');
    setAppliedFrom('');
    setAppliedTo('');
  };

  const handleExport = (format: ReportExportFormat) => {
    if (exportMutation.isPending) return;
    setExportError(null);
    exportMutation.mutate(
      { format, params: filterParams },
      {
        onSuccess: ({ blob, filename }) => {
          downloadBlob(blob, filename);
        },
        onError: (exportFailure) => {
          setExportError(getApiErrorMessage(exportFailure));
        },
      }
    );
  };

  const netPosition = summary.financial.net_position;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Reports"
        subtitle="Business insights across orders, customers, tailor workload, and finances."
        icon={<BarChartIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Reports' }]}
      />

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" flexWrap="wrap">
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
          <Button variant="contained" onClick={applyFilters} disabled={isFetching}>
            Apply
          </Button>
          <Button variant="outlined" onClick={resetFilters} disabled={isFetching || (!appliedFrom && !appliedTo)}>
            Reset
          </Button>
          <Box sx={{ flexGrow: 1 }} />
          <Button
            variant="outlined"
            startIcon={<FileDownloadIcon />}
            onClick={() => handleExport('csv')}
            disabled={exportMutation.isPending}
          >
            {exportMutation.isPending ? 'Exporting…' : 'Export CSV'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<PictureAsPdfIcon />}
            onClick={() => handleExport('pdf')}
            disabled={exportMutation.isPending}
          >
            {exportMutation.isPending ? 'Exporting…' : 'Export PDF'}
          </Button>
          {summary.range.date_from || summary.range.date_to ? (
            <Chip
              size="small"
              label={`${summary.range.date_from ?? 'Start'} to ${summary.range.date_to ?? 'Today'}`}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          ) : (
            <Chip size="small" label="All time" variant="outlined" sx={{ fontWeight: 600 }} />
          )}
        </Stack>
        {exportError && (
          <Alert severity="error" onClose={() => setExportError(null)} sx={{ mt: 2 }}>
            Export failed: {exportError}
          </Alert>
        )}
      </FilterBar>

      {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}

      {isLoading ? (
        <FilterBar sx={{ py: 8, textAlign: 'center' }}>
          <Typography color="text.secondary">Loading reports…</Typography>
        </FilterBar>
      ) : isError ? (
        <FilterBar>
          <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        </FilterBar>
      ) : (
        <>
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
            }}
          >
            <StatCard
              label="Net Position"
              value={formatCurrency(netPosition)}
              sublabel="Income minus expenses in the selected range"
              tone={netPosition < 0 ? 'error' : 'success'}
            />
            <StatCard
              label="Income"
              value={formatCurrency(summary.financial.income.total_income)}
              sublabel={`${summary.financial.income.payment_count} payment(s), ${summary.financial.income.refund_count} refund(s)`}
              tone="gold"
            />
            <StatCard
              label="Expenses"
              value={formatCurrency(summary.financial.expenses.total_expenses)}
              sublabel={`${summary.financial.expenses.expense_count} expense(s)`}
              tone="error"
            />
            <StatCard
              label="Order Revenue"
              value={formatCurrency(summary.financial.order_revenue)}
              sublabel="Billed value of orders placed"
              tone="info"
            />
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <SectionCard title="Orders" icon={<ShoppingBagIcon />}>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Total orders
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.orders.total}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                    Status distribution
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {ORDER_STATUSES.map((status) => {
                      const count = summary.orders.status_distribution[status];
                      if (count === 0) return null;
                      const color = ORDER_STATUS_COLORS[status];
                      return (
                        <Chip
                          key={status}
                          label={`${ORDER_STATUS_LABELS[status]}: ${count}`}
                          size="small"
                          sx={{ fontWeight: 600, backgroundColor: color.bg, color: color.text }}
                        />
                      );
                    })}
                    {summary.orders.total === 0 && (
                      <Typography variant="body2" sx={{ color: 'text.disabled' }}>
                        No orders in the selected range.
                      </Typography>
                    )}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                    Garment quantities
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {Object.entries(summary.orders.garment_quantities).map(([type, quantity]) => (
                      <Chip
                        key={type}
                        label={`${type}: ${quantity}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                    ))}
                  </Stack>
                </Box>
              </Stack>
            </SectionCard>

            <SectionCard title="Customers" icon={<GroupsIcon />}>
              <Stack spacing={1.25}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Active customers
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.customers.active_customers}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    New customers in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.customers.new_customers}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Customers with orders in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.customers.customers_with_orders}</Typography>
                </Box>
              </Stack>
            </SectionCard>

            <SectionCard title="Tailor Workload" icon={<HandymanIcon />}>
              <Stack spacing={1.25}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Active tailors
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.tailors.active_tailors}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Assigned pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.tailors.workload.assigned_quantity}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Completed pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700, color: '#1F5C3C' }}>
                    {summary.tailors.workload.completed_quantity}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Outstanding pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700, color: '#8F4A00' }}>
                    {summary.tailors.workload.outstanding_quantity}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Earnings earned
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.tailors.workload.earned_amount)}
                  </Typography>
                </Box>
              </Stack>
            </SectionCard>

            <SectionCard title="Payroll & Settlements" icon={<AccountBalanceWalletIcon />}>
              <Stack spacing={1.25}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Payroll paid in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.financial.payroll_paid)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Salary advances in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.financial.salary_advances)}
                  </Typography>
                </Box>
              </Stack>
            </SectionCard>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <SectionCard title="Income by Payment Type" icon={<TrendingUpIcon />} noPadding>
              <TableCard sx={{ border: 'none', borderRadius: 0 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Type</TableCell>
                      <TableCell>Net Income</TableCell>
                      <TableCell>Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.financial.income.by_payment_type.length === 0 ? (
                      <TableStateRow colSpan={3} state="empty" emptyTitle="No payments in the selected range" />
                    ) : (
                      summary.financial.income.by_payment_type.map((row) => {
                        const isRefund = row.payment_type === 'REFUND';
                        return (
                          <TableRow key={row.payment_type}>
                            <TableCell>{PAYMENT_TYPE_LABELS[row.payment_type]}</TableCell>
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
              </TableCard>
            </SectionCard>

            <SectionCard title="Expenses by Category" icon={<AccountBalanceWalletIcon />} noPadding>
              <TableCard sx={{ border: 'none', borderRadius: 0 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Category</TableCell>
                      <TableCell>Total</TableCell>
                      <TableCell>Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.financial.expenses.by_category.length === 0 ? (
                      <TableStateRow colSpan={3} state="empty" emptyTitle="No expenses in the selected range" />
                    ) : (
                      summary.financial.expenses.by_category.map((row) => (
                        <TableRow key={row.category}>
                          <TableCell>{EXPENSE_CATEGORY_LABELS[row.category]}</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: '#8F2F22' }}>
                            {formatCurrency(row.total)}
                          </TableCell>
                          <TableCell>{row.count}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableCard>
            </SectionCard>
          </Box>
        </>
      )}
    </Box>
  );
};

export default Reports;
