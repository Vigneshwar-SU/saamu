import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { MainLayout } from '../layouts/MainLayout';
import { Login } from '../pages/Login';
import { Customers } from '../pages/Customers';
import { CustomerDetail } from '../pages/CustomerDetail';
import { Orders } from '../pages/Orders';
import { OrderDetail } from '../pages/OrderDetail';
import { Tailors } from '../pages/Tailors';
import { TailorDetail } from '../pages/TailorDetail';
import { AttendancePage } from '../pages/Attendance';
import { Payroll } from '../pages/Payroll';
import { PayrollDetail } from '../pages/PayrollDetail';
import { SalaryConfigurations } from '../pages/SalaryConfigurations';
import { Advances } from '../pages/Advances';
import { Dashboard } from '../pages/Dashboard';
import { Income } from '../pages/Income';
import { Expenses } from '../pages/Expenses';
import { Invoices } from '../pages/Invoices';
import { InvoiceDetail } from '../pages/InvoiceDetail';
import { InvoiceBill } from '../pages/InvoiceBill';
import { Reports } from '../pages/Reports';
import { Reminders } from '../pages/Reminders';
import { Payments, Settings } from '../pages/Placeholders';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/login" element={<Login />} />

      {/* Authenticated ERP Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
          <Route path="/tailors" element={<Tailors />} />
          <Route path="/tailors/:id" element={<TailorDetail />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/payroll" element={<Payroll />} />
          <Route path="/payroll/:id" element={<PayrollDetail />} />
          <Route path="/salary-configurations" element={<SalaryConfigurations />} />
          <Route path="/advances" element={<Advances />} />
          <Route path="/income" element={<Income />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/invoices/:id" element={<InvoiceDetail />} />
          <Route path="/invoices/:id/bill" element={<InvoiceBill />} />
          <Route path="/reminders" element={<Reminders />} />
          <Route path="/payments" element={<Payments />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>

      {/* Fallback Catch-all Route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
