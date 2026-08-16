import React, { useState } from 'react';
import { Box, Button, Stack, Tooltip, Typography } from '@mui/material';
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
import { PAYROLL_PERIOD_STATUS_LABELS, SETTLEMENT_STATUS_LABELS } from '../types/payroll';
import type { PayrollPeriod, PayrollPeriodPayload } from '../types/payroll';
import { PageHeader } from '../components/ui/PageHeader';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import type { StatusTone } from '../components/ui/StatusBadge';

const PAGE_SIZE = 7;

const PERIOD_TONES: Record<string, StatusTone> = {
  DRAFT: 'neutral',
  CALCULATED: 'gold',
  FINALIZED: 'success',
};

const SETTLEMENT_TONES: Record<string, StatusTone> = {
  UNPAID: 'warning',
  PARTIALLY_PAID: 'gold',
  SETTLED: 'success',
};

export const Payroll: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dialogOpen, setDialogOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [confirmState, setConfirmState] = useState<'calculate' | 'finalize' | null>(null);
  const [targetPeriod, setTargetPeriod] = useState<PayrollPeriod | null>(null);

  const { data, isLoading, isError, error, isFetching, refetch } = usePayrollPeriodList(page);

  const createMutation = useCreatePayrollPeriod();
  const calculateMutation = useCalculatePayrollPeriod();
  const finalizeMutation = useFinalizePayrollPeriod();

  const handleCreate = async (payload: PayrollPeriodPayload) => {
    const created = await createMutation.mutateAsync(payload);
    setPage(1);
    return created;
  };

  const openConfirm = (action: 'calculate' | 'finalize', period: PayrollPeriod) => {
    setConfirmState(action);
    setTargetPeriod(period);
  };

  const closeConfirm = () => {
    setConfirmState(null);
    setTargetPeriod(null);
  };

  const handleConfirmedAction = async () => {
    if (!targetPeriod) return;
    try {
      if (confirmState === 'calculate') {
        await calculateMutation.mutateAsync(targetPeriod.id);
      } else if (confirmState === 'finalize') {
        await finalizeMutation.mutateAsync(targetPeriod.id);
      }
      closeConfirm();
    } catch (actionError) {
      window.alert(getApiErrorMessage(actionError));
      closeConfirm();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Payroll"
        subtitle="Create payroll periods and calculate piece-rate earnings."
        icon={<PointOfSaleIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Payroll' }]}
        actions={
          isStaff && (
            <Button
              variant="contained"
              startIcon={<AddCardIcon />}
              onClick={() => setDialogOpen(true)}
            >
              New Period
            </Button>
          )
        }
      />

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(period) => period.id}
        onRowClick={(period) => navigate(`/payroll/${period.id}`)}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No payroll periods yet"
        emptyMessage="Create a payroll period to start tracking earnings."
        columns={[
          {
            label: 'Period',
            primary: true,
            render: (period) => (
              <Box>
                <Typography sx={{ fontWeight: 600 }}>
                  {formatDate(period.period_start)} – {formatDate(period.period_end)}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                  #{period.id}
                </Typography>
              </Box>
            ),
          },
          {
            label: 'Status',
            render: (period) => (
              <StatusBadge
                label={PAYROLL_PERIOD_STATUS_LABELS[period.status]}
                tone={PERIOD_TONES[period.status] ?? 'neutral'}
              />
            ),
          },
          {
            label: 'Completed Pieces',
            render: (period) => (
              <Typography variant="body2">{formatPieces(period.total_completed_pieces)}</Typography>
            ),
          },
          {
            label: 'Piece Rate Earnings',
            render: (period) => (
              <Typography variant="body2">
                {formatCurrency(period.total_piece_rate_earnings)}
              </Typography>
            ),
          },
          {
            label: 'Attendance',
            render: (period) => (
              <Typography variant="body2">
                {formatCurrency(period.total_attendance_amount)}
              </Typography>
            ),
          },
          {
            label: 'Total Payable',
            render: (period) => (
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#1F5C3C' }}>
                {formatCurrency(period.total_payable)}
              </Typography>
            ),
          },
          {
            label: 'Paid',
            render: (period) => (
              <Typography variant="body2">
                {formatCurrency(period.settlement.payments_recorded)}
              </Typography>
            ),
          },
          {
            label: 'Outstanding',
            render: (period) => (
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: period.settlement.outstanding_payable > 0 ? '#8F4A00' : '#1F5C3C',
                }}
              >
                {formatCurrency(period.settlement.outstanding_payable)}
              </Typography>
            ),
          },
          {
            label: 'Settlement',
            render: (period) => (
              <StatusBadge
                label={SETTLEMENT_STATUS_LABELS[period.settlement.settlement_status]}
                tone={SETTLEMENT_TONES[period.settlement.settlement_status] ?? 'neutral'}
              />
            ),
          },
          {
            label: 'Tailors',
            render: (period) => <Typography variant="body2">{period.entry_count}</Typography>,
          },
        ]}
        actions={(period) => (
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
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
                    openConfirm('calculate', period);
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
                    openConfirm('finalize', period);
                  }}
                >
                  Finalize
                </Button>
              </Tooltip>
            )}
          </Stack>
        )}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <PayrollPeriodDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleCreate}
      />

      <ConfirmDialog
        open={confirmState !== null}
        title={confirmState === 'calculate' ? 'Calculate Payroll' : 'Finalize Payroll'}
        message={
          targetPeriod
            ? confirmState === 'calculate'
              ? `Calculate payroll for ${formatDate(targetPeriod.period_start)} to ${formatDate(targetPeriod.period_end)}? Entries will be generated from completed assignments and attendance.`
              : `Finalize payroll for ${formatDate(targetPeriod.period_start)} to ${formatDate(targetPeriod.period_end)}? This locks the amounts and cannot be undone.`
            : ''
        }
        confirmLabel={confirmState === 'calculate' ? 'Calculate' : 'Finalize'}
        tone={confirmState === 'calculate' ? 'primary' : 'warning'}
        loading={calculateMutation.isPending || finalizeMutation.isPending}
        onConfirm={handleConfirmedAction}
        onCancel={closeConfirm}
      />
    </Box>
  );
};

export default Payroll;
