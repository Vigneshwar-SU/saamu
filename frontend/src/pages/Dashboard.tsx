import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Divider,
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
import DashboardIcon from '@mui/icons-material/Dashboard';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PaymentsIcon from '@mui/icons-material/Payments';
import SavingsIcon from '@mui/icons-material/Savings';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import { useDashboardSummary } from '../hooks/useFinance';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { EXPENSE_CATEGORY_LABELS } from '../types/finance';
import type { DashboardOrderCounts } from '../types/finance';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { SectionCard } from '../components/ui/SectionCard';
import { TableCard } from '../components/ui/TableCard';
import { FilterBar } from '../components/ui/FilterBar';
import { TableStateRow } from '../components/ui/TableStateRow';
import { ErrorState } from '../components/ui/ErrorState';

type OrderCountKey = Exclude<keyof DashboardOrderCounts, 'total'>;

const ORDER_STATUS_LABELS: Record<OrderCountKey, string> = {
  NEW: 'New',
  CUTTING: 'Cutting',
  STITCHING: 'Stitching',
  READY: 'Ready',
  COLLECTED: 'Collected',
  CANCELLED: 'Cancelled',
};

function expenseCategoryLabel(category: string): string {
  return EXPENSE_CATEGORY_LABELS[category as keyof typeof EXPENSE_CATEGORY_LABELS] ?? category;
}

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
      <PageHeader
        title="Dashboard"
        subtitle="Financial and operational overview of the shop."
        icon={<DashboardIcon />}
        crumbs={[{ label: 'Dashboard' }]}
      />

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }}>
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
          <Button variant="contained" onClick={handleApply}>
            Apply
          </Button>
          <Button variant="outlined" onClick={handleReset}>
            Reset
          </Button>
        </Stack>
      </FilterBar>

      {isLoading ? (
        <FilterBar sx={{ py: 8, textAlign: 'center' }}>
          <Typography color="text.secondary">Loading dashboard…</Typography>
        </FilterBar>
      ) : isError ? (
        <FilterBar>
          <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        </FilterBar>
      ) : (
        <>
          {isFetching && <LinearProgress sx={{ height: 3 }} />}

          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
            }}
          >
            <StatCard
              label="Recorded Income"
              value={formatCurrency(financial?.recorded_income ?? 0)}
              sublabel="Net customer receipts for the selected range"
              icon={<AccountBalanceWalletIcon />}
              tone="success"
            />
            <StatCard
              label="Recorded Expenses"
              value={formatCurrency(financial?.recorded_expenses ?? 0)}
              sublabel="Expense ledger for the selected range"
              icon={<ReceiptLongIcon />}
              tone="error"
            />
            <StatCard
              label="Net Recorded Balance"
              value={formatCurrency(financial?.net_recorded_balance ?? 0)}
              sublabel="Income minus expenses"
              icon={<PaymentsIcon />}
              tone="gold"
            />
            <StatCard
              label="Payroll Paid"
              value={formatCurrency(financial?.payroll_paid ?? 0)}
              sublabel="Settled payroll payments"
              icon={<FactCheckIcon />}
              tone="default"
            />
            <StatCard
              label="Salary Advances"
              value={formatCurrency(financial?.salary_advances ?? 0)}
              sublabel="Advances issued (kept separate)"
              icon={<SavingsIcon />}
              tone="warning"
            />
            <StatCard
              label="Order Revenue"
              value={formatCurrency(financial?.order_revenue ?? 0)}
              sublabel="Order value (not recorded cash)"
              icon={<ShoppingBagIcon />}
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
            <SectionCard title="Order Status" subtitle="Live counts by stage">
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {(Object.keys(ORDER_STATUS_LABELS) as OrderCountKey[]).map((status) => (
                  <Chip
                    key={status}
                    label={`${ORDER_STATUS_LABELS[status]}: ${operational?.order_counts[status] ?? 0}`}
                    size="small"
                    sx={{ fontWeight: 600, backgroundColor: '#F1EDE2', color: '#242424' }}
                  />
                ))}
                <Chip
                  label={`Total: ${operational?.order_counts.total ?? 0}`}
                  size="small"
                  sx={{ fontWeight: 700, backgroundColor: '#A98216', color: '#FFFFFF' }}
                />
              </Stack>
            </SectionCard>

            <SectionCard title="Shop Overview" subtitle="Key operational numbers">
              <Stack spacing={1.25}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Active customers
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {operational?.active_customers ?? 0}
                  </Typography>
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Active tailors
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {operational?.active_tailors ?? 0}
                  </Typography>
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Shirts ordered
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatPieces(operational?.garment_quantities.SHIRT ?? 0)}
                  </Typography>
                </Box>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Pants ordered
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatPieces(operational?.garment_quantities.PANT ?? 0)}
                  </Typography>
                </Box>
              </Stack>
            </SectionCard>
          </Box>

          <SectionCard title="Tailor Workload" subtitle="Stitching performance across the team">
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
              }}
            >
              <StatCard
                label="Assigned Pieces"
                value={formatPieces(operational?.workload.assigned_quantity ?? 0)}
                tone="gold"
              />
              <StatCard
                label="Completed Pieces"
                value={formatPieces(operational?.workload.completed_quantity ?? 0)}
                tone="success"
              />
              <StatCard
                label="Outstanding Pieces"
                value={formatPieces(operational?.workload.outstanding_quantity ?? 0)}
                tone="warning"
              />
              <StatCard
                label="Earned Amount"
                value={formatCurrency(operational?.workload.earned_amount ?? 0)}
                tone="info"
              />
            </Box>
          </SectionCard>

          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            }}
          >
            <SectionCard title="Recent Income" noPadding>
              <TableCard sx={{ border: 'none', borderRadius: 0 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Amount</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data?.recent_payments.length === 0 ? (
                      <TableStateRow
                        colSpan={3}
                        state="empty"
                        emptyTitle="No customer payments yet"
                      />
                    ) : (
                      data?.recent_payments.map((payment) => {
                        const isRefund = payment.payment_type === 'REFUND';
                        return (
                          <TableRow key={payment.id}>
                            <TableCell>{formatDate(payment.payment_date)}</TableCell>
                            <TableCell>
                              <Typography
                                sx={{
                                  fontSize: '0.8125rem',
                                  fontWeight: 600,
                                  color: isRefund ? '#8F2F22' : '#1F5C3C',
                                }}
                              >
                                {payment.payment_type_display}
                              </Typography>
                            </TableCell>
                            <TableCell
                              sx={{ fontWeight: 600, color: isRefund ? '#8F2F22' : '#1F5C3C' }}
                            >
                              {formatCurrency(payment.net_amount)}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </TableCard>
            </SectionCard>

            <SectionCard title="Recent Expenses" noPadding>
              <TableCard sx={{ border: 'none', borderRadius: 0 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Amount</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data?.recent_expenses.length === 0 ? (
                      <TableStateRow
                        colSpan={3}
                        state="empty"
                        emptyTitle="No expenses recorded yet"
                      />
                    ) : (
                      data?.recent_expenses.map((expense) => (
                        <TableRow key={expense.id}>
                          <TableCell>{formatDate(expense.expense_date)}</TableCell>
                          <TableCell>{expenseCategoryLabel(expense.category)}</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: '#8F2F22' }}>
                            {formatCurrency(expense.amount)}
                          </TableCell>
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

export default Dashboard;
