# Phase 11 — API Specification

## API Convention
Use the project's existing `/api/v1/` convention and standard response/error contract.

## Required Capability

### Payment APIs
Provide the appropriate existing-architecture endpoints for:
- listing payments for an order
- recording a payment
- retrieving payment details
- recording/referring to refunds where supported by the established model

### Order Payment Summary
Expose:
- order total
- total paid
- balance/outstanding amount
- payment status

### Digital Bill
Provide an API response or endpoint that supplies the complete bill data required by the frontend.

## Authorization
- OWNER: read access.
- STAFF: read and payment/billing mutations.
- Anonymous: rejected.

## Important
Do not invent endpoint paths before inspecting the current URL/router conventions. Keep endpoint naming consistent with the existing project.
