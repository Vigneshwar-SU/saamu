import { ReactNode } from 'react';
import type { UserRole } from './api';

export interface NavItem {
  id: string;
  title: string;
  path: string;
  icon: ReactNode;
  badge?: string | number;
  /**
   * Application roles that may see this item. Omit to show the item to every
   * authenticated role (OWNER and STAFF). Role filtering here is UX only;
   * backend authorization remains authoritative.
   */
  roles?: UserRole[];
}
