import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Link,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import CalculateIcon from '@mui/icons-material/Calculate';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import PaymentsIcon from '@mui/icons-material/Payments';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { RecordPaymentDialog } from '../components/RecordPaymentDialog';
import { ApplyAdvanceDialog } from '../components/ApplyAdvanceDialog';
import {
  useApplyAdvanceToEntry,
  useCalculatePayrollPeriod,
  useFinalizePayrollPeriod,
  usePayrollEntries,
  usePayrollPaymentHistory,
  usePayrollPeriod,
  usePayrollTailorDetail,
  useRecordPayment,
  useSettleEntry,
} from '../hooks/usePayroll';
import {
  PAYROLL_PERIOD_STATUS_COLORS,
  PAYROLL_PERIOD_STATUS_LABELS,
  SALARY_MODEL_LABELS,
  SETTLEMENT_STATUS_COLORS,
  SETTLEMENT_STATUS_LABELS,
} from '../types/payroll';
import type {
  PayrollEntry,
  PaymentHistoryResponse,
  PaymentPayload,
  PayrollSettlement,
} from '../types/payroll';

const SummaryCard: React.FC<{ label: string; value: string; color?: string }> = ({
  label,
  value,
  color,
}) => (
  <Paper sx={{ flex: 1, minWidth: 180, p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
    <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
      {label}
    </Typography>
    <Typography variant="h5" sx={{ fontWeight: 700, mt: 0.5, color: color ?? '#0F172A' }}>
      {value}
    </Typography>
  </Paper>
);

export const PayrollDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const periodId = Number(id ?? 0);
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [selectedTailorId, setSelectedTailorId] = useState<number | null>(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [settleDialogOpen, setSettleDialogOpen] = useState(false);
  const [advanceDialogOpen, setAdvanceDialogOpen] = useState(false);

  const { data: period, isLoading, isError, error, refetch } = usePayrollPeriod(periodId);
  const { data: entriesData } = usePayrollEntries({ period: periodId });
  const { data: tailorDetail } = usePayrollTailorDetail(periodId, selectedTailorId ?? 0);

  const calculateMutation = useCalculatePayrollPeriod();
  const finalizeMutation = useFinalizePayrollPeriod();
  const recordMutation = useRecordPayment();
  const settleMutation = useSettleEntry();
  const applyMutation = useApplyAdvanceToEntry();

  const entries = entriesData?.results ?? [];
  const selectedEntry = entries.find((e) => e.tailor.id === selectedTailorId) ?? null;
  const selectedEntryId = selectedEntry?.id ?? 0;

  const { data: paymentHistory } = usePayrollPaymentHistory(selectedEntryId);

  const isFinalized = period?.status === 'FINALIZED';

  const handleCalculate = async () => {
    const confirmed = window.confirm(
      'Calculate payroll for this period? Existing entries will be replaced with fresh figures.'
    );
    if (!confirmed) return;
    try {
      await calculateMutation.mutateAsync(periodId);
    } catch (calculateError) {
      window.alert(getApiErrorMessage(calculateError));
    }
  };

  const handleFinalize = async () => {
    const confirmed = window.confirm(
      'Finalize this payroll period? The amounts will be locked and cannot be recalculated.'
    );
    if (!confirmed) return;
    try {
      await finalizeMutation.mutateAsync(periodId);
    } catch (finalizeError) {
      window.alert(getApiErrorMessage(finalizeError));
    }
  };

  const handleRecordPayment = async (payload: PaymentPayload) => {
    await recordMutation.mutateAsync({ entryId: selectedEntryId, payload });
  };

  const handleSettleInFull = async (payload: PaymentPayload) => {
    await settleMutation.mutateAsync({ entryId: selectedEntryId, payload });
  };

  const handleApplyAdvance = async (advanceId: number) => {
    await applyMutation.mutateAsync({ entryId: selectedEntryId, advanceId });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (isError || !period) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button size="small" variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
      </Box>
    );
  }

  const colors = PAYROLL_PERIOD_STATUS_COLORS[period.status];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
            Saamu Tailors ERP
          </Link>
          <Link underline="hover" color="inherit" href="/payroll" sx={{ fontSize: '0.85rem' }}>
            Payroll
          </Link>
          <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
            Period #{period.id}
          </Typography>
        </Breadcrumbs>
        <Button size="small" startIcon={<ArrowBackIcon />} onClick={() => navigate('/payroll')}>
          Back to Payroll
        </Button>
      </Box>

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
              {formatDate(period.period_start)} – {formatDate(period.period_end)}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
              <Chip
                label={PAYROLL_PERIOD_STATUS_LABELS[period.status]}
                size="small"
                sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
              />
              {period.created_by_name && (
                <Typography variant="body2" sx={{ color: '#64748B' }}>
                  Created by {period.created_by_name}
                </Typography>
              )}
            </Stack>
          </Box>
        </Box>
        <Stack direction="row" spacing={1.5}>
          {isStaff && period.status === 'DRAFT' && (
            <Button
              variant="contained"
              startIcon={<CalculateIcon />}
              disabled={calculateMutation.isPending || finalizeMutation.isPending}
              onClick={handleCalculate}
              sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
            >
              Calculate Payroll
            </Button>
          )}
          {isStaff && period.status === 'CALCULATED' && (
            <Button
              variant="contained"
              startIcon={<CheckCircleOutlineIcon />}
              disabled={calculateMutation.isPending || finalizeMutation.isPending}
              onClick={handleFinalize}
              sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
            >
              Finalize
            </Button>
          )}
        </Stack>
      </Box>

      {period.notes && (
        <Paper
          sx={{
            p: 2,
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            backgroundColor: '#F8FAFC',
          }}
        >
          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
            NOTES
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.5 }}>
            {period.notes}
          </Typography>
        </Paper>
      )}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
        <SummaryCard
          label="TOTAL COMPLETED PIECES"
          value={formatPieces(period.total_completed_pieces)}
        />
        <SummaryCard
          label="PIECE RATE EARNINGS"
          value={formatCurrency(period.total_piece_rate_earnings)}
          color="#1E3A8A"
        />
        <SummaryCard
          label="TOTAL FIXED SALARY"
          value={formatCurrency(period.total_fixed_salary)}
          color="#7C3AED"
        />
        <SummaryCard
          label="TOTAL GROSS SALARY"
          value={formatCurrency(period.total_gross_salary)}
          color="#0E7490"
        />
        <SummaryCard label="ATTENDANCE" value={formatCurrency(period.total_attendance_amount)} />
        <SummaryCard
          label="TOTAL PAYABLE"
          value={formatCurrency(period.total_payable)}
          color="#15803D"
        />
        <SummaryCard label="TAILORS IN PERIOD" value={String(period.entry_count)} />
      </Stack>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Tailor</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Present</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Half Day</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Absent</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Completed</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Salary Model</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Fixed Salary</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Piece Rate Earnings</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Attendance Amount</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Total Payable</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Advance</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Paid</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Outstanding</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Settlement</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={14} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>
                      {period.status === 'DRAFT'
                        ? 'No entries yet. Calculate payroll to generate tailor entries.'
                        : 'No tailor entries found for this period.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                entries.map((entry) => {
                  const settlementColors =
                    SETTLEMENT_STATUS_COLORS[entry.settlement.settlement_status];
                  return (
                    <TableRow
                      key={entry.id}
                      hover
                      sx={{
                        cursor: 'pointer',
                        '&:last-child td, &:last-child th': { border: 0 },
                        backgroundColor:
                          selectedTailorId === entry.tailor.id ? '#F8FAFC' : 'transparent',
                      }}
                      onClick={() =>
                        setSelectedTailorId((current) =>
                          current === entry.tailor.id ? null : entry.tailor.id
                        )
                      }
                    >
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>{entry.tailor.name}</Typography>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                          #{entry.tailor.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{entry.present_days}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{entry.half_days}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{entry.absent_days}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatPieces(entry.completed_pieces)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={SALARY_MODEL_LABELS[entry.salary_model]}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            fontSize: '0.7rem',
                            backgroundColor:
                              entry.salary_model === 'FIXED_SALARY'
                                ? '#EDE9FE'
                                : entry.salary_model === 'MIXED'
                                  ? '#E0F2FE'
                                  : '#F1F5F9',
                            color:
                              entry.salary_model === 'FIXED_SALARY'
                                ? '#6D28D9'
                                : entry.salary_model === 'MIXED'
                                  ? '#0369A1'
                                  : '#475569',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {entry.salary_model === 'PER_GARMENT'
                            ? '—'
                            : formatCurrency(entry.fixed_salary_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(entry.piece_rate_earnings)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(entry.attendance_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#15803D' }}>
                          {formatCurrency(entry.total_payable)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {entry.settlement.advance_deductions > 0
                            ? `-${formatCurrency(entry.settlement.advance_deductions)}`
                            : '0'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatCurrency(entry.settlement.payments_recorded)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: 600,
                            color:
                              entry.settlement.outstanding_payable === 0 ? '#15803D' : '#B45309',
                          }}
                        >
                          {formatCurrency(entry.settlement.outstanding_payable)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={SETTLEMENT_STATUS_LABELS[entry.settlement.settlement_status]}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: settlementColors.bg,
                            color: settlementColors.text,
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {selectedTailorId && (
        <>
          <TailorAssignmentBreakdown
            periodId={periodId}
            tailorId={selectedTailorId}
            entry={selectedEntry}
            data={tailorDetail}
          />
          {selectedEntry && (
            <SettlementPanel
              entry={selectedEntry}
              isStaff={isStaff}
              isFinalized={isFinalized}
              paymentHistory={paymentHistory}
              onRecordPayment={() => setPaymentDialogOpen(true)}
              onSettleInFull={() => setSettleDialogOpen(true)}
              onApplyAdvance={() => setAdvanceDialogOpen(true)}
            />
          )}
        </>
      )}

      {selectedEntry && (
        <>
          <RecordPaymentDialog
            open={paymentDialogOpen}
            onClose={() => setPaymentDialogOpen(false)}
            submit={handleRecordPayment}
            settlement={selectedEntry.settlement}
          />
          <RecordPaymentDialog
            open={settleDialogOpen}
            onClose={() => setSettleDialogOpen(false)}
            submit={handleSettleInFull}
            settlement={selectedEntry.settlement}
            settleInFull
          />
          <ApplyAdvanceDialog
            open={advanceDialogOpen}
            onClose={() => setAdvanceDialogOpen(false)}
            submit={handleApplyAdvance}
            tailorId={selectedEntry.tailor.id}
            outstandingPayable={selectedEntry.settlement.outstanding_payable}
          />
        </>
      )}
    </Box>
  );
};

const TailorAssignmentBreakdown: React.FC<{
  periodId: number;
  tailorId: number;
  entry: PayrollEntry | null;
  data?: {
    tailor: { id: number; name: string; mobile_number: string; is_active: boolean };
    assignments: Array<{
      id: number;
      order_number: string;
      garment_type: string;
      assigned_quantity: number;
      completed_quantity: number;
      remaining_quantity: number;
      rate_per_piece_snapshot: number;
      earned_amount: number;
      completed_at: string | null;
    }>;
  };
}> = ({ tailorId, entry, data }) => {
  const assignments = data?.assignments ?? [];

  return (
    <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
      <Box sx={{ p: 2, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
        <Typography sx={{ fontWeight: 700 }}>
          Assignment Breakdown · {data?.tailor.name ?? `Tailor #${tailorId}`}
        </Typography>
        {entry && (
          <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
            {entry.present_days} present · {entry.half_days} half day · {entry.absent_days} absent ·{' '}
            {formatPieces(entry.completed_pieces)} completed ·{' '}
            <Chip
              label={SALARY_MODEL_LABELS[entry.salary_model]}
              size="small"
              sx={{
                fontWeight: 600,
                fontSize: '0.7rem',
                height: 18,
                backgroundColor:
                  entry.salary_model === 'FIXED_SALARY'
                    ? '#EDE9FE'
                    : entry.salary_model === 'MIXED'
                      ? '#E0F2FE'
                      : '#F1F5F9',
                color:
                  entry.salary_model === 'FIXED_SALARY'
                    ? '#6D28D9'
                    : entry.salary_model === 'MIXED'
                      ? '#0369A1'
                      : '#475569',
              }}
            />{' '}
            {entry.salary_model !== 'PER_GARMENT' &&
              `${formatCurrency(entry.fixed_salary_amount)} fixed · `}
            {formatCurrency(entry.piece_rate_earnings)} piece · {formatCurrency(entry.gross_salary)}{' '}
            gross · {formatCurrency(entry.total_payable)} payable
          </Typography>
        )}
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Order</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Assigned</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Completed</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Rate</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Earned</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assignments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography sx={{ color: '#64748B' }}>
                    No completed assignments in this period.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              assignments.map((assignment) => (
                <TableRow
                  key={assignment.id}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell>
                    <Typography variant="body2">{assignment.order_number}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{assignment.garment_type}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatPieces(assignment.assigned_quantity)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatPieces(assignment.completed_quantity)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatCurrency(assignment.rate_per_piece_snapshot)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#15803D' }}>
                      {formatCurrency(assignment.earned_amount)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

const SettlementPanel: React.FC<{
  entry: PayrollEntry;
  isStaff: boolean;
  isFinalized: boolean;
  paymentHistory?: PaymentHistoryResponse;
  onRecordPayment: () => void;
  onSettleInFull: () => void;
  onApplyAdvance: () => void;
}> = ({
  entry,
  isStaff,
  isFinalized,
  paymentHistory,
  onRecordPayment,
  onSettleInFull,
  onApplyAdvance,
}) => {
  const settlement: PayrollSettlement = entry.settlement;
  const statusColors = SETTLEMENT_STATUS_COLORS[settlement.settlement_status];
  const payments = paymentHistory?.payments ?? [];

  return (
    <Stack direction="column" spacing={2}>
      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box
          sx={{
            p: 2,
            backgroundColor: '#F8FAFC',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1.5,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: '10px',
                backgroundColor: '#EFF6FF',
                color: '#1E3A8A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <PaymentsIcon fontSize="small" />
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 700 }}>Settlement · {entry.tailor.name}</Typography>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.25 }}>
                <Chip
                  label={SETTLEMENT_STATUS_LABELS[settlement.settlement_status]}
                  size="small"
                  sx={{
                    fontWeight: 600,
                    backgroundColor: statusColors.bg,
                    color: statusColors.text,
                  }}
                />
                <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                  {settlement.payment_count} payment{settlement.payment_count === 1 ? '' : 's'}
                </Typography>
              </Stack>
            </Box>
          </Box>
          {isStaff && isFinalized && (
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Button
                size="small"
                variant="outlined"
                startIcon={<AccountBalanceWalletIcon fontSize="small" />}
                onClick={onApplyAdvance}
              >
                Apply Advance
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<PaymentsIcon fontSize="small" />}
                onClick={onRecordPayment}
              >
                Record Payment
              </Button>
              {settlement.outstanding_payable > 0 && (
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<VerifiedUserIcon fontSize="small" />}
                  onClick={onSettleInFull}
                  sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
                >
                  Settle in Full
                </Button>
              )}
            </Stack>
          )}
          {!isFinalized && (
            <Typography variant="body2" sx={{ color: '#94A3B8' }}>
              Finalize the payroll period to record payments and advances.
            </Typography>
          )}
        </Box>

        <Box sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
            <SummaryCard
              label="GROSS PAYABLE"
              value={formatCurrency(settlement.gross_payable)}
              color="#0F172A"
            />
            <SummaryCard
              label="ADVANCE DEDUCTION"
              value={`-${formatCurrency(settlement.advance_deductions)}`}
              color="#B45309"
            />
            <SummaryCard
              label="PAID AMOUNT"
              value={formatCurrency(settlement.payments_recorded)}
              color="#1E3A8A"
            />
            <SummaryCard
              label="OUTSTANDING"
              value={formatCurrency(settlement.outstanding_payable)}
              color={settlement.outstanding_payable === 0 ? '#15803D' : '#B45309'}
            />
          </Stack>
        </Box>
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ p: 2, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
          <Typography sx={{ fontWeight: 700 }}>Payment History</Typography>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Reference</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Notes</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography sx={{ color: '#64748B' }}>No payments recorded yet.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((payment) => {
                  return (
                    <TableRow
                      key={payment.id}
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell>
                        <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {formatCurrency(payment.amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.payment_method_display}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.reference || '-'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 220 }}>
                          {payment.notes || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.recorded_by_name || '-'}</Typography>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Stack>
  );
};
