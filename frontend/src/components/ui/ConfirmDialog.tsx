import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';

type ConfirmTone = 'primary' | 'error' | 'warning';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmTone;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  tone = 'primary',
  loading = false,
  onConfirm,
  onCancel,
}) => {
  const confirmColor = tone === 'error' ? 'error' : tone === 'warning' ? 'warning' : 'primary';

  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="xs" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions
        sx={{ px: 3, py: 2, flexDirection: { xs: 'column-reverse', sm: 'row' }, gap: 1 }}
      >
        <Button
          onClick={onConfirm}
          disabled={loading}
          variant="contained"
          color={confirmColor}
          fullWidth
        >
          {confirmLabel}
        </Button>
        <Button onClick={onCancel} disabled={loading} variant="outlined" fullWidth>
          {cancelLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
