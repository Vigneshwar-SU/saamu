# Saamu Tailors — Version 1 Scope

## 1. Version 1 objective

Version 1 should digitize the core daily operations of Saamu Tailors.

## 2. Included modules

### Authentication & Authorization

- Owner login
- Staff login
- JWT-based authentication
- Role-based authorization
- Owner-only staff administration

### Shop & Master Data

- Shop profile
- Garment types
- Stitching/service types
- Basic configurable statuses where appropriate

### Customers

- Create customer
- Edit customer
- Search customer
- View customer
- Customer history
- Customer contact details

### Measurements

- Garment-specific measurements
- Measurements associated with an order/item snapshot
- Reuse previous measurements as a starting point
- Measurement history

### Orders

- Create order
- Multiple items per order
- Garment type
- Quantity
- Measurements
- Pricing
- Notes
- Due date
- Advance/payment information
- Order status
- Order history/timeline

### Cutting

- Cutting status
- Cutting workflow
- Cutting completion tracking

### Tailors

- Tailor profiles
- Tailor assignment
- Workload
- Current work
- Completed work

### Tailor Salary

- Salary/payment records
- Support the shop's actual salary model after business rules are finalized
- Salary history
- Pending/paid amounts where applicable

### Customer Payments

- Advance payment
- Partial payment
- Final payment
- Balance tracking
- Payment history

### Income

Income should be derived from customer payment records rather than manually duplicating the same payment as an income entry.

### Expenses

- Expense records
- Expense categories
- Amount
- Date
- Description
- Payment method if needed
- Recorded by

### Delivery & Locker

- Ready for collection
- Locker/location tracking
- Customer collection
- Delivery/collection date

### Digital Billing

- Generate digital bill
- PDF-ready bill design
- Customer/order/payment information

### Notifications

The system should be prepared for:

- WhatsApp
- SMS

Automation/provider integration can be introduced after the core order and payment workflow is stable.

### Dashboard

Dashboard should use actual stored data.

It should eventually include:

- Orders
- Income
- Expenses
- Net amount
- Pending balances
- Ready garments
- Garment counts
- Tailor workload
- Other useful operational KPIs

### Reports

- Income
- Expenses
- Orders
- Garments
- Tailors
- Customers
- Payments
- Business summaries

### Settings

Owner-level settings and administration.

### Audit

Track important changes and financial actions with:

- User
- Action
- Entity
- Timestamp
- Relevant before/after information where appropriate

### Backup

Provide a practical database backup and restore strategy for the local Windows deployment.

## 3. Explicitly out of scope for initial Version 1

Do NOT add these unless explicitly approved later:

- Multi-branch management
- Public customer portal
- Customer mobile application
- Online customer ordering
- Online payments
- Inventory/cloth stock management
- E-commerce
- AI features
- Complex accounting/ERP
- Payroll tax compliance
- Cloud deployment
- Subscription billing
- SaaS multi-tenancy

These may become Version 2+ features.

## 4. Scope principle

When uncertain whether a feature belongs in Version 1, prefer the smallest implementation that solves the real shop problem.

Do not add complexity merely because it is technically possible.
