import React from 'react';
import {
  Box,
  Breadcrumbs,
  Button,
  Link,
  Stack,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom';

export interface Crumb {
  label: string;
  to?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  crumbs?: Crumb[];
  backTo?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon,
  actions,
  crumbs,
  backTo,
}) => {
  const navigate = useNavigate();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {(crumbs && crumbs.length > 0) && (
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          {crumbs.map((crumb, index) =>
            crumb.to && index < crumbs.length - 1 ? (
              <Link
                key={crumb.label}
                underline="hover"
                color="inherit"
                href={crumb.to}
                onClick={(event) => {
                  event.preventDefault();
                  navigate(crumb.to!);
                }}
                sx={{ fontSize: '0.85rem' }}
              >
                {crumb.label}
              </Link>
            ) : (
              <Typography key={crumb.label} color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                {crumb.label}
              </Typography>
            )
          )}
        </Breadcrumbs>
      )}

      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ minWidth: 0 }}>
          {backTo && (
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(backTo)}
              aria-label="Go back"
              sx={{ minWidth: 0, px: 1.5 }}
            >
              Back
            </Button>
          )}
          {icon && (
            <Box
              sx={{
                width: 52,
                height: 52,
                flexShrink: 0,
                borderRadius: '14px',
                backgroundColor: '#F5EBD2',
                color: '#A98216',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          )}
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.25 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        </Stack>

        {actions && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'center' }}>
            {actions}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PageHeader;
