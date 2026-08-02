# Saamu Tailors — Real-World Shop Workflow

This document describes the actual business process the software must support.

## 1. Shop opening

The shop opens and daily operations begin.

The owner/staff should be able to see pending work from previous days.

Useful information includes:

- Orders waiting for cutting.
- Orders currently being stitched.
- Orders waiting for ironing.
- Orders ready for collection.
- Customers with pending balances.

## 2. Customer arrives

A customer brings cloth material for stitching or comes to collect an existing order.

The staff should first identify the customer.

### Existing customer

Search using information such as:

- Name
- Phone number
- Customer ID

Open the existing customer record.

### New customer

Create a new customer record.

## 3. New tailoring order

For a new stitching request:

1. Select/create customer.
2. Record garment type.
3. Record quantity.
4. Record relevant measurements.
5. Record price.
6. Record expected/due date if applicable.
7. Record advance payment if received.
8. Record notes/instructions.
9. Create the order.

A single customer order should be capable of containing multiple garment items.

Example:

- 2 shirts
- 1 pant

## 4. Cloth and cutting

The customer supplies the cloth.

The owner/father initially handles cutting according to the required measurements.

The system should support a cutting workflow such as:

```text
Order Created
    ↓
Cutting Pending
    ↓
Cutting In Progress
    ↓
Cutting Completed
```

The exact status names can be finalized during implementation.

## 5. Tailor assignment

After cutting, the garment can be assigned to a tailor.

The system should track:

- Tailor
- Assigned garment/order item
- Assignment date
- Work status

## 6. Stitching

The tailor works on the garment.

The order/item should move through a stitching workflow.

The system must make it easy to answer:

- What is each tailor currently working on?
- How many garments are pending for each tailor?
- Which orders are delayed?

## 7. Ironing

After stitching, garments may go for ironing.

The system should track ironing as part of the operational workflow where applicable.

## 8. Ready for collection

Once the garment is completed and ironed:

```text
Ready for Collection
```

The system should record that the garment is ready.

## 9. Locker/storage

Finished garments may be kept in a locker until the customer arrives.

The system should eventually support:

- Locker/location identifier.
- Date stored.
- Order/customer.
- Collection status.

The objective is to answer:

> Where is this customer's finished garment?

## 10. Customer contact

When an order is ready, the shop contacts the customer.

Version 1 should support the data needed for communication.

WhatsApp/SMS automation can be implemented as a dedicated feature later in Version 1 after the core workflow is stable.

## 11. Customer collection

Customer comes to collect the garment.

Staff should:

1. Find the order.
2. Verify the garment/order.
3. Check payment status.
4. Collect remaining balance if applicable.
5. Mark the order/item as delivered/collected.
6. Record collection date/time.

## 12. Payment

The system must distinguish:

- Total amount
- Advance/initial payment
- Additional payments
- Balance
- Refunds where required

Customer payment records should be the source for income calculations.

## 13. Bill

A digital bill should eventually be generated for the order/payment.

It should contain:

- Shop information
- Customer
- Order number
- Garment details
- Amounts
- Payments
- Balance
- Date
- Appropriate bill/invoice identifier

## 14. Daily business monitoring

The owner should be able to see:

- Today's orders.
- Orders in progress.
- Ready garments.
- Pending collections.
- Payments received.
- Expenses.
- Tailor workload.
- Pending customer balances.

## 15. Important workflow principle

The software should support the shop's current working style rather than forcing the family to radically change the way they work.

The system should reduce writing and searching, not add unnecessary data entry.
