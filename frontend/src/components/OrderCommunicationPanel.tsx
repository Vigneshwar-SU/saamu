import React from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import ChatIcon from '@mui/icons-material/Chat';
import { useOrderCommunication } from '../hooks/useCommunications';
import { getApiErrorMessage } from '../utils/apiErrors';
import {
  ORDER_MESSAGE_TYPES,
  ORDER_MESSAGE_TYPE_LABELS,
} from '../types/communications';
import type { OrderMessageType } from '../types/communications';

export const OrderCommunicationPanel: React.FC<{ orderId: number }> = ({
  orderId,
}) => {
  const {
    messageType,
    selectType,
    data,
    isLoading,
    isError,
    queryError,
    errorMessage,
    copied,
    isBusy,
    copy,
    open,
    retry,
  } = useOrderCommunication(orderId);

  return (
    <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E7E0D0' }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: '10px',
            backgroundColor: '#F5EBD2',
            color: '#7A5E0C',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ChatIcon fontSize="small" />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Customer Communication
          </Typography>
          <Typography variant="caption" sx={{ color: '#6B6B6B' }}>
            Prepare a WhatsApp-ready message. Nothing is sent automatically.
          </Typography>
        </Box>
      </Stack>

      <Stack spacing={2}>
        <FormControl size="small" sx={{ minWidth: 260, alignSelf: 'flex-start' }}>
          <InputLabel id="order-message-type-label">Message Type</InputLabel>
          <Select
            labelId="order-message-type-label"
            label="Message Type"
            value={messageType}
            onChange={(event) =>
              selectType(event.target.value as OrderMessageType)
            }
          >
            {ORDER_MESSAGE_TYPES.map((type) => (
              <MenuItem key={type} value={type}>
                {ORDER_MESSAGE_TYPE_LABELS[type]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={26} />
          </Box>
        )}

        {isError && !isLoading && (
          <Stack direction="row" spacing={1} alignItems="center">
            <Alert severity="error" sx={{ flex: 1 }}>
              {getApiErrorMessage(queryError)}
            </Alert>
            <Button variant="outlined" size="small" onClick={() => retry()}>
              Retry
            </Button>
          </Stack>
        )}

        {data && !isLoading && (
          <>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                borderRadius: '10px',
                backgroundColor: '#FBF6EA',
                maxHeight: 260,
                overflow: 'auto',
              }}
            >
              <Typography
                component="pre"
                sx={{
                  m: 0,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'inherit',
                  fontSize: '0.875rem',
                  color: '#242424',
                }}
              >
                {data.message}
              </Typography>
            </Paper>

            {!data.phone_number && (
              <Typography variant="body2" sx={{ color: '#8F4A00' }}>
                No usable WhatsApp number is recorded for this customer, so Open
                WhatsApp is disabled. The message can still be copied.
              </Typography>
            )}

            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}

            <Stack direction="row" spacing={1.5} flexWrap="wrap">
              <Button
                variant="outlined"
                startIcon={copied ? <CheckIcon /> : <ContentCopyIcon />}
                disabled={isBusy}
                onClick={copy}
                sx={
                  copied
                    ? { color: '#1F5C3C', borderColor: '#86EFAC' }
                    : undefined
                }
              >
                {copied ? 'Copied' : 'Copy WhatsApp Message'}
              </Button>
              <Button
                variant="contained"
                startIcon={<ChatIcon />}
                disabled={!data.whatsapp_url || isBusy}
                onClick={open}
              >
                Open WhatsApp
              </Button>
            </Stack>
          </>
        )}
      </Stack>
    </Paper>
  );
};
