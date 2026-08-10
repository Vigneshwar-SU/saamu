import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
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
  Tooltip,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import TuneIcon from '@mui/icons-material/Tune';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useAuth } from '../context/useAuth';
import { useTailorList } from '../hooks/useTailors';
import {
  useCreateSalaryConfiguration,
  useSalaryConfigurationList,
  useUpdateSalaryConfiguration,
} from '../hooks/useSalaryConfigurations';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { SalaryConfigurationDialog } from '../components/SalaryConfigurationDialog';
import { SALARY_MODEL_LABELS, SALARY_MODELS } from '../types/payroll';
import type {
  SalaryConfigurationPayload,
  SalaryModel,
  TailorSalaryConfiguration,
} from '../types/payroll';

const PAGE_SIZE = 6;

export const SalaryConfigurations: React.FC = () => {
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<TailorSalaryConfiguration | null>(null);
  const [tailorFilter, setTailorFilter] = useState<number>(0);
  const [modelFilter, setModelFilter] = useState<SalaryModel | ''>('');
  const [activeFilter, setActiveFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: tailorsData } = useTailorList({ scope: 'all', page_size: 100 });
  const { data, isLoading, isError, error, refetch, isFetching } = useSalaryConfigurationList({
    page: page > 1 ? page : undefined,
    tailor: tailorFilter || undefined,
    salary_model: modelFilter || undefined,
    is_active:
      activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  useEffect(() => {
    if (data && page > totalPages) {
      setPage(1);
    }
  }, [data, page, totalPages]);

  const createMutation = useCreateSalaryConfiguration();
  const updateMutation = useUpdateSalaryConfiguration();

  const handleEdit = (config: TailorSalaryConfiguration) => {
    setEditingConfig(config);
    setDialogOpen(true);
  };

  const handleSubmit = async (payload: SalaryConfigurationPayload) => {
    setActionError(null);
    if (editingConfig) {
      await updateMutation.mutateAsync({ id: editingConfig.id, payload });
    } else {
      await createMutation.mutateAsync(payload);
      setPage(1);
    }
  };

  const handleToggleActive = async (config: TailorSalaryConfiguration) => {
    setActionError(null);
    try {
      await updateMutation.mutateAsync({
        id: config.id,
        payload: { is_active: !config.is_active },
      });
    } catch (toggleError) {
      setActionError(getApiErrorMessage(toggleError));
    }
  };

  const tailors = tailorsData?.results ?? [];
  const configurations = data?.results ?? [];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Link underline="hover" color="inherit" href="/payroll" sx={{ fontSize: '0.85rem' }}>
          Payroll
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Salary Configurations
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
            <TuneIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Salary Configurations
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Choose how each tailor is paid: per garment, fixed salary, or a mix.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingConfig(null);
              setDialogOpen(true);
            }}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            New Configuration
          </Button>
        )}
      </Box>

      {actionError && <Alert severity="error">{actionError}</Alert>}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel>Tailor</InputLabel>
          <Select
            label="Tailor"
            value={tailorFilter}
            onChange={(event) => {
              setTailorFilter(event.target.value as number);
              setPage(1);
            }}
          >
            <MenuItem value={0}>All Tailors</MenuItem>
            {tailors.map((tailor) => (
              <MenuItem key={tailor.id} value={tailor.id}>
                {tailor.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Salary Model</InputLabel>
          <Select
            label="Salary Model"
            value={modelFilter}
            onChange={(event) => {
              setModelFilter(event.target.value as SalaryModel | '');
              setPage(1);
            }}
          >
            <MenuItem value="">All Models</MenuItem>
            {SALARY_MODELS.map((model) => (
              <MenuItem key={model} value={model}>
                {SALARY_MODEL_LABELS[model]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={activeFilter}
            onChange={(event) => {
              setActiveFilter(event.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="true">Active</MenuItem>
            <MenuItem value="false">Inactive</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Tailor</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Salary Model</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Fixed Salary</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Effective From</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Effective To</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Created By</TableCell>
                {isStaff && (
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    Actions
                  </TableCell>
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={isStaff ? 8 : 7} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={isStaff ? 8 : 7} align="center" sx={{ py: 4 }}>
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
              ) : configurations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={isStaff ? 8 : 7} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>
                      No salary configurations found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                configurations.map((config) => (
                  <TableRow
                    key={config.id}
                    hover
                    sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  >
                    <TableCell>
                      <Typography sx={{ fontWeight: 600 }}>{config.tailor.name}</Typography>
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        #{config.tailor.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{config.salary_model_display}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {config.salary_model === 'PER_GARMENT'
                          ? '—'
                          : formatCurrency(config.fixed_salary_amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{formatDate(config.effective_from)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {config.effective_to ? formatDate(config.effective_to) : 'Open-ended'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={config.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        sx={{
                          fontWeight: 600,
                          backgroundColor: config.is_active ? '#DCFCE7' : '#F1F5F9',
                          color: config.is_active ? '#15803D' : '#475569',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{config.created_by_name || '-'}</Typography>
                    </TableCell>
                    {isStaff && (
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Edit configuration">
                            <Button
                              size="small"
                              startIcon={<EditIcon fontSize="small" />}
                              onClick={() => handleEdit(config)}
                            >
                              Edit
                            </Button>
                          </Tooltip>
                          <Tooltip title={config.is_active ? 'Deactivate' : 'Activate'}>
                            <Button
                              size="small"
                              startIcon={
                                config.is_active ? (
                                  <BlockIcon fontSize="small" color="error" />
                                ) : (
                                  <CheckCircleIcon fontSize="small" color="success" />
                                )
                              }
                              onClick={() => handleToggleActive(config)}
                            >
                              {config.is_active ? 'Deactivate' : 'Activate'}
                            </Button>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    )}
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
            Showing {data.results.length} of {data.count} configurations
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      {isFetching && <Typography variant="caption" sx={{ color: '#94A3B8' }}>Refreshing…</Typography>}

      <SalaryConfigurationDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleSubmit}
        config={editingConfig}
      />
    </Box>
  );
};

export default SalaryConfigurations;
