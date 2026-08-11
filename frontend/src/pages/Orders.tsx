import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import AddBoxIcon from '@mui/icons-material/AddBox';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useOrderList } from '../hooks/useOrders';
import { CreateOrderDialog } from '../components/CreateOrderDialog';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';
import { ORDER_STATUS_LABELS, ORDER_STATUSES } from '../types/orders';
import type { OrderStatus } from '../types/orders';
const PAGE_SIZE = 6;

const ORDER_STATUS_TONES: Record<OrderStatus, StatusTone> = {
  NEW: 'gold',
  CUTTING: 'warning',
  STITCHING: 'info',
  READY: 'success',
  COLLECTED: 'neutral',
  CANCELLED: 'error',
};

export const Orders: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<OrderStatus | ''>('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, status]);

  const { data, isLoading, isError, error, isFetching, refetch } = useOrderList({
    search,
    status,
    page,
  });

  const statusBadge = (orderStatus: OrderStatus) => (
    <StatusBadge
      label={ORDER_STATUS_LABELS[orderStatus]}
      tone={ORDER_STATUS_TONES[orderStatus]}
    />
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Orders"
        subtitle="Track tailoring orders from creation to delivery."
        icon={<ShoppingBagIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Orders' }]}
        actions={
          isStaff && (
            <Button
              variant="contained"
              startIcon={<AddBoxIcon />}
              onClick={() => setDialogOpen(true)}
            >
              New Order
            </Button>
          )
        }
      />

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by order number, customer, or mobile"
            fullWidth
            size="small"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={status}
              label="Status"
              onChange={(event) => setStatus(event.target.value as OrderStatus | '')}
            >
              <MenuItem value="">All</MenuItem>
              {ORDER_STATUSES.map((orderStatus) => (
                <MenuItem key={orderStatus} value={orderStatus}>
                  {ORDER_STATUS_LABELS[orderStatus]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <TableCard loading={isFetching && !isLoading}>
        <Table size="medium">
          <TableHead>
            <TableRow>
              <TableCell>Order</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Items</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Delivery</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableStateRow colSpan={7} state="loading" />
            ) : isError ? (
              <TableStateRow
                colSpan={7}
                state="error"
                errorMessage={getApiErrorMessage(error)}
                onRetry={() => refetch()}
              />
            ) : data && data.results.length === 0 ? (
              <TableStateRow colSpan={7} state="empty" emptyTitle="No orders found" />
            ) : (
              data?.results.map((order) => (
                <TableRow
                  key={order.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/orders/${order.id}`)}
                >
                  <TableCell>
                    <Typography sx={{ fontWeight: 600 }}>{order.order_number}</Typography>
                    <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                      {formatDate(order.order_date)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {order.customer.full_name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                      {order.customer.mobile_number}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {order.garment_summary
                        .map(
                          (summary) =>
                            `${summary.quantity}x ${summary.garment_type.toLowerCase()}`
                        )
                        .join(', ')}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography sx={{ fontWeight: 600 }}>
                      {formatCurrency(Number(order.total_amount))}
                    </Typography>
                  </TableCell>
                  <TableCell>{statusBadge(order.status)}</TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {order.expected_delivery_date
                        ? formatDate(order.expected_delivery_date)
                        : '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View order">
                      <Button
                        size="small"
                        startIcon={<VisibilityIcon fontSize="small" />}
                        onClick={(event) => {
                          event.stopPropagation();
                          navigate(`/orders/${order.id}`);
                        }}
                      >
                        View
                      </Button>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableCard>

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <CreateOrderDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={(order) => {
          setDialogOpen(false);
          navigate(`/orders/${order.id}`);
        }}
      />
    </Box>
  );
};
