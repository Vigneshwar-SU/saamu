# Saamu Tailors — Domain Model Direction

This is a **domain design document**, not a final database schema.

The implementation agent should refine field names, constraints, indexes, and relationships before migrations are created.

## Core domains

### User

Represents application users.

Key concepts:

- username/login identity
- display name
- role
- active status
- password/authentication fields
- timestamps

Roles:

- OWNER
- STAFF

### Shop

Represents the business configuration.

Potential concepts:

- name
- address
- contact numbers
- logo
- bill settings
- operational settings

### Customer

Represents a customer.

Potential concepts:

- customer identifier
- name
- phone
- alternate phone
- address
- notes
- timestamps

Relationship:

```text
Customer 1 ──── * Order
```

### Order

Represents a customer's tailoring transaction.

Potential concepts:

- order number
- customer
- created date
- due date
- status
- notes
- totals
- timestamps

Relationship:

```text
Customer 1 ──── * Order
Order    1 ──── * OrderItem
```

### OrderItem

Represents a garment/item within an order.

Potential concepts:

- garment type
- quantity
- price
- measurements snapshot/reference
- tailoring workflow status
- tailor assignment
- notes

This is important because one order can contain multiple garments.

### GarmentType

Configurable garment category.

Examples may include:

- Shirt
- Pant
- Blouse
- Churidar
- Kurta

Do not hard-code the final list without confirmation.

### Measurement

Represents measurements used for a specific garment/order.

Important principle:

Historical measurements must be preserved.

A customer may have different measurements across different orders.

### Tailor

Represents a tailor who performs stitching work.

Potential concepts:

- name
- phone
- active status
- joining date
- payment model
- notes

### TailorAssignment / Work

Represents the relationship between a tailor and the work they perform.

The final model should support workload tracking and historical work.

### TailorSalary / TailorPayment

Represents salary/payment made to a tailor.

The exact model depends on the shop's actual compensation method.

### CustomerPayment

Represents money received from a customer.

Potential concepts:

- order
- amount
- payment date
- payment method
- reference/notes
- recorded by

### Expense

Represents money spent by the business.

Potential concepts:

- category
- amount
- date
- description
- payment method
- recorded by

### LockerLocation

Represents storage information for ready garments.

Potential concepts:

- locker identifier
- location
- status

The final design must support identifying where a ready garment is stored.

### Notification

Represents customer communication events.

Potential concepts:

- order/customer
- channel
- message/template
- status
- sent timestamp
- provider reference

This can be implemented after core workflow stabilization.

### AuditLog

Represents important system activity.

Potential concepts:

- user
- action
- entity type
- entity ID
- timestamp
- metadata/context

## High-level relationship map

```text
User
 ├── records CustomerPayment
 ├── records Expense
 └── creates/changes AuditLog

Customer
 └── Order
      ├── OrderItem
      │    ├── Measurement Snapshot
      │    ├── Tailor Assignment
      │    └── Locker/Delivery state
      │
      └── CustomerPayment

Tailor
 ├── TailorAssignment
 └── TailorSalary/Payment

Order
 └── Notification

Shop
 └── Configuration / Settings
```

## Important design principles

### Do not put everything into Order

An order can have multiple garments.

Therefore garment-specific information should generally belong to OrderItem.

### Do not store only the customer's latest measurement

Historical order measurements must remain accurate.

### Do not duplicate income

Customer payments should feed income reporting.

### Do not use dashboard counters as source data

Dashboard values should be calculated from transactional data.

### Do not hard-delete important financial history casually

Use cancellation/reversal/archival approaches where appropriate.

## Schema implementation rule

Before creating production migrations, the implementation agent must verify:

- relationships
- cardinality
- uniqueness
- indexes
- foreign-key behavior
- deletion behavior
- historical data preservation
- monetary precision
- timestamps
- audit requirements

Any significant schema decision that differs from this document should be documented.
