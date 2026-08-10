import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  InputAdornment,
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
  Tooltip,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import AddBoxIcon from '@mui/icons-material/AddBox';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useOrderList } from '../hooks/useOrders';
import { CreateOrderDialog } from '../components/CreateOrderDialog';
import {
  ORDER_STATUS_COLORS,
  ORDER_STATUS_LABELS,
  ORDER_STATUSES,
} from '../types/orders';
import type { OrderStatus } from '../types/orders';
const PAGE_SIZE = 6;

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

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Orders
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
            <ShoppingBagIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Orders
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Track tailoring orders from creation to delivery.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Button
            variant="contained"
            startIcon={<AddBoxIcon />}
            onClick={() => setDialogOpen(true)}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            New Order
          </Button>
        )}
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
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
                  <SearchIcon sx={{ color: '#64748B' }} />
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
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Order</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Customer</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Items</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Total
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Delivery</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
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
                    <Typography sx={{ color: '#64748B' }}>No orders found.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((order) => (
                  <TableRow
                    key={order.id}
                    hover
                    sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                    onClick={() => navigate(`/orders/${order.id}`)}
                  >
                    <TableCell>
                      <Typography sx={{ fontWeight: 600 }}>{order.order_number}</Typography>
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        {formatDate(order.order_date)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {order.customer.full_name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
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
                    <TableCell>{statusChip(order.status)}</TableCell>
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
        </TableContainer>
      </Paper>

      {data && data.count > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Showing {data.results.length} of {data.count} orders
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
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
