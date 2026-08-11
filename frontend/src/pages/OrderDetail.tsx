import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import CancelIcon from '@mui/icons-material/Cancel';
import StraightenIcon from '@mui/icons-material/Straighten';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HistoryIcon from '@mui/icons-material/History';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useChangeOrderStatus, useOrder, useUpdateOrder } from '../hooks/useOrders';
import { useCreateOrderInvoice, useInvoiceList } from '../hooks/useInvoices';
import {
  useChangeWorkAssignmentStatus,
  useUpdateWorkAssignment,
  useWorkAssignmentList,
} from '../hooks/useTailors';
import AssignWorkDialog from '../components/AssignWorkDialog';
import { OrderCommunicationPanel } from '../components/OrderCommunicationPanel';
import ReportProgressDialog from '../components/ReportProgressDialog';
import WorkAssignmentStatusChip from '../components/WorkAssignmentStatusChip';
import { PageHeader } from '../components/ui/PageHeader';
import { InfoField } from '../components/ui/InfoField';
import { SectionCard } from '../components/ui/SectionCard';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';
import { ErrorState } from '../components/ui/ErrorState';
import { TableStateRow } from '../components/ui/TableStateRow';
import { MEASUREMENT_FIELD_LABELS } from '../types/customers';
import type { MeasurementFieldName } from '../types/customers';
import {
  NEXT_STATUS,
  ORDER_STATUS_COLORS,
  ORDER_STATUS_LABELS,
  TERMINAL_ORDER_STATUSES,
} from '../types/orders';
import type { Order, OrderItem, OrderStatus, OrderUpdatePayload } from '../types/orders';
import { INVOICE_STATUS_LABELS } from '../types/billing';
import type { InvoiceStatus } from '../types/billing';
import { NEXT_ASSIGNMENT_STATUS, WORK_ASSIGNMENT_STATUS_LABELS } from '../types/tailors';
import type { WorkAssignment, WorkAssignmentStatus } from '../types/tailors';

const ORDER_STATUS_TONES: Record<OrderStatus, StatusTone> = {
  NEW: 'gold',
  CUTTING: 'warning',
  STITCHING: 'info',
  READY: 'success',
  COLLECTED: 'neutral',
  CANCELLED: 'error',
};

const INVOICE_STATUS_TONES: Record<InvoiceStatus, StatusTone> = {
  UNPAID: 'error',
  PARTIALLY_PAID: 'warning',
  PAID: 'success',
};

interface EditOrderDialogProps {
  open: boolean;
  order: Order | null;
  onClose: () => void;
  submit: (payload: OrderUpdatePayload) => Promise<unknown>;
}

