import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
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
import DashboardIcon from '@mui/icons-material/Dashboard';
import { useDashboardSummary } from '../hooks/useFinance';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { EXPENSE_CATEGORY_LABELS } from '../types/finance';
import type { DashboardOrderCounts } from '../types/finance';

type OrderCountKey = Exclude<keyof DashboardOrderCounts, 'total'>;

const ORDER_STATUS_LABELS: Record<OrderCountKey, string> = {
  NEW: 'New',
  CUTTING: 'Cutting',
  STITCHING: 'Stitching',
  READY: 'Ready',
  COLLECTED: 'Collected',
  CANCELLED: 'Cancelled',
};

const ORDER_STATUS_COLORS: Record<OrderCountKey, { bg: string; text: string }> = {
  NEW: { bg: '#EFF6FF', text: '#1E3A8A' },
  CUTTING: { bg: '#FEF3C7', text: '#B45309' },
  STITCHING: { bg: '#FCE7F3', text: '#9D174D' },
  READY: { bg: '#DCFCE7', text: '#15803D' },
  COLLECTED: { bg: '#E2E8F0', text: '#475569' },
  CANCELLED: { bg: '#FEE2E2', text: '#B91C1C' },
};

function expenseCategoryLabel(category: string): string {
  return EXPENSE_CATEGORY_LABELS[category as keyof typeof EXPENSE_CATEGORY_LABELS] ?? category;
}

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

