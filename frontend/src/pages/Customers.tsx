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
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import PeopleIcon from '@mui/icons-material/People';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { CustomerFormDialog } from '../components/CustomerFormDialog';
import {
  useArchiveCustomer,
  useCreateCustomer,
  useCustomerList,
  useRestoreCustomer,
  useUpdateCustomer,
} from '../hooks/useCustomers';
import type {
  Customer,
  CustomerPayload,
  CustomerStatus,
} from '../types/customers';

const PAGE_SIZE = 20;

export const Customers: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<CustomerStatus>('active');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, status]);

  const {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    refetch,
  } = useCustomerList({ search, status, page });

  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer(editingCustomer?.id ?? 0);
  const archiveMutation = useArchiveCustomer();
  const restoreMutation = useRestoreCustomer();

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  const openCreateDialog = () => {
    setEditingCustomer(null);
    setDialogOpen(true);
  };

  const openEditDialog = (customer: Customer) => {
    setEditingCustomer(customer);
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingCustomer(null);
  };

  const handleSubmit = (payload: CustomerPayload) => {
    if (editingCustomer) {
      return updateMutation.mutateAsync(payload);
    }
    return createMutation.mutateAsync(payload);
  };

  const handleArchive = async (customer: Customer) => {
    const confirmed = window.confirm(
      `Archive customer "${customer.full_name}"? The profile is kept and can be restored later.`
    );
    if (!confirmed) return;
    try {
      await archiveMutation.mutateAsync(customer.id);
    } catch (archiveError) {
      window.alert(getApiErrorMessage(archiveError));
    }
  };

  const handleRestore = async (customer: Customer) => {
    try {
      await restoreMutation.mutateAsync(customer.id);
    } catch (restoreError) {
      window.alert(getApiErrorMessage(restoreError));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Customers
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
            <PeopleIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Customers
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Manage customer profiles, measurement charts, and fitting history.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Button
            variant="contained"
            startIcon={<PersonAddAltIcon />}
            onClick={openCreateDialog}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            Add Customer
          </Button>
        )}
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by name, mobile, or ID"
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
              onChange={(event) => setStatus(event.target.value as CustomerStatus)}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="archived">Archived</MenuItem>
              <MenuItem value="all">All</MenuItem>
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
                <TableCell sx={{ fontWeight: 700 }}>Customer</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Mobile</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Address</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Created</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
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
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>No customers found.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((customer) => (
                  <TableRow
                    key={customer.id}
                    hover
                    sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                    onClick={() => navigate(`/customers/${customer.id}`)}
                  >
                    <TableCell>
                      <Typography sx={{ fontWeight: 600 }}>{customer.full_name}</Typography>
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        #{customer.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{customer.mobile_number}</Typography>
                      {customer.alternate_mobile_number && (
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                          {customer.alternate_mobile_number}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {customer.address || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={customer.is_active ? 'Active' : 'Archived'}
                        size="small"
                        sx={{
                          fontWeight: 600,
                          backgroundColor: customer.is_active ? '#DCFCE7' : '#F1F5F9',
                          color: customer.is_active ? '#15803D' : '#64748B',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{formatDate(customer.created_at)}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        <Tooltip title="View details">
                          <Button
                            size="small"
                            startIcon={<VisibilityIcon fontSize="small" />}
                            onClick={(event) => {
                              event.stopPropagation();
                              navigate(`/customers/${customer.id}`);
                            }}
                          >
                            View
                          </Button>
                        </Tooltip>
                        {isStaff && (
                          <Tooltip title={customer.is_active ? 'Edit customer' : 'Restore customer'}>
                            <Button
                              size="small"
                              startIcon={
                                customer.is_active ? (
                                  <EditIcon fontSize="small" />
                                ) : (
                                  <UnarchiveIcon fontSize="small" />
                                )
                              }
                              onClick={(event) => {
                                event.stopPropagation();
                                if (customer.is_active) {
                                  openEditDialog(customer);
                                } else {
                                  handleRestore(customer);
                                }
                              }}
                            >
                              {customer.is_active ? 'Edit' : 'Restore'}
                            </Button>
                          </Tooltip>
                        )}
                        {isStaff && customer.is_active && (
                          <Tooltip title="Archive customer">
                            <Button
                              size="small"
                              color="error"
                              startIcon={<ArchiveIcon fontSize="small" />}
                              onClick={(event) => {
                                event.stopPropagation();
                                handleArchive(customer);
                              }}
                            >
                              Archive
                            </Button>
                          </Tooltip>
                        )}
                      </Stack>
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
            Showing {data.results.length} of {data.count} customers
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      <CustomerFormDialog
        open={dialogOpen}
        initial={editingCustomer}
        onClose={closeDialog}
        submit={handleSubmit}
      />
    </Box>
  );
};
