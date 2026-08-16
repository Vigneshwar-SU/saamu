import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
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
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
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
    is_active: activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined,
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
      <PageHeader
        title="Salary Configurations"
        subtitle="Choose how each tailor is paid: per garment, fixed salary, or a mix."
        icon={<TuneIcon />}
        crumbs={[
          { label: 'Dashboard', to: '/dashboard' },
          { label: 'Payroll', to: '/payroll' },
          { label: 'Salary Configurations' },
        ]}
        actions={
          isStaff && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingConfig(null);
                setDialogOpen(true);
              }}
            >
              New Configuration
            </Button>
          )
        }
      />

      {actionError && <Alert severity="error">{actionError}</Alert>}

      <FilterBar>
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
      </FilterBar>

      <ResponsiveTable
        data={configurations}
        rowKey={(config) => config.id}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No salary configurations found"
        columns={[
          {
            label: 'Tailor',
            primary: true,
            render: (config) => (
              <Box>
                <Typography sx={{ fontWeight: 600 }}>{config.tailor.name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                  #{config.tailor.id}
                </Typography>
              </Box>
            ),
          },
          {
            label: 'Salary Model',
            render: (config) => (
              <Typography variant="body2">{config.salary_model_display}</Typography>
            ),
          },
          {
            label: 'Fixed Salary',
            render: (config) => (
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {config.salary_model === 'PER_GARMENT'
                  ? '—'
                  : formatCurrency(config.fixed_salary_amount)}
              </Typography>
            ),
          },
          {
            label: 'Effective From',
            render: (config) => (
              <Typography variant="body2">{formatDate(config.effective_from)}</Typography>
            ),
          },
          {
            label: 'Effective To',
            render: (config) => (
              <Typography variant="body2">
                {config.effective_to ? formatDate(config.effective_to) : 'Open-ended'}
              </Typography>
            ),
          },
          {
            label: 'Status',
            render: (config) => (
              <StatusBadge
                label={config.is_active ? 'Active' : 'Inactive'}
                tone={config.is_active ? 'success' : 'neutral'}
              />
            ),
          },
          {
            label: 'Created By',
            render: (config) => (
              <Typography variant="body2">{config.created_by_name || '-'}</Typography>
            ),
          },
        ]}
        actions={
          isStaff
            ? (config) => (
                <Stack direction="row" spacing={0.5} flexWrap="wrap">
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
              )
            : undefined
        }
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      {isFetching && (
        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
          Refreshing…
        </Typography>
      )}

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