const EditOrderDialog: React.FC<EditOrderDialogProps> = ({ open, order, onClose, submit }) => {
  const [notes, setNotes] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open && order) {
      setNotes(order.notes ?? '');
      setExpectedDelivery(order.expected_delivery_date ?? '');
      setSubmitError(null);
    }
  }, [open, order]);

  const handleSubmit = async () => {
    if (!order) return;
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      await submit({
        notes: notes.trim(),
        expected_delivery_date: expectedDelivery || null,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Edit Order</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}
          <TextField
            label="Expected Delivery"
            type="date"
            value={expectedDelivery}
            onChange={(event) => setExpectedDelivery(event.target.value)}
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            fullWidth
            multiline
            minRows={3}
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const MeasurementSnapshotRow: React.FC<{ item: OrderItem }> = ({ item }) => {
  const [open, setOpen] = useState(false);
  const snapshot = item.measurement_snapshot;
  const fields = snapshot ? (Object.entries(snapshot) as Array<[string, number | null]>) : [];

  if (!snapshot || fields.length === 0) return null;

  return (
    <>
      <TableRow sx={{ '&:last-child td': { border: 0 } }}>
        <TableCell colSpan={7} sx={{ py: 0.5 }}>
          <Button
            size="small"
            startIcon={<StraightenIcon fontSize="small" />}
            onClick={() => setOpen((value) => !value)}
            sx={{ textTransform: 'none' }}
          >
            {open ? 'Hide measurements' : 'View measurements used'}
          </Button>
        </TableCell>
      </TableRow>
      {open && (
        <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
          <TableCell colSpan={7} sx={{ pb: 2 }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: 'repeat(2, 1fr)',
                  sm: 'repeat(3, 1fr)',
                  md: 'repeat(4, 1fr)',
                },
                gap: 2,
              }}
            >
              {fields.map(([field, value]) => (
                <Box key={field}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.secondary',
                      display: 'block',
                      fontSize: '0.7rem',
                      textTransform: 'uppercase',
                      fontWeight: 600,
                    }}
                  >
                    {MEASUREMENT_FIELD_LABELS[field as MeasurementFieldName] ?? field}
                  </Typography>
                  <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
                    {value == null ? '-' : `${value} in`}
                  </Typography>
                </Box>
              ))}
            </Box>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

export const OrderDetail: React.FC = () => {
  const { id } = useParams();
  const orderId = Number(id);
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data: order, isLoading, isError, error, refetch } = useOrder(orderId);
  const updateMutation = useUpdateOrder(orderId);
  const statusMutation = useChangeOrderStatus(orderId);

  const validOrderId = Number.isFinite(orderId) && orderId > 0 ? orderId : 0;
  const { data: orderInvoicesData } = useInvoiceList({ order: validOrderId }, validOrderId > 0);
  const createInvoiceMutation = useCreateOrderInvoice();

  const [statusFilter, setStatusFilter] = useState<WorkAssignmentStatus | ''>('');
  const { data: assignmentsData } = useWorkAssignmentList({
    order: validOrderId,
    status: statusFilter,
  });
  const assignmentStatusMutation = useChangeWorkAssignmentStatus();
  const assignmentProgressMutation = useUpdateWorkAssignment();

  const existingInvoice = orderInvoicesData?.results[0];

  const [editOpen, setEditOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [assignOpen, setAssignOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<WorkAssignment | null>(null);
  const [progressOpen, setProgressOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);

  const assignments = useMemo(() => assignmentsData?.results ?? [], [assignmentsData]);

  const nextStatus = order ? NEXT_STATUS[order.status] : undefined;
  const isTerminal = order ? TERMINAL_ORDER_STATUSES.has(order.status) : false;

  const handleCreateInvoice = async () => {
    if (!order) return;
    setActionError(null);
    try {
      const response = await createInvoiceMutation.mutateAsync({ orderId: order.id, payload: {} });
      navigate(`/invoices/${response.invoice.id}`);
    } catch (invoiceError) {
      setActionError(getApiErrorMessage(invoiceError));
    }
  };

  const handleAdvance = async () => {
    if (!order || !nextStatus) return;
    setActionError(null);
    try {
      await statusMutation.mutateAsync(nextStatus);
    } catch (transitionError) {
      setActionError(getApiErrorMessage(transitionError));
    }
  };

  const handleCancel = async () => {
    if (!order) return;
    setActionError(null);
    try {
      await statusMutation.mutateAsync('CANCELLED');
      setCancelOpen(false);
    } catch (transitionError) {
      setActionError(getApiErrorMessage(transitionError));
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !order) {
    return (
      <Box>
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        <Stack direction="row" justifyContent="center" sx={{ mt: 2 }}>
          <Button color="inherit" onClick={() => navigate('/orders')}>
            Back to Orders
          </Button>
        </Stack>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title={order.order_number}
        subtitle={`${order.customer.full_name} · ${order.customer.mobile_number}`}
        icon={<ShoppingBagIcon />}
        crumbs={[
          { label: 'Dashboard', to: '/dashboard' },
          { label: 'Orders', to: '/orders' },
          { label: order.order_number },
        ]}
        backTo="/orders"
        actions={
          <>
            <StatusBadge
              label={ORDER_STATUS_LABELS[order.status]}
              tone={ORDER_STATUS_TONES[order.status]}
            />
            {isStaff && !isTerminal && (
              <>
                <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
                  Edit
                </Button>
                {nextStatus && (
                  <Button
                    variant="contained"
                    startIcon={nextStatus === 'COLLECTED' ? <CheckCircleIcon /> : undefined}
                    onClick={handleAdvance}
                  >
                    Move to {ORDER_STATUS_LABELS[nextStatus]}
                  </Button>
                )}
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CancelIcon />}
                  onClick={() => setCancelOpen(true)}
                >
                  Cancel
                </Button>
              </>
            )}
            {isStaff && existingInvoice && (
              <Button
                variant="outlined"
                startIcon={<ReceiptLongIcon />}
                onClick={() => navigate(`/invoices/${existingInvoice.id}`)}
              >
                View Invoice
              </Button>
            )}
            {isStaff && !existingInvoice && (
              <Button
                variant="outlined"
                startIcon={<ReceiptLongIcon />}
                onClick={handleCreateInvoice}
                disabled={createInvoiceMutation.isPending}
              >
                Create Invoice
              </Button>
            )}
          </>
        }
      />

      {actionError && <Alert severity="error">{actionError}</Alert>}
      {statusMutation.isPending && (
        <Alert severity="info" icon={<CircularProgress size={16} />}>
          Updating order status...
        </Alert>
      )}

      <SectionCard title="Order Summary">
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 3,
          }}
        >
          <InfoField label="Order Date" value={formatDate(order.order_date)} />
          <InfoField
            label="Expected Delivery"
            value={order.expected_delivery_date ? formatDate(order.expected_delivery_date) : '-'}
          />
          <InfoField label="Total Amount" value={formatCurrency(Number(order.total_amount))} />
          <InfoField
            label="Collected At"
            value={
              order.collected_at ? formatDate(order.collected_at, 'DD MMM YYYY, hh:mm A') : '-'
            }
          />
        </Box>
        {order.notes && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              Order Notes
            </Typography>
            <Typography
              variant="body2"
              sx={{ mt: 0.5, color: 'text.primary', whiteSpace: 'pre-wrap' }}
            >
              {order.notes}
            </Typography>
          </Box>
        )}
      </SectionCard>

      <SectionCard
        title="Billing"
        action={
          order.payment_summary?.has_invoice && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<ReceiptLongIcon />}
              onClick={() => navigate(`/invoices/${existingInvoice?.id ?? ''}`)}
              disabled={!existingInvoice}
            >
              View Invoice
            </Button>
          )
        }
      >
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 3,
          }}
        >
          <InfoField label="Order Total" value={formatCurrency(Number(order.total_amount))} />
          <InfoField
            label="Total Paid"
            value={formatCurrency(Number(order.payment_summary?.total_paid ?? 0))}
          />
          <InfoField
            label="Outstanding Balance"
            value={formatCurrency(
              Number(order.payment_summary?.outstanding_balance ?? order.total_amount)
            )}
          />
          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              Payment Status
            </Typography>
            {order.payment_summary?.has_invoice ? (
              <Box sx={{ mt: 0.5 }}>
                <StatusBadge
                  label={INVOICE_STATUS_LABELS[order.payment_summary.payment_status]}
                  tone={INVOICE_STATUS_TONES[order.payment_summary.payment_status]}
                />
              </Box>
            ) : (
              <Typography sx={{ fontWeight: 600, mt: 0.5, color: 'text.secondary' }}>
                No invoice yet
              </Typography>
            )}
          </Box>
        </Box>
      </SectionCard>

      <OrderCommunicationPanel orderId={orderId} />

      <SectionCard
        title="Order Items"
        subtitle="Measurements snapshot at the time of ordering"
        icon={<StraightenIcon />}
        noPadding
      >
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Qty
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Version</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Unit Price
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Line Total
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {order.items.map((item) => (
                <React.Fragment key={item.id}>
                  <TableRow sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell sx={{ fontWeight: 600 }}>{item.garment_type}</TableCell>
                    <TableCell align="center">{item.quantity}</TableCell>
                    <TableCell>
                      <Chip
                        label={`V${item.measurement_version ?? '-'}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(Number(item.unit_price))}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      {formatCurrency(Number(item.line_total))}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        {item.notes || '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <MeasurementSnapshotRow item={item} />
                </React.Fragment>
              ))}
              <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                <TableCell colSpan={4} sx={{ fontWeight: 700 }}>
                  Total Amount
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, color: '#7A5E0C' }}>
                  {formatCurrency(Number(order.total_amount))}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </SectionCard>

      <SectionCard
        title="Work Assignments"
        subtitle="Piece-rate work assigned for this order"
        icon={<PersonAddAltIcon />}
        action={
          <Stack direction="row" spacing={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(event) =>
                  setStatusFilter(event.target.value as WorkAssignmentStatus | '')
                }
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="ASSIGNED">Assigned</MenuItem>
                <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
                <MenuItem value="COMPLETED">Completed</MenuItem>
              </Select>
            </FormControl>
            {isStaff && (
              <Button
                variant="contained"
                startIcon={<PersonAddAltIcon />}
                onClick={() => setAssignOpen(true)}
              >
                Assign Work
              </Button>
            )}
          </Stack>
        }
        noPadding
      >
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                <TableCell sx={{ fontWeight: 700 }}>Tailor</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Assigned
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Completed
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Outstanding
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Rate
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Earned
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                {isStaff && (
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    Actions
                  </TableCell>
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {assignments.length === 0 ? (
                <TableStateRow
                  colSpan={isStaff ? 9 : 8}
                  state="empty"
                  emptyTitle={
                    statusFilter
                      ? 'No assignments match this status.'
                      : 'No work assigned for this order yet.'
                  }
                />
              ) : (
                assignments.map((assignment) => {
                  const nextStatus = NEXT_ASSIGNMENT_STATUS[assignment.status];
                  return (
                    <TableRow key={assignment.id} hover>
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>{assignment.tailor.name}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>
                          {assignment.order_item.garment_type}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {formatPieces(assignment.assigned_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {formatPieces(assignment.completed_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#8F4A00' }}>
                          {formatPieces(
                            assignment.assigned_quantity - assignment.completed_quantity
                          )}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {formatCurrency(assignment.rate_per_piece_snapshot)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#1F5C3C' }}>
                          {formatCurrency(assignment.earned_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <WorkAssignmentStatusChip status={assignment.status} />
                      </TableCell>
                      {isStaff && (
                        <TableCell align="right">
                          {nextStatus && (
                            <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                              <Tooltip title="Report completed quantity">
                                <Button
                                  size="small"
                                  startIcon={<EditIcon fontSize="small" />}
                                  disabled={assignmentProgressMutation.isPending}
                                  onClick={() => {
                                    setSelectedAssignment(assignment);
                                    setProgressOpen(true);
                                  }}
                                >
                                  Progress
                                </Button>
                              </Tooltip>
                              <Tooltip
                                title={`Move to ${WORK_ASSIGNMENT_STATUS_LABELS[nextStatus]}`}
                              >
                                <Button
                                  size="small"
                                  variant="contained"
                                  color={nextStatus === 'COMPLETED' ? 'success' : 'primary'}
                                  disabled={assignmentStatusMutation.isPending}
                                  startIcon={
                                    nextStatus === 'COMPLETED' ? (
                                      <CheckCircleIcon fontSize="small" />
                                    ) : (
                                      <PlayArrowIcon fontSize="small" />
                                    )
                                  }
                                  onClick={async () => {
                                    setActionError(null);
                                    try {
                                      await assignmentStatusMutation.mutateAsync({
                                        id: assignment.id,
                                        status: nextStatus,
                                      });
                                    } catch (transitionError) {
                                      setActionError(getApiErrorMessage(transitionError));
                                    }
                                  }}
                                >
                                  {nextStatus === 'COMPLETED'
                                    ? 'Complete'
                                    : WORK_ASSIGNMENT_STATUS_LABELS[nextStatus]}
                                </Button>
                              </Tooltip>
                            </Stack>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </SectionCard>

      <SectionCard
        title="Status History"
        subtitle="Every status change is recorded with the staff member who made it"
        icon={<HistoryIcon />}
      >
        <Stack spacing={2}>
          {order.status_history.map((entry, index) => {
            const colors = ORDER_STATUS_COLORS[entry.to_status];
            return (
              <Stack key={entry.id} direction="row" spacing={2} alignItems="flex-start">
                <Stack alignItems="center" sx={{ minWidth: 24 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: colors.text,
                      mt: 0.75,
                    }}
                  />
                  {index < order.status_history.length - 1 && (
                    <Box sx={{ width: 2, height: '100%', backgroundColor: '#E7E0D0' }} />
                  )}
                </Stack>
                <Box sx={{ flex: 1 }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
                      {entry.from_status
                        ? `${ORDER_STATUS_LABELS[entry.from_status]} → ${ORDER_STATUS_LABELS[entry.to_status]}`
                        : `Order placed · ${ORDER_STATUS_LABELS[entry.to_status]}`}
                    </Typography>
                  </Stack>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {entry.changed_by_username ?? 'System'} ·{' '}
                    {formatDate(entry.changed_at, 'DD MMM YYYY, hh:mm A')}
                  </Typography>
                </Box>
              </Stack>
            );
          })}
        </Stack>
      </SectionCard>

      <ConfirmDialog
        open={cancelOpen}
        title="Cancel order"
        message={`Cancel order ${order.order_number}? This cannot be undone.`}
        confirmLabel="Cancel Order"
        tone="error"
        loading={statusMutation.isPending}
        onConfirm={handleCancel}
        onCancel={() => setCancelOpen(false)}
      />

      <EditOrderDialog
        open={editOpen}
        order={order}
        onClose={() => setEditOpen(false)}
        submit={(payload) => updateMutation.mutateAsync(payload)}
      />
      <AssignWorkDialog
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        onCreated={() => setAssignOpen(false)}
        defaultOrderId={orderId}
      />
      <ReportProgressDialog
        open={progressOpen}
        assignment={selectedAssignment}
        onClose={() => setProgressOpen(false)}
        submit={async (completedQuantity) => {
          if (!selectedAssignment) return;
          await assignmentProgressMutation.mutateAsync({
            id: selectedAssignment.id,
            completedQuantity,
          });
        }}
      />
    </Box>
  );
};

export default OrderDetail;
