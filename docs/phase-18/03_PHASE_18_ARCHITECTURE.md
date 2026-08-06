# Phase 18 — Architecture

## Principle
Add a thin communication/presentation layer over existing authoritative customer, order, and payment services.

## Backend
Use the most appropriate existing app/shared layer for:
- deterministic message building;
- phone normalization;
- WhatsApp URL construction.

Avoid duplicate financial calculations.

## Frontend
Place communication actions only on existing relevant customer/order/payment surfaces. Prefer reusable communication components/hooks.

## Data Flow
Authoritative data → backend message preparation → safe message payload → user chooses Copy or Open WhatsApp → external WhatsApp handoff.

## Security Boundary
No arbitrary URL, command, filesystem path, or external execution input is accepted.

## Provider Boundary
WhatsApp Business / Meta Cloud API / Twilio are outside Phase 18.
