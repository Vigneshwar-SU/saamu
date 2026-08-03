import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
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
  Tooltip,
  Typography,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import EditIcon from '@mui/icons-material/Edit';
import CancelIcon from '@mui/icons-material/Cancel';
import StraightenIcon from '@mui/icons-material/Straighten';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PaymentsIcon from '@mui/icons-material/Payments';
import InventoryIcon from '@mui/icons-material/Inventory';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HistoryIcon from '@mui/icons-material/History';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useChangeOrderStatus, useOrder, useUpdateOrder } from '../hooks/useOrders';
import { useCreateOrderInvoice, useInvoiceList } from '../hooks/useInvoices';
import { MEASUREMENT_FIELD_LABELS } from '../types/customers';
import type { MeasurementFieldName } from '../types/customers';
import {
  NEXT_STATUS,
  ORDER_STATUS_COLORS,
  ORDER_STATUS_LABELS,
  TERMINAL_ORDER_STATUSES,
} from '../types/orders';
import type { Order, OrderItem, OrderStatus, OrderUpdatePayload } from '../types/orders';
import { INVOICE_STATUS_COLORS, INVOICE_STATUS_LABELS } from '../types/billing';

const InfoCell: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
}> = ({ icon, label, value }) => (
  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
    <Box
      sx={{
        width: 36,
        height: 36,
        borderRadius: '10px',
        backgroundColor: '#F1F5F9',
        color: '#475569',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      {icon}
    </Box>
    <Box>
      <Typography
        variant="caption"
        sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}
      >
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 500, color: '#0F172A', whiteSpace: 'pre-wrap' }}>
        {value}
      </Typography>
    </Box>
  </Box>
);

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
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
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
  const fields = snapshot
    ? (Object.entries(snapshot) as Array<[string, number | null]>)
    : [];

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
        <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
          <TableCell colSpan={7} sx={{ pb: 2 }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
                gap: 2,
              }}
            >
              {fields.map(([field, value]) => (
                <Box key={field}>
                  <Typography
                    variant="caption"
                    sx={{ color: '#94A3B8', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}
                  >
                    {MEASUREMENT_FIELD_LABELS[field as MeasurementFieldName] ?? field}
                  </Typography>
                  <Typography sx={{ fontWeight: 600, color: '#0F172A' }}>
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

  const existingInvoice = orderInvoicesData?.results[0];

  const [editOpen, setEditOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

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

  const statusChip = (orderStatus: OrderStatus) => {
    const colors = ORDER_STATUS_COLORS[orderStatus];
    return (
      <Chip
        label={ORDER_STATUS_LABELS[orderStatus]}
        size="small"
        sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
      />
    );
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
    const confirmed = window.confirm(
      `Cancel order ${order.order_number}? This cannot be undone.`
    );
    if (!confirmed) return;
    setActionError(null);
    try {
      await statusMutation.mutateAsync('CANCELLED');
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
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 8 }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
        <Button color="inherit" onClick={() => navigate('/orders')}>
          Back to Orders
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Link underline="hover" color="inherit" href="/orders" sx={{ fontSize: '0.85rem' }}>
          Orders
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          {order.order_number}
        </Typography>
      </Breadcrumbs>

      {actionError && <Alert severity="error">{actionError}</Alert>}
      {statusMutation.isPending && (
        <Alert severity="info" icon={<CircularProgress size={16} />}>
          Updating order status...
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Tooltip title="Back to orders">
            <IconButton
              onClick={() => navigate('/orders')}
              sx={{ border: '1px solid #E2E8F0', borderRadius: '10px', color: '#475569' }}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {order.order_number}
              </Typography>
              {statusChip(order.status)}
            </Stack>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              {order.customer.full_name} · {order.customer.mobile_number}
            </Typography>
          </Box>
        </Stack>

        {isStaff && !isTerminal && (
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
              Edit
            </Button>
            {nextStatus && (
              <Button
                variant="contained"
                startIcon={nextStatus === 'COLLECTED' ? <CheckCircleIcon /> : undefined}
                onClick={handleAdvance}
                sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
              >
                Move to {ORDER_STATUS_LABELS[nextStatus]}
              </Button>
            )}
            <Button variant="outlined" color="error" startIcon={<CancelIcon />} onClick={handleCancel}>
              Cancel
            </Button>
          </Stack>
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
      </Box>

      <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2.5 }}>
          Order Summary
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 3,
          }}
        >
          <InfoCell
            icon={<CalendarTodayIcon sx={{ fontSize: 18 }} />}
            label="Order Date"
            value={formatDate(order.order_date)}
          />
          <InfoCell
            icon={<CalendarTodayIcon sx={{ fontSize: 18 }} />}
            label="Expected Delivery"
            value={order.expected_delivery_date ? formatDate(order.expected_delivery_date) : '-'}
          />
          <InfoCell
            icon={<ReceiptLongIcon sx={{ fontSize: 18 }} />}
            label="Total Amount"
            value={formatCurrency(Number(order.total_amount))}
          />
          <InfoCell
            icon={<InventoryIcon sx={{ fontSize: 18 }} />}
            label="Collected At"
            value={order.collected_at ? formatDate(order.collected_at, 'DD MMM YYYY, hh:mm A') : '-'}
          />
        </Box>
        {order.notes && (
          <Box sx={{ mt: 3 }}>
            <Typography
              variant="caption"
              sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}
            >
              Order Notes
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, color: '#0F172A', whiteSpace: 'pre-wrap' }}>
              {order.notes}
            </Typography>
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Billing
          </Typography>
          {order.payment_summary?.has_invoice && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<ReceiptLongIcon />}
              onClick={() => navigate(`/invoices/${existingInvoice?.id ?? ''}`)}
              disabled={!existingInvoice}
            >
              View Invoice
            </Button>
          )}
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
            gap: 3,
          }}
        >
          <InfoCell
            icon={<ReceiptLongIcon sx={{ fontSize: 18 }} />}
            label="Order Total"
            value={formatCurrency(Number(order.total_amount))}
          />
          <InfoCell
            icon={<PaymentsIcon sx={{ fontSize: 18 }} />}
            label="Total Paid"
            value={formatCurrency(Number(order.payment_summary?.total_paid ?? 0))}
          />
          <InfoCell
            icon={<ReceiptLongIcon sx={{ fontSize: 18 }} />}
            label="Outstanding Balance"
            value={formatCurrency(Number(order.payment_summary?.outstanding_balance ?? order.total_amount))}
          />
          <Box>
            <Typography
              variant="caption"
              sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}
            >
              Payment Status
            </Typography>
            {order.payment_summary?.has_invoice ? (
              <Chip
                size="small"
                label={INVOICE_STATUS_LABELS[order.payment_summary.payment_status]}
                sx={{
                  mt: 0.5,
                  fontWeight: 600,
                  backgroundColor: INVOICE_STATUS_COLORS[order.payment_summary.payment_status].bg,
                  color: INVOICE_STATUS_COLORS[order.payment_summary.payment_status].text,
                }}
              />
            ) : (
              <Typography sx={{ fontWeight: 600, mt: 0.5, color: '#64748B' }}>
                No invoice yet
              </Typography>
            )}
          </Box>
        </Box>
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ px: 3, py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Stack direction="row" spacing={1} alignItems="center">
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
              <StraightenIcon fontSize="small" />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Order Items
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Measurements snapshot at the time of ordering
              </Typography>
            </Box>
          </Stack>
        </Box>
        <Divider />
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
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
                    <TableCell align="right">{formatCurrency(Number(item.unit_price))}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      {formatCurrency(Number(item.line_total))}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ color: '#475569' }}>
                        {item.notes || '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <MeasurementSnapshotRow item={item} />
                </React.Fragment>
              ))}
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell colSpan={4} sx={{ fontWeight: 700 }}>
                  Total Amount
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, color: '#1E3A8A' }}>
                  {formatCurrency(Number(order.total_amount))}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2.5 }}>
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
            <HistoryIcon fontSize="small" />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Status History
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Every status change is recorded with the staff member who made it
            </Typography>
          </Box>
        </Stack>
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
                    <Box sx={{ width: 2, height: '100%', backgroundColor: '#E2E8F0' }} />
                  )}
                </Stack>
                <Box sx={{ flex: 1 }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography sx={{ fontWeight: 600, color: '#0F172A' }}>
                      {entry.from_status
                        ? `${ORDER_STATUS_LABELS[entry.from_status]} → ${ORDER_STATUS_LABELS[entry.to_status]}`
                        : `Order placed · ${ORDER_STATUS_LABELS[entry.to_status]}`}
                    </Typography>
                  </Stack>
                  <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                    {entry.changed_by_username ?? 'System'} · {formatDate(entry.changed_at, 'DD MMM YYYY, hh:mm A')}
                  </Typography>
                </Box>
              </Stack>
            );
          })}
        </Stack>
      </Paper>

      <EditOrderDialog
        open={editOpen}
        order={order}
        onClose={() => setEditOpen(false)}
        submit={(payload) => updateMutation.mutateAsync(payload)}
      />
    </Box>
  );
};
