import React from 'react';
import { Box, Card, CardContent, Typography, Breadcrumbs, Link, Chip, Stack } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ConstructionIcon from '@mui/icons-material/Construction';
import PaymentIcon from '@mui/icons-material/Payment';
import BarChartIcon from '@mui/icons-material/BarChart';
import SettingsIcon from '@mui/icons-material/Settings';

interface PlaceholderProps {
  title: string;
  description: string;
  icon: React.ReactNode;
}

const GenericPlaceholder: React.FC<PlaceholderProps> = ({ title, description, icon }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Breadcrumb Navigation */}
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          {title}
        </Typography>
      </Breadcrumbs>

      {/* Header Title */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
            {icon}
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {title}
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              {description}
            </Typography>
          </Box>
        </Box>
        <Chip
          label="Sprint Foundation"
          size="small"
          color="primary"
          variant="outlined"
          sx={{ fontWeight: 600 }}
        />
      </Box>

      {/* Main Content Card */}
      <Card sx={{ p: 4, textAlign: 'center', backgroundColor: '#FFFFFF' }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 6 }}>
          <Box
            sx={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              backgroundColor: '#FEF3C7',
              color: '#D97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 3,
            }}
          >
            <ConstructionIcon sx={{ fontSize: 36 }} />
          </Box>

          <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, color: '#0F172A' }}>
            {title} Module - Coming Soon
          </Typography>

          <Typography
            variant="body1"
            sx={{ color: '#64748B', maxWidth: 480, mx: 'auto', mb: 3, lineHeight: 1.6 }}
          >
            This module is reserved for upcoming tailoring business features. The current sprint focuses strictly on establishing a solid, scalable React + Django + PostgreSQL enterprise foundation.
          </Typography>

          <Stack direction="row" spacing={1} justifyContent="center">
            <Chip label="Architecture Ready" size="small" sx={{ backgroundColor: '#F1F5F9', color: '#475569' }} />
            <Chip label="PostgreSQL Models Schema Ready" size="small" sx={{ backgroundColor: '#F1F5F9', color: '#475569' }} />
            <Chip label="REST API Route Configured" size="small" sx={{ backgroundColor: '#F1F5F9', color: '#475569' }} />
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};

export const Payments: React.FC = () => (
  <GenericPlaceholder
    title="Payments"
    description="Track cash, UPI, card, and bank transfers across all operations."
    icon={<PaymentIcon fontSize="large" />}
  />
);

export const Reports: React.FC = () => (
  <GenericPlaceholder
    title="Reports"
    description="Financial summary statements, tailor productivity, and monthly growth analytics."
    icon={<BarChartIcon fontSize="large" />}
  />
);

export const Settings: React.FC = () => (
  <GenericPlaceholder
    title="Settings"
    description="System configuration, user permissions, shop details, and print options."
    icon={<SettingsIcon fontSize="large" />}
  />
);
