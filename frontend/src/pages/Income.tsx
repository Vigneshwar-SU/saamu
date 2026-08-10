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
  FormControl,
  InputLabel,
  LinearProgress,
  Link,
  MenuItem,
  Pagination,
  Paper,
  Select,
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

const PAGE_SIZE = 6;

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

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Income
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
            <AccountBalanceWalletIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Income
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Track income from customer payments. Refunds reduce net income.
            </Typography>
          </Box>
        </Box>
      </Box>

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
          accent="#15803D"
        />
        <StatCard
          label="Payments"
          value={String(summary?.payment_count ?? 0)}
          sublabel="Customer payments in the selected range"
          accent="#1E3A8A"
        />
        <StatCard
          label="Refunds"
          value={formatCurrency(summary?.total_refunds ?? 0)}
          sublabel={`${summary?.refund_count ?? 0} refund(s) in the selected range`}
          accent="#B91C1C"
        />
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
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
              onChange={(event) =>
                setPaymentMethodFilter(event.target.value as PaymentMethod | '')
              }
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
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Customer</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Invoice</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Alert severity="error" sx={{ display: 'inline-flex' }}>
                      {getApiErrorMessage(error)}
                    </Alert>
                    <Box sx={{ mt: 1.5 }}>
                      <Button size="small" variant="outlined" onClick={() => refetch()}>
                        Retry
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : data && data.results.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>
                      No customer payments found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((income) => {
                  const isRefund = income.payment_type === 'REFUND';
                  return (
                    <TableRow
                      key={income.id}
                      hover
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell>
                        <Typography variant="body2">{formatDate(income.payment_date)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={income.payment_type_display}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: isRefund ? '#FEE2E2' : '#DCFCE7',
                            color: isRefund ? '#B91C1C' : '#15803D',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{income.payment_method_display}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: 600, color: isRefund ? '#B91C1C' : '#15803D' }}
                        >
                          {formatCurrency(income.net_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{income.customer_name}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{income.invoice_number}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{income.recorded_by_name || '-'}</Typography>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {data && data.count > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Showing {data.results.length} of {data.count} records
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
        }}
      >
        <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          <Box
            sx={{ px: 2, py: 1.5, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}
          >
            <Typography sx={{ fontWeight: 700 }}>Income by Payment Method</Typography>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Net Income</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Payments</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {summary && summary.by_payment_method.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" sx={{ color: '#64748B' }}>
                        No payments in the selected range.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  summary?.by_payment_method.map((row) => (
                    <TableRow key={row.payment_method}>
                      <TableCell>{row.payment_method_display}</TableCell>
                      <TableCell
                        sx={{ fontWeight: 600, color: row.total < 0 ? '#B91C1C' : '#15803D' }}
                      >
                        {formatCurrency(row.total)}
                      </TableCell>
                      <TableCell>{row.count}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          <Box
            sx={{ px: 2, py: 1.5, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}
          >
            <Typography sx={{ fontWeight: 700 }}>Income by Payment Type</Typography>
          </Box>
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
                {summary && summary.by_payment_type.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" sx={{ color: '#64748B' }}>
                        No payments in the selected range.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  summary?.by_payment_type.map((row) => {
                    const isRefund = row.payment_type === 'REFUND';
                    return (
                      <TableRow key={row.payment_type}>
                        <TableCell>{row.payment_type_display}</TableCell>
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
        </Paper>
      </Box>
    </Box>
  );
};
