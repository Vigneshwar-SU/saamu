import { useCallback, useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { communicationsService } from '../services/communicationsService';
import { copyToClipboard } from '../utils/clipboard';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { PreparedMessage } from '../types/communications';

export const COMMUNICATION_KEY = 'communication';

/**
 * Reusable communication hook for an order.
 *
 * Prepares the single server-authored WhatsApp-ready message for the order
 * (message type and wording are derived from order status + payment balance,
 * never chosen by staff), exposes copy/open actions with duplicate-action
 * protection, and keeps errors recoverable (retry, or the copy flow can be
 * tried again).
 */
export const useOrderCommunication = (orderId: number) => {
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isOpening, setIsOpening] = useState(false);
  const copiedTimer = useRef<number | null>(null);
  const openTimer = useRef<number | null>(null);

  const enabled = orderId > 0;

  const { data, isLoading, isError, error, refetch } = useQuery<PreparedMessage>({
    queryKey: [COMMUNICATION_KEY, orderId],
    queryFn: () => communicationsService.prepareOrderMessage(orderId),
    enabled,
  });

  useEffect(() => {
    return () => {
      if (copiedTimer.current !== null) window.clearTimeout(copiedTimer.current);
      if (openTimer.current !== null) window.clearTimeout(openTimer.current);
    };
  }, []);

  const copy = useCallback(async () => {
    if (!data) return;
    setActionError(null);
    try {
      await copyToClipboard(data.message);
      setCopied(true);
      if (copiedTimer.current !== null) window.clearTimeout(copiedTimer.current);
      copiedTimer.current = window.setTimeout(() => setCopied(false), 2000);
    } catch (copyError) {
      setActionError(getApiErrorMessage(copyError));
    }
  }, [data]);

  const open = useCallback(() => {
    if (!data?.whatsapp_url || isOpening) return;
    setActionError(null);
    setIsOpening(true);
    const finish = () => {
      setIsOpening(false);
      window.removeEventListener('blur', finish);
    };
    window.open(data.whatsapp_url, '_blank', 'noopener,noreferrer');
    window.addEventListener('blur', finish);
    if (openTimer.current !== null) window.clearTimeout(openTimer.current);
    openTimer.current = window.setTimeout(finish, 1500);
  }, [data, isOpening]);

  const isBusy = isLoading || isOpening;

  return {
    data,
    isLoading,
    isError,
    queryError: error,
    errorMessage: actionError,
    copied,
    isOpening,
    isBusy,
    copy,
    open,
    retry: refetch,
  };
};
