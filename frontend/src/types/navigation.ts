import { ReactNode } from 'react';

export interface NavItem {
  id: string;
  title: string;
  path: string;
  icon: ReactNode;
  badge?: string | number;
}
