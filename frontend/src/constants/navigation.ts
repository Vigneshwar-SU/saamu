import React from 'react';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import SavingsIcon from '@mui/icons-material/Savings';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import ReceiptIcon from '@mui/icons-material/Receipt';
import PaymentIcon from '@mui/icons-material/Payment';
import BarChartIcon from '@mui/icons-material/BarChart';
import SettingsIcon from '@mui/icons-material/Settings';
import { NavItem } from '../types/navigation';

export const SIDEBAR_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    path: '/dashboard',
    icon: React.createElement(DashboardIcon),
  },
  {
    id: 'customers',
    title: 'Customers',
    path: '/customers',
    icon: React.createElement(PeopleIcon),
  },
  {
    id: 'orders',
    title: 'Orders',
    path: '/orders',
    icon: React.createElement(ShoppingBagIcon),
  },
  {
    id: 'tailors',
    title: 'Tailors',
    path: '/tailors',
    icon: React.createElement(ContentCutIcon),
  },
  {
    id: 'attendance',
    title: 'Attendance',
    path: '/attendance',
    icon: React.createElement(FactCheckIcon),
  },
  {
    id: 'payroll',
    title: 'Payroll',
    path: '/payroll',
    icon: React.createElement(PointOfSaleIcon),
  },
  {
    id: 'advances',
    title: 'Advances',
    path: '/advances',
    icon: React.createElement(SavingsIcon),
  },
  {
    id: 'income',
    title: 'Income',
    path: '/income',
    icon: React.createElement(AccountBalanceWalletIcon),
  },
  {
    id: 'expenses',
    title: 'Expenses',
    path: '/expenses',
    icon: React.createElement(ReceiptLongIcon),
  },
  {
    id: 'invoices',
    title: 'Invoices',
    path: '/invoices',
    icon: React.createElement(ReceiptIcon),
  },
  {
    id: 'payments',
    title: 'Payments',
    path: '/payments',
    icon: React.createElement(PaymentIcon),
  },
  {
    id: 'reports',
    title: 'Reports',
    path: '/reports',
    icon: React.createElement(BarChartIcon),
  },
  {
    id: 'settings',
    title: 'Settings',
    path: '/settings',
    icon: React.createElement(SettingsIcon),
  },
];
