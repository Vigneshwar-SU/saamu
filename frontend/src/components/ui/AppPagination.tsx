import React from 'react';
import { Box, Pagination, Typography } from '@mui/material';

interface AppPaginationProps {
  page: number;
  count: number;
  pageSize: number;
  onChange: (page: number) => void;
}

export const AppPagination: React.FC<AppPaginationProps> = ({
  page,
  count,
  pageSize,
  onChange,
}) => {
  if (count === 0) return null;

  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, count);

  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: { xs: 'center', sm: 'space-between' },
        alignItems: 'center',
        gap: 1.5,
      }}
    >
      <Typography
        variant="body2"
        sx={{ color: 'text.secondary', textAlign: { xs: 'center', sm: 'left' } }}
      >
        Showing {start}–{end} of {count}
      </Typography>
      <Pagination
        count={totalPages}
        page={Math.min(page, totalPages)}
        onChange={(_event, value) => onChange(value)}
        color="primary"
        size="small"
        siblingCount={0}
      />
    </Box>
  );
};

export default AppPagination;
