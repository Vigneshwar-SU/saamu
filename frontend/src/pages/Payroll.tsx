import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  LinearProgress,
  Link,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import AddCardIcon from '@mui/icons-material/AddCard';
import CalculateIcon from '@mui/icons-material/Calculate';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { PayrollPeriodDialog } from '../components/PayrollPeriodDialog';
import {
  useCalculatePayrollPeriod,
  useCreatePayrollPeriod,
  useFinalizePayrollPeriod,
  usePayrollPeriodList,
} from '../hooks/usePayroll';
import {
  PAYROLL_PERIOD_STATUS_COLORS,
  PAYROLL_PERIOD_STATUS_LABELS,
  SETTLEMENT_STATUS_COLORS,
  SETTLEMENT_STATUS_LABELS,
} from '../types/payroll';
import type { PayrollPeriod, PayrollPeriodPayload } from '../types/payroll';

const PAGE_SIZE = 7;

export const Payroll: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dialogOpen, setDialogOpen] = useState(false);
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, isFetching, refetch } = usePayrollPeriodList(page);

  const createMutation = useCreatePayrollPeriod();
  const calculateMutation = useCalculatePayrollPeriod();
  const finalizeMutation = useFinalizePayrollPeriod();

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  const handleCreate = async (payload: PayrollPeriodPayload) => {
    const created = await createMutation.mutateAsync(payload);
    setPage(1);
    return created;
  };

  const handleCalculate = async (period: PayrollPeriod) => {
    const confirmed = window.confirm(
      `Calculate payroll for ${formatDate(period.period_start)} to ${formatDate(period.period_end)}? Entries will be generated from completed assignments and attendance.`
    );
    if (!confirmed) return;
    try {
      await calculateMutation.mutateAsync(period.id);
    } catch (calculateError) {
      window.alert(getApiErrorMessage(calculateError));
    }
  };

  const handleFinalize = async (period: PayrollPeriod) => {
    const confirmed = window.confirm(
      `Finalize payroll for ${formatDate(period.period_start)} to ${formatDate(period.period_end)}? This locks the amounts and cannot be undone.`
    );
    if (!confirmed) return;
    try {
      await finalizeMutation.mutateAsync(period.id);
    } catch (finalizeError) {
      window.alert(getApiErrorMessage(finalizeError));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Payroll
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
            <PointOfSaleIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Payroll
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Create payroll periods and calculate piece-rate earnings.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Button
            variant="contained"
            startIcon={<AddCardIcon />}
            onClick={() => setDialogOpen(true)}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            New Period
          </Button>
        )}
      </Box>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Period</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Completed Pieces</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Piece Rate Earnings</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Attendance</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Total Payable</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Paid</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Outstanding</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Settlement</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Tailors</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={11} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={11} align="center" sx={{ py: 4 }}>
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
                  <TableCell colSpan={11} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>No payroll periods found.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((period) => {
                  const colors = PAYROLL_PERIOD_STATUS_COLORS[period.status];
                  const settlementColors =
                    SETTLEMENT_STATUS_COLORS[period.settlement.settlement_status];
                  return (
                    <TableRow
                      key={period.id}
                      hover
                      sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                      onClick={() => navigate(`/payroll/${period.id}`)}
                    >
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>
                          {formatDate(period.period_start)} – {formatDate(period.period_end)}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                          #{period.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={PAYROLL_PERIOD_STATUS_LABELS[period.status]}
                          size="small"
                          sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatPieces(period.total_completed_pieces)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(period.total_piece_rate_earnings)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(period.total_attendance_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#15803D' }}>
                          {formatCurrency(period.total_payable)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(period.settlement.payments_recorded)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: 600,
                            color:
                              period.settlement.outstanding_payable > 0 ? '#B45309' : '#15803D',
                          }}
                        >
                          {formatCurrency(period.settlement.outstanding_payable)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={SETTLEMENT_STATUS_LABELS[period.settlement.settlement_status]}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: settlementColors.bg,
                            color: settlementColors.text,
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{period.entry_count}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="View period">
                            <Button
                              size="small"
                              startIcon={<VisibilityIcon fontSize="small" />}
                              onClick={(event) => {
                                event.stopPropagation();
                                navigate(`/payroll/${period.id}`);
                              }}
                            >
                              View
                            </Button>
                          </Tooltip>
                          {isStaff && period.status === 'DRAFT' && (
                            <Tooltip title="Calculate payroll">
                              <Button
                                size="small"
                                startIcon={<CalculateIcon fontSize="small" />}
                                disabled={calculateMutation.isPending || finalizeMutation.isPending}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleCalculate(period);
                                }}
                              >
                                Calculate
                              </Button>
                            </Tooltip>
                          )}
                          {isStaff && period.status === 'CALCULATED' && (
                            <Tooltip title="Finalize payroll">
                              <Button
                                size="small"
                                startIcon={<CheckCircleOutlineIcon fontSize="small" />}
                                disabled={calculateMutation.isPending || finalizeMutation.isPending}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleFinalize(period);
                                }}
                              >
                                Finalize
                              </Button>
                            </Tooltip>
                          )}
                        </Stack>
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
            Showing {data.results.length} of {data.count} periods
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      <PayrollPeriodDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleCreate}
      />
    </Box>
  );
};
