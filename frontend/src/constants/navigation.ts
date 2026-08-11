import React from 'react';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import TuneIcon from '@mui/icons-material/Tune';
import SavingsIcon from '@mui/icons-material/Savings';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import ReceiptIcon from '@mui/icons-material/Receipt';
import PaymentIcon from '@mui/icons-material/Payment';
import BarChartIcon from '@mui/icons-material/BarChart';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import SettingsIcon from '@mui/icons-material/Settings';
import { NavItem } from '../types/navigation';

export const NAV_GROUPS = [
  { id: 'overview', label: 'Overview' },
  { id: 'customers', label: 'Customers' },
  { id: 'orders', label: 'Orders' },
  { id: 'tailoring', label: 'Tailoring' },
  { id: 'finance', label: 'Finance' },
  { id: 'insights', label: 'Insights' },
  { id: 'system', label: 'System' },
] as const;

export const SIDEBAR_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    path: '/dashboard',
    icon: React.createElement(DashboardIcon),
    group: NAV_GROUPS[0],
  },
  {
    id: 'customers',
    title: 'Customers',
    path: '/customers',
    icon: React.createElement(PeopleIcon),
    group: NAV_GROUPS[1],
  },
  {
    id: 'orders',
    title: 'Orders',
    path: '/orders',
    icon: React.createElement(ShoppingBagIcon),
    group: NAV_GROUPS[2],
  },
  {
    id: 'reminders',
    title: 'Reminders',
    path: '/reminders',
    icon: React.createElement(NotificationsActiveIcon),
    group: NAV_GROUPS[2],
  },
  {
    id: 'tailors',
    title: 'Tailors',
    path: '/tailors',
    icon: React.createElement(ContentCutIcon),
    group: NAV_GROUPS[3],
  },
  {
    id: 'attendance',
    title: 'Attendance',
    path: '/attendance',
    icon: React.createElement(FactCheckIcon),
    group: NAV_GROUPS[3],
  },
  {
    id: 'payroll',
    title: 'Payroll',
    path: '/payroll',
    icon: React.createElement(PointOfSaleIcon),
    group: NAV_GROUPS[3],
  },
  {
    id: 'salary-configurations',
    title: 'Salary Config',
    path: '/salary-configurations',
    icon: React.createElement(TuneIcon),
    group: NAV_GROUPS[3],
  },
  {
    id: 'advances',
    title: 'Advances',
    path: '/advances',
    icon: React.createElement(SavingsIcon),
    group: NAV_GROUPS[3],
  },
  {
    id: 'income',
    title: 'Income',
    path: '/income',
    icon: React.createElement(AccountBalanceWalletIcon),
    group: NAV_GROUPS[4],
  },
  {
    id: 'expenses',
    title: 'Expenses',
    path: '/expenses',
    icon: React.createElement(ReceiptLongIcon),
    group: NAV_GROUPS[4],
  },
  {
    id: 'invoices',
    title: 'Invoices',
    path: '/invoices',
    icon: React.createElement(ReceiptIcon),
    group: NAV_GROUPS[4],
  },
  {
    id: 'payments',
    title: 'Payments',
    path: '/payments',
    icon: React.createElement(PaymentIcon),
    group: NAV_GROUPS[4],
  },
  {
    id: 'reports',
    title: 'Reports',
    path: '/reports',
    icon: React.createElement(BarChartIcon),
    group: NAV_GROUPS[5],
  },
  {
    id: 'settings',
    title: 'Settings',
    path: '/settings',
    icon: React.createElement(SettingsIcon),
    group: NAV_GROUPS[6],
  },
];
