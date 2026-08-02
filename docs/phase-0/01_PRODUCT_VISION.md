# Saamu Tailors — Product Vision

## 1. Product summary

Saamu Tailors is a digital management system for a family tailoring business operating since 1954.

The shop does **custom stitching**. Customers bring their own cloth material, and the shop manages cutting, stitching, ironing, storage, customer communication, payments, and delivery.

The system will replace the current paper-based process for:

- Customer records
- Order records
- Measurements
- Tailoring workflow
- Tailor workload
- Tailor salary
- Income
- Expenses
- Payments
- Digital bills
- Ready-for-collection tracking
- Dashboard and reports

## 2. Primary objective

Create a simple, reliable system that helps the shop:

- Reduce paper-based record keeping.
- Quickly find customer and order information.
- Track every garment from cloth receipt to delivery.
- Know which tailor is working on which garments.
- Track tailor workload and salary.
- Track customer payments and balances.
- Track shop income and expenses.
- Generate digital bills.
- Know which finished garments are waiting for customers.
- Give the owner a clear view of business performance.

## 3. Users

Version 1 has exactly two roles:

### Owner

The owner is a full-access business user.

The owner can:

- View all business information.
- Perform operational tasks.
- Manage customers.
- Manage orders.
- Manage payments.
- Manage expenses.
- Manage tailors.
- Manage salaries.
- View dashboard and reports.
- Manage staff accounts.
- Manage permitted system/shop settings.

The owner should NOT be treated as a view-only user. The owner must be able to perform staff operations because the owner actively participates in the shop workflow.

### Staff

Staff handles daily operational work.

Staff can:

- Create and edit customers.
- Create and manage orders.
- Record measurements.
- Manage order workflow.
- Assign tailors.
- Update stitching/cutting/ironing statuses.
- Record payments.
- Generate bills.
- Record expenses.
- View required operational information.
- Manage day-to-day customer delivery/collection.

Staff must not have owner-only administrative privileges.

## 4. Deployment

### Version 1

The application will initially run on one Windows PC inside the shop.

Data will be stored locally in PostgreSQL.

No paid cloud server is required for Version 1.

### Future

The architecture must allow migration to cloud infrastructure without redesigning the business logic.

The application must therefore use:

- Separate React frontend.
- Django REST API backend.
- PostgreSQL database.
- Environment-based configuration.
- No hard-coded local filesystem/database assumptions in business logic.

## 5. Design principles

The application should be:

- Simple for shop staff.
- Fast for daily operations.
- Desktop-first.
- Easy to learn.
- Reliable.
- Professional.
- Maintainable.
- Cloud-ready.
- Data-safe.

Do not optimize the application for technical complexity at the expense of shop usability.
