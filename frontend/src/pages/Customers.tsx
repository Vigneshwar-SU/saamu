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
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import PeopleIcon from '@mui/icons-material/People';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { CustomerFormDialog } from '../components/CustomerFormDialog';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import {
  useArchiveCustomer,
  useCreateCustomer,
  useCustomerList,
  useRestoreCustomer,
  useUpdateCustomer,
} from '../hooks/useCustomers';
import type { Customer, CustomerPayload, CustomerStatus } from '../types/customers';

const PAGE_SIZE = 6;

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
  const [archiveTarget, setArchiveTarget] = useState<Customer | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, status]);

  const { data, isLoading, isError, error, isFetching, refetch } = useCustomerList({
    search,
    status,
    page,
  });

  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer(editingCustomer?.id ?? 0);
  const archiveMutation = useArchiveCustomer();
  const restoreMutation = useRestoreCustomer();

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

  const confirmArchive = async () => {
    if (!archiveTarget) return;
    try {
      await archiveMutation.mutateAsync(archiveTarget.id);
    } catch (archiveError) {
      window.alert(getApiErrorMessage(archiveError));
    }
    setArchiveTarget(null);
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
      <PageHeader
        title="Customers"
        subtitle="Manage customer profiles, measurement charts, and fitting history."
        icon={<PeopleIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Customers' }]}
        actions={
          isStaff && (
            <Button variant="contained" startIcon={<PersonAddAltIcon />} onClick={openCreateDialog}>
              Add Customer
            </Button>
          )
        }
      />

      <FilterBar>
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
              onChange={(event) => setStatus(event.target.value as CustomerStatus)}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="archived">Archived</MenuItem>
              <MenuItem value="all">All</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(customer) => customer.id}
        onRowClick={(customer) => navigate(`/customers/${customer.id}`)}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle={search ? 'No matching customers' : 'No customers yet'}
        emptyMessage={
          search
            ? 'Try a different search or filter.'
            : 'Add your first customer to start recording orders.'
        }
        emptyAction={
          isStaff ? (
            <Button variant="contained" startIcon={<PersonAddAltIcon />} onClick={openCreateDialog}>
              Add Customer
            </Button>
          ) : undefined
        }
        columns={[
          {
            label: 'Customer',
            primary: true,
            render: (customer) => (
              <Box>
                <Typography sx={{ fontWeight: 600 }}>{customer.full_name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                  #{customer.id}
                </Typography>
              </Box>
            ),
          },
          {
            label: 'Mobile',
            render: (customer) => (
              <Box>
                <Typography variant="body2">{customer.mobile_number}</Typography>
                {customer.alternate_mobile_number && (
                  <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                    {customer.alternate_mobile_number}
                  </Typography>
                )}
              </Box>
            ),
          },
          {
            label: 'Address',
            hideOnMobile: true,
            render: (customer) => (
              <Typography
                variant="body2"
                sx={{
                  maxWidth: 240,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {customer.address || '-'}
              </Typography>
            ),
          },
          {
            label: 'Status',
            render: (customer) => (
              <StatusBadge
                label={customer.is_active ? 'Active' : 'Archived'}
                tone={customer.is_active ? 'success' : 'neutral'}
              />
            ),
          },
          {
            label: 'Created',
            render: (customer) => (
              <Typography variant="body2">{formatDate(customer.created_at)}</Typography>
            ),
          },
        ]}
        actions={(customer) => (
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
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
                    setArchiveTarget(customer);
                  }}
                >
                  Archive
                </Button>
              </Tooltip>
            )}
          </Stack>
        )}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <ConfirmDialog
        open={archiveTarget !== null}
        title="Archive customer"
        message={
          archiveTarget
            ? `Archive customer "${archiveTarget.full_name}"? The profile is kept and can be restored later.`
            : ''
        }
        confirmLabel="Archive"
        tone="warning"
        loading={archiveMutation.isPending}
        onConfirm={confirmArchive}
        onCancel={() => setArchiveTarget(null)}
      />

      <CustomerFormDialog
        open={dialogOpen}
        initial={editingCustomer}
        onClose={closeDialog}
        submit={handleSubmit}
      />
    </Box>
  );
};

export default Customers;
