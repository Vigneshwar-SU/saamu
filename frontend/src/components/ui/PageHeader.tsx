import React from 'react';
import { Box, Breadcrumbs, Button, Link, Stack, Typography } from '@mui/material';
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
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 1.5, sm: 2 } }}>
      {crumbs && crumbs.length > 0 && (
        <Breadcrumbs
          separator={<NavigateNextIcon fontSize="small" />}
          aria-label="breadcrumb"
          sx={{ flexWrap: 'wrap' }}
        >
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
              <Typography
                key={crumb.label}
                color="text.primary"
                sx={{ fontSize: '0.85rem', fontWeight: 600 }}
              >
                {crumb.label}
              </Typography>
            )
          )}
        </Breadcrumbs>
      )}

      {backTo && (
        <Box>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(backTo)}
            aria-label="Go back"
            sx={{ minWidth: 0, px: 1.5 }}
          >
            Back
          </Button>
        </Box>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'center' },
          justifyContent: { sm: 'space-between' },
          gap: { xs: 1.5, sm: 2 },
        }}
      >
        <Stack
          direction="row"
          spacing={{ xs: 1.5, sm: 2 }}
          alignItems="center"
          sx={{ minWidth: 0 }}
        >
          {icon && (
            <Box
              sx={{
                width: { xs: 40, sm: 52 },
                height: { xs: 40, sm: 52 },
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
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                lineHeight: 1.2,
                fontSize: { xs: '1.375rem', sm: '2.125rem' },
              }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  mt: 0.25,
                  fontSize: { xs: '0.8rem', sm: '0.875rem' },
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
        </Stack>

        {actions && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
            {actions}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PageHeader;
