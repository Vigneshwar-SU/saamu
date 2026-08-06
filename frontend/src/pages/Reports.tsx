import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  LinearProgress,
  Link,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import BarChartIcon from '@mui/icons-material/BarChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import GroupsIcon from '@mui/icons-material/Groups';
import HandymanIcon from '@mui/icons-material/Handyman';
import { formatCurrency } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useReportsSummary } from '../hooks/useReports';
import {
  ORDER_STATUSES,
  ORDER_STATUS_LABELS,
  ORDER_STATUS_COLORS,
} from '../types/orders';
import {
  EXPENSE_CATEGORY_LABELS,
  PAYMENT_TYPE_LABELS,
} from '../types/finance';
import type { ReportsSummary } from '../types/reports';

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
  accent: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, sublabel, accent }) => {
  return (
    <Card sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 500 }}>
          {label}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 700, color: accent }}>
          {value}
        </Typography>
        {sublabel && (
          <Typography variant="caption" sx={{ color: '#94A3B8' }}>
            {sublabel}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

interface SectionCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const SectionCard: React.FC<SectionCardProps> = ({ title, icon, children }) => {
  return (
    <Paper
      sx={{
        borderRadius: '12px',
        border: '1px solid #E2E8F0',
        overflow: 'hidden',
        backgroundColor: '#FFFFFF',
      }}
    >
      <Box
        sx={{
          px: 2,
          py: 1.5,
          backgroundColor: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Box sx={{ color: '#1E3A8A', display: 'flex' }}>{icon}</Box>
        <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
      </Box>
      {children}
    </Paper>
  );
};

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
  tailors: { active_tailors: 0, workload: { assigned_quantity: 0, completed_quantity: 0, outstanding_quantity: 0, earned_amount: 0 } },
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

  const {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    refetch,
  } = useReportsSummary(filterParams);

  const summary = data ?? emptySummary;

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

  const netPosition = summary.financial.net_position;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Reports
        </Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              backgroundColor: '#EFF6FF',
              color: '#1E3A8A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <BarChartIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Reports
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Business insights across orders, customers, tailor workload, and finances.
            </Typography>
          </Box>
        </Box>
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center">
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
          <Button
            variant="contained"
            color="primary"
            onClick={applyFilters}
            disabled={isFetching}
          >
            Apply
          </Button>
          <Button
            variant="outlined"
            onClick={resetFilters}
            disabled={isFetching || (!appliedFrom && !appliedTo)}
          >
            Reset
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
      </Paper>

      {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={32} />
        </Box>
      ) : isError ? (
        <Paper sx={{ p: 4, textAlign: 'center', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <Alert severity="error" sx={{ display: 'inline-flex' }}>
            {getApiErrorMessage(error)}
          </Alert>
          <Box sx={{ mt: 2 }}>
            <Button size="small" variant="outlined" onClick={() => refetch()}>
              Retry
            </Button>
          </Box>
        </Paper>
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
              accent={netPosition < 0 ? '#B91C1C' : '#15803D'}
            />
            <StatCard
              label="Income"
              value={formatCurrency(summary.financial.income.total_income)}
              sublabel={`${summary.financial.income.payment_count} payment(s), ${summary.financial.income.refund_count} refund(s)`}
              accent="#1E3A8A"
            />
            <StatCard
              label="Expenses"
              value={formatCurrency(summary.financial.expenses.total_expenses)}
              sublabel={`${summary.financial.expenses.expense_count} expense(s)`}
              accent="#B91C1C"
            />
            <StatCard
              label="Order Revenue"
              value={formatCurrency(summary.financial.order_revenue)}
              sublabel="Billed value of orders placed"
              accent="#7C3AED"
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
              <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Total orders
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.orders.total}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ color: '#64748B', mb: 1 }}>
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
                          sx={{
                            fontWeight: 600,
                            backgroundColor: color.bg,
                            color: color.text,
                          }}
                        />
                      );
                    })}
                    {summary.orders.total === 0 && (
                      <Typography variant="body2" sx={{ color: '#94A3B8' }}>
                        No orders in the selected range.
                      </Typography>
                    )}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ color: '#64748B', mb: 1 }}>
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
              </CardContent>
            </SectionCard>

            <SectionCard title="Customers" icon={<GroupsIcon />}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Active customers
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {summary.customers.active_customers}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    New customers in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.customers.new_customers}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Customers with orders in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {summary.customers.customers_with_orders}
                  </Typography>
                </Box>
              </CardContent>
            </SectionCard>

            <SectionCard title="Tailor Workload" icon={<HandymanIcon />}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Active tailors
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{summary.tailors.active_tailors}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Assigned pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {summary.tailors.workload.assigned_quantity}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Completed pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700, color: '#15803D' }}>
                    {summary.tailors.workload.completed_quantity}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Outstanding pieces
                  </Typography>
                  <Typography sx={{ fontWeight: 700, color: '#B45309' }}>
                    {summary.tailors.workload.outstanding_quantity}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Earnings earned
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.tailors.workload.earned_amount)}
                  </Typography>
                </Box>
              </CardContent>
            </SectionCard>

            <SectionCard title="Payroll & Settlements" icon={<AccountBalanceWalletIcon />}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Payroll paid in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.financial.payroll_paid)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Salary advances in range
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {formatCurrency(summary.financial.salary_advances)}
                  </Typography>
                </Box>
              </CardContent>
            </SectionCard>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <SectionCard title="Income by Payment Type" icon={<TrendingUpIcon />}>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Net Income</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.financial.income.by_payment_type.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                          <Typography variant="body2" sx={{ color: '#64748B' }}>
                            No payments in the selected range.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      summary.financial.income.by_payment_type.map((row) => {
                        const isRefund = row.payment_type === 'REFUND';
                        return (
                          <TableRow key={row.payment_type}>
                            <TableCell>{PAYMENT_TYPE_LABELS[row.payment_type]}</TableCell>
                            <TableCell
                              sx={{ fontWeight: 600, color: isRefund ? '#B91C1C' : '#15803D' }}
                            >
                              {formatCurrency(row.total)}
                            </TableCell>
                            <TableCell>{row.count}</TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </SectionCard>

            <SectionCard title="Expenses by Category" icon={<AccountBalanceWalletIcon />}>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Total</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summary.financial.expenses.by_category.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                          <Typography variant="body2" sx={{ color: '#64748B' }}>
                            No expenses in the selected range.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      summary.financial.expenses.by_category.map((row) => (
                        <TableRow key={row.category}>
                          <TableCell>{EXPENSE_CATEGORY_LABELS[row.category]}</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: '#B91C1C' }}>
                            {formatCurrency(row.total)}
                          </TableCell>
                          <TableCell>{row.count}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </SectionCard>
          </Box>
        </>
      )}
    </Box>
  );
};
