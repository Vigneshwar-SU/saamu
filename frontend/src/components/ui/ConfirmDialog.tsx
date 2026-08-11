import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Stack,
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
  const confirmColor =
    tone === 'error' ? 'error' : tone === 'warning' ? 'warning' : 'primary';

  return (
    <Dialog open={open} onClose={loading ? undefined : onCancel} maxWidth="xs" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Stack direction="row" spacing={1.5}>
          <Button onClick={onCancel} disabled={loading} variant="outlined">
            {cancelLabel}
          </Button>
          <Button
            onClick={onConfirm}
            disabled={loading}
            variant="contained"
            color={confirmColor}
          >
            {confirmLabel}
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