export const Dashboard: React.FC = () => {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [appliedFrom, setAppliedFrom] = useState('');
  const [appliedTo, setAppliedTo] = useState('');

  const { data, isLoading, isError, error, isFetching, refetch } = useDashboardSummary({
    date_from: appliedFrom || undefined,
    date_to: appliedTo || undefined,
  });

  useEffect(() => {
    if (dateFrom === '' && dateTo === '') {
      setAppliedFrom('');
      setAppliedTo('');
    }
  }, [dateFrom, dateTo]);

  const handleApply = () => {
    setAppliedFrom(dateFrom);
    setAppliedTo(dateTo);
  };

  const handleReset = () => {
    setDateFrom('');
    setDateTo('');
    setAppliedFrom('');
    setAppliedTo('');
  };

  const financial = data?.financial;
  const operational = data?.operational;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Dashboard
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
            <DashboardIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Dashboard
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Financial and operational overview of the shop.
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
            onClick={handleApply}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            Apply
          </Button>
          <Button variant="outlined" onClick={handleReset} sx={{ color: '#64748B' }}>
            Reset
          </Button>
        </Stack>
      </Paper>

      {isLoading ? (
        <Paper sx={{ p: 8, textAlign: 'center', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <CircularProgress size={32} />
        </Paper>
      ) : isError ? (
        <Paper sx={{ p: 4, textAlign: 'center', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <Alert severity="error" sx={{ display: 'inline-flex' }}>
            {getApiErrorMessage(error)}
          </Alert>
          <Box sx={{ mt: 1.5 }}>
            <Button size="small" variant="outlined" onClick={() => refetch()}>
              Retry
            </Button>
          </Box>
        </Paper>
      ) : (
        <>
          {isFetching && <LinearProgress sx={{ height: 3 }} />}

          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
              Financial Summary
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(3, 1fr)',
                },
              }}
            >
              <StatCard
                label="Recorded Income"
                value={formatCurrency(financial?.recorded_income ?? 0)}
                sublabel="Net customer receipts for the selected range"
                accent="#15803D"
              />
              <StatCard
                label="Recorded Expenses"
                value={formatCurrency(financial?.recorded_expenses ?? 0)}
                sublabel="Expense ledger for the selected range"
                accent="#B91C1C"
              />
              <StatCard
                label="Net Recorded Balance"
                value={formatCurrency(financial?.net_recorded_balance ?? 0)}
                sublabel="Income minus expenses"
                accent="#1E3A8A"
              />
              <StatCard
                label="Payroll Paid"
                value={formatCurrency(financial?.payroll_paid ?? 0)}
                sublabel="Settled payroll payments"
                accent="#7C3AED"
              />
              <StatCard
                label="Salary Advances"
                value={formatCurrency(financial?.salary_advances ?? 0)}
                sublabel="Advances issued (kept separate)"
                accent="#B45309"
              />
              <StatCard
                label="Order Revenue"
                value={formatCurrency(financial?.order_revenue ?? 0)}
                sublabel="Order value (not recorded cash)"
                accent="#0F766E"
              />
            </Box>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <Card sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Order Status
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {(Object.keys(ORDER_STATUS_LABELS) as OrderCountKey[]).map((status) => {
                    const colors = ORDER_STATUS_COLORS[status] ?? { bg: '#F1F5F9', text: '#475569' };
                    return (
                      <Chip
                        key={status}
                        label={`${ORDER_STATUS_LABELS[status]}: ${operational?.order_counts[status] ?? 0}`}
                        size="small"
                        sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
                      />
                    );
                  })}
                  <Chip
                    label={`Total: ${operational?.order_counts.total ?? 0}`}
                    size="small"
                    sx={{ fontWeight: 700, backgroundColor: '#1E3A8A', color: '#FFFFFF' }}
                  />
                </Stack>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Shop Overview
                </Typography>
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      Active customers
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {operational?.active_customers ?? 0}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      Active tailors
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {operational?.active_tailors ?? 0}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      Shirts ordered
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {formatPieces(operational?.garment_quantities.SHIRT ?? 0)}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      Pants ordered
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {formatPieces(operational?.garment_quantities.PANT ?? 0)}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Box>

          <Card sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Tailor Workload
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gap: 2,
                  gridTemplateColumns: {
                    xs: 'repeat(2, 1fr)',
                    md: 'repeat(4, 1fr)',
                  },
                }}
              >
                <StatCard
                  label="Assigned Pieces"
                  value={formatPieces(operational?.workload.assigned_quantity ?? 0)}
                  accent="#1E3A8A"
                />
                <StatCard
                  label="Completed Pieces"
                  value={formatPieces(operational?.workload.completed_quantity ?? 0)}
                  accent="#15803D"
                />
                <StatCard
                  label="Outstanding Pieces"
                  value={formatPieces(operational?.workload.outstanding_quantity ?? 0)}
                  accent="#B45309"
                />
                <StatCard
                  label="Earned Amount"
                  value={formatCurrency(operational?.workload.earned_amount ?? 0)}
                  accent="#7C3AED"
                />
              </Box>
            </CardContent>
          </Card>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                <Typography sx={{ fontWeight: 700 }}>Recent Income</Typography>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data?.recent_payments.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                          <Typography variant="body2" sx={{ color: '#64748B' }}>
                            No customer payments yet.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      data?.recent_payments.map((payment) => {
                        const isRefund = payment.payment_type === 'REFUND';
                        return (
                          <TableRow key={payment.id}>
                            <TableCell>{formatDate(payment.payment_date)}</TableCell>
                            <TableCell>
                              <Chip
                                label={payment.payment_type_display}
                                size="small"
                                sx={{
                                  fontWeight: 600,
                                  backgroundColor: isRefund ? '#FEE2E2' : '#DCFCE7',
                                  color: isRefund ? '#B91C1C' : '#15803D',
                                }}
                              />
                            </TableCell>
                            <TableCell
                              sx={{ fontWeight: 600, color: isRefund ? '#B91C1C' : '#15803D' }}
                            >
                              {formatCurrency(payment.net_amount)}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>

            <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                <Typography sx={{ fontWeight: 700 }}>Recent Expenses</Typography>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data?.recent_expenses.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                          <Typography variant="body2" sx={{ color: '#64748B' }}>
                            No expenses recorded yet.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      data?.recent_expenses.map((expense) => (
                        <TableRow key={expense.id}>
                          <TableCell>{formatDate(expense.expense_date)}</TableCell>
                          <TableCell>{expenseCategoryLabel(expense.category)}</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: '#B91C1C' }}>
                            {formatCurrency(expense.amount)}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Box>
        </>
      )}
    </Box>
  );
};
