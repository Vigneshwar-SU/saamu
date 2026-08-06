import { useCallback, useEffect, useRef, useState } from 'react';
import { remindersService } from '../services/remindersService';
import { copyToClipboard } from '../utils/clipboard';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { ReminderCandidate } from '../types/reminders';

/**
 * Copy / open actions for one reminder candidate, with duplicate-action
 * protection and recoverable error handling.
 *
 * Opening WhatsApp re-fetches the prepared reminder so the destination and
 * message are re-validated against current order/payment state at handoff
 * time (a stale reminder yields a clear backend error instead of being sent).
 */
export const useReminderActions = (candidate: ReminderCandidate) => {
  const [copied, setCopied] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timers = useRef<Array<number | null>>([]);

  useEffect(() => {
    const current = timers.current;
    return () => {
      current.forEach((timer) => {
        if (timer !== null) window.clearTimeout(timer);
      });
    };
  }, []);

  const copy = useCallback(async () => {
    setError(null);
    try {
      await copyToClipboard(candidate.message);
      setCopied(true);
      timers.current.forEach((timer) => {
        if (timer !== null) window.clearTimeout(timer);
      });
      timers.current = [window.setTimeout(() => setCopied(false), 2000)];
    } catch (copyError) {
      setError(getApiErrorMessage(copyError));
    }
  }, [candidate.message]);

  const open = useCallback(async () => {
    if (isOpening) return;
    setError(null);
    setIsOpening(true);
    const finish = () => {
      setIsOpening(false);
      window.removeEventListener('blur', finish);
    };
    try {
      const prepared = await remindersService.prepareReminder(candidate.id);
      if (!prepared.whatsapp_url) {
        setError('No usable WhatsApp number is recorded for this customer.');
        setIsOpening(false);
        return;
      }
      window.open(prepared.whatsapp_url, '_blank', 'noopener,noreferrer');
      window.addEventListener('blur', finish);
      timers.current.forEach((timer) => {
        if (timer !== null) window.clearTimeout(timer);
      });
      timers.current = [window.setTimeout(finish, 1500)];
    } catch (openError) {
      setError(getApiErrorMessage(openError));
      setIsOpening(false);
    }
  }, [candidate.id, isOpening]);

  return { copied, isOpening, error, copy, open };
};
