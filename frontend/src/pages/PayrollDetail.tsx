import React, { useState } from 'react';
import {
  Box,
  Button,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import CalculateIcon from '@mui/icons-material/Calculate';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import PaymentsIcon from '@mui/icons-material/Payments';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import { useParams } from 'react-router-dom';import { useAuth } from '../context/useAuth';
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
  SALARY_MODEL_LABELS,
  SETTLEMENT_STATUS_LABELS,
} from '../types/payroll';
import type {
  PayrollEntry,
  PaymentHistoryResponse,
  PaymentPayload,
} from '../types/payroll';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { StatCard } from '../components/ui/StatCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { ErrorState } from '../components/ui/ErrorState';
import type { StatusTone } from '../components/ui/StatusBadge';

const SETTLEMENT_TONES: Record<string, StatusTone> = {
  UNPAID: 'warning',
  PARTIALLY_PAID: 'gold',
  SETTLED: 'success',
};

const SALARY_MODEL_TONES: Record<string, StatusTone> = {
  PER_GARMENT: 'neutral',
  FIXED_SALARY: 'gold',
  MIXED: 'info',
};

export const PayrollDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const periodId = Number(id ?? 0);
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [selectedTailorId, setSelectedTailorId] = useState<number | null>(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [settleDialogOpen, setSettleDialogOpen] = useState(false);
  const [advanceDialogOpen, setAdvanceDialogOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'calculate' | 'finalize' | null>(null);

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
    setConfirmAction(null);
    try {
      await calculateMutation.mutateAsync(periodId);
    } catch (calculateError) {
      window.alert(getApiErrorMessage(calculateError));
    }
  };

  const handleFinalize = async () => {
    setConfirmAction(null);
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
        <Typography color="text.secondary">Loading period…</Typography>
      </Box>
    );
  }

  if (isError || !period) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title={`${formatDate(period.period_start)} – ${formatDate(period.period_end)}`}
        subtitle={`Period #${period.id}${period.created_by_name ? ` · Created by ${period.created_by_name}` : ''}`}
        icon={<PointOfSaleIcon />}
        backTo="/payroll"
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Payroll', to: '/payroll' }, { label: `Period #${period.id}` }]}
        actions={
          isStaff && (
            <Stack direction="row" spacing={1}>
              {period.status === 'DRAFT' && (
                <Button
                  variant="contained"
                  startIcon={<CalculateIcon />}
                  disabled={calculateMutation.isPending || finalizeMutation.isPending}
                  onClick={() => setConfirmAction('calculate')}
                >
                  Calculate Payroll
                </Button>
              )}
              {period.status === 'CALCULATED' && (
                <Button
                  variant="contained"
                  startIcon={<CheckCircleOutlineIcon />}
                  disabled={calculateMutation.isPending || finalizeMutation.isPending}
                  onClick={() => setConfirmAction('finalize')}
                >
                  Finalize
                </Button>
              )}
            </Stack>
          )
        }
      />

      {period.notes && (
        <Box
          sx={{
            p: 2,
            borderRadius: '12px',
            border: '1px solid #E7E0D0',
            backgroundColor: '#FBF6EA',
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
            NOTES
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.5 }}>
            {period.notes}
          </Typography>
        </Box>
      )}

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
        }}
      >
        <StatCard label="Total Completed Pieces" value={formatPieces(period.total_completed_pieces)} tone="default" />
        <StatCard label="Piece Rate Earnings" value={formatCurrency(period.total_piece_rate_earnings)} tone="gold" />
        <StatCard label="Total Fixed Salary" value={formatCurrency(period.total_fixed_salary)} tone="info" />
        <StatCard label="Total Gross Salary" value={formatCurrency(period.total_gross_salary)} tone="default" />
        <StatCard label="Attendance" value={formatCurrency(period.total_attendance_amount)} tone="default" />
        <StatCard label="Total Payable" value={formatCurrency(period.total_payable)} tone="success" />
        <StatCard label="Tailors in Period" value={String(period.entry_count)} tone="default" />
      </Box>

      <TableCard>
        <Table size="medium">
          <TableHead>
            <TableRow>
              <TableCell>Tailor</TableCell>
              <TableCell>Present</TableCell>
              <TableCell>Half Day</TableCell>
              <TableCell>Absent</TableCell>
              <TableCell>Completed</TableCell>
              <TableCell>Salary Model</TableCell>
              <TableCell>Fixed Salary</TableCell>
              <TableCell>Piece Rate Earnings</TableCell>
              <TableCell>Attendance Amount</TableCell>
              <TableCell>Total Payable</TableCell>
              <TableCell>Advance</TableCell>
              <TableCell>Paid</TableCell>
              <TableCell>Outstanding</TableCell>
              <TableCell>Settlement</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.length === 0 ? (
              <TableStateRow
                colSpan={14}
                state="empty"
                emptyTitle="No tailor entries yet"
                emptyMessage={
                  period.status === 'DRAFT'
                    ? 'Calculate payroll to generate tailor entries.'
                    : 'No tailor entries found for this period.'
                }
              />
            ) : (
              entries.map((entry) => (
                <TableRow
                  key={entry.id}
                  hover
                  sx={{
                    cursor: 'pointer',
                    '&:last-child td, &:last-child th': { border: 0 },
                    backgroundColor:
                      selectedTailorId === entry.tailor.id ? '#FBF6EA' : 'transparent',
                  }}
                  onClick={() =>
                    setSelectedTailorId((current) =>
                      current === entry.tailor.id ? null : entry.tailor.id
                    )
                  }
                >
                  <TableCell>
                    <Typography sx={{ fontWeight: 600 }}>{entry.tailor.name}</Typography>
                    <Typography variant="caption" sx={{ color: 'text.disabled' }}>
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
                    <Typography variant="body2">{formatPieces(entry.completed_pieces)}</Typography>
                  </TableCell>
                  <TableCell>
                    <StatusBadge
                      label={SALARY_MODEL_LABELS[entry.salary_model]}
                      tone={SALARY_MODEL_TONES[entry.salary_model] ?? 'neutral'}
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
                    <Typography variant="body2">{formatCurrency(entry.piece_rate_earnings)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatCurrency(entry.attendance_amount)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#1F5C3C' }}>
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
                          entry.settlement.outstanding_payable === 0 ? '#1F5C3C' : '#8F4A00',
                      }}
                    >
                      {formatCurrency(entry.settlement.outstanding_payable)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <StatusBadge
                      label={SETTLEMENT_STATUS_LABELS[entry.settlement.settlement_status]}
                      tone={SETTLEMENT_TONES[entry.settlement.settlement_status] ?? 'neutral'}
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableCard>

      {selectedTailorId && (
        <>
          <TailorAssignmentBreakdown
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

      <ConfirmDialog
        open={confirmAction !== null}
        title={confirmAction === 'calculate' ? 'Calculate Payroll' : 'Finalize Payroll'}
        message={
          confirmAction === 'calculate'
            ? 'Calculate payroll for this period? Existing entries will be replaced with fresh figures.'
            : 'Finalize this payroll period? The amounts will be locked and cannot be recalculated.'
        }
        confirmLabel={confirmAction === 'calculate' ? 'Calculate' : 'Finalize'}
        tone={confirmAction === 'calculate' ? 'primary' : 'warning'}
        loading={calculateMutation.isPending || finalizeMutation.isPending}
        onConfirm={confirmAction === 'calculate' ? handleCalculate : handleFinalize}
        onCancel={() => setConfirmAction(null)}
      />
    </Box>
  );
};

const TailorAssignmentBreakdown: React.FC<{
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
    <SectionCard
      title={`Assignment Breakdown · ${data?.tailor.name ?? `Tailor #${tailorId}`}`}
      noPadding
    >
      {entry && (
        <Box sx={{ px: 2.5, py: 1.5, backgroundColor: '#FBF6EA', borderBottom: '1px solid #E7E0D0' }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {entry.present_days} present · {entry.half_days} half day · {entry.absent_days} absent ·{' '}
            {formatPieces(entry.completed_pieces)} completed ·{' '}
            <StatusBadge
              label={SALARY_MODEL_LABELS[entry.salary_model]}
              tone={SALARY_MODEL_TONES[entry.salary_model] ?? 'neutral'}
            />
            {entry.salary_model !== 'PER_GARMENT' &&
              ` ${formatCurrency(entry.fixed_salary_amount)} fixed · `}
            {formatCurrency(entry.piece_rate_earnings)} piece · {formatCurrency(entry.gross_salary)}{' '}
            gross · {formatCurrency(entry.total_payable)} payable
          </Typography>
        </Box>
      )}
      <TableCard sx={{ border: 'none', borderRadius: 0 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Order</TableCell>
              <TableCell>Garment</TableCell>
              <TableCell>Assigned</TableCell>
              <TableCell>Completed</TableCell>
              <TableCell>Rate</TableCell>
              <TableCell>Earned</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assignments.length === 0 ? (
              <TableStateRow
                colSpan={6}
                state="empty"
                emptyTitle="No completed assignments"
                emptyMessage="No completed assignments in this period."
              />
            ) : (
              assignments.map((assignment) => (
                <TableRow key={assignment.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                  <TableCell>
                    <Typography variant="body2">{assignment.order_number}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{assignment.garment_type}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatPieces(assignment.assigned_quantity)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatPieces(assignment.completed_quantity)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatCurrency(assignment.rate_per_piece_snapshot)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#1F5C3C' }}>
                      {formatCurrency(assignment.earned_amount)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableCard>
    </SectionCard>
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
  const settlement = entry.settlement;
  const payments = paymentHistory?.payments ?? [];

  return (
    <Stack direction="column" spacing={2}>
      <SectionCard
        title={`Settlement · ${entry.tailor.name}`}
        subtitle={`${settlement.payment_count} payment${settlement.payment_count === 1 ? '' : 's'}`}
        icon={<PaymentsIcon />}
        noPadding
        action={
          <>
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
                  >
                    Settle in Full
                  </Button>
                )}
              </Stack>
            )}
            {!isFinalized && (
              <Typography variant="body2" sx={{ color: 'text.disabled' }}>
                Finalize the payroll period to record payments and advances.
              </Typography>
            )}
          </>
        }
      >
        <Box sx={{ px: 2.5, py: 2 }}>
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
            }}
          >
            <StatCard label="Gross Payable" value={formatCurrency(settlement.gross_payable)} tone="default" />
            <StatCard label="Advance Deduction" value={`-${formatCurrency(settlement.advance_deductions)}`} tone="warning" />
            <StatCard label="Paid Amount" value={formatCurrency(settlement.payments_recorded)} tone="gold" />
            <StatCard
              label="Outstanding"
              value={formatCurrency(settlement.outstanding_payable)}
              tone={settlement.outstanding_payable === 0 ? 'success' : 'warning'}
            />
          </Box>
        </Box>
      </SectionCard>

      <SectionCard title="Payment History" icon={<AccountBalanceWalletIcon />} noPadding>
        <TableCard sx={{ border: 'none', borderRadius: 0 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Method</TableCell>
                <TableCell>Reference</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.length === 0 ? (
                <TableStateRow
                  colSpan={6}
                  state="empty"
                  emptyTitle="No payments recorded yet"
                  emptyMessage="Payments for this tailor will appear here."
                />
              ) : (
                payments.map((payment) => (
                  <TableRow key={payment.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
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
                ))
              )}
            </TableBody>
          </Table>
        </TableCard>
      </SectionCard>
    </Stack>
  );
};

export default PayrollDetail;
