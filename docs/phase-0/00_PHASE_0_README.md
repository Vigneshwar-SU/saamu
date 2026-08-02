# Saamu Tailors — Phase 0 Documentation

## Purpose

This folder contains the **Phase 0 Product & Architecture Planning documents** for Saamu Tailors.

These documents are the source of truth for the initial development of the application.

The development agent (OpenCode) should read these documents before implementing Phase 1 or any business feature.

## Project

**Name:** Saamu Tailors  
**Version:** Version 1  
**Current deployment:** Local Windows PC in the shop  
**Future deployment:** Cloud-ready architecture  
**Application type:** Internal tailoring management system

## Phase 0 goals

Phase 0 establishes:

1. Product vision
2. Real-world shop workflow
3. Version 1 scope
4. User roles and permissions
5. Business rules
6. High-level architecture
7. Data/domain model direction
8. API architecture principles
9. Non-functional requirements
10. Development boundaries

## Source-of-truth rule

When implementing the system:

- Follow these documents over assumptions.
- Do not invent business rules that are not specified.
- If implementation details are missing, choose the simplest scalable solution and document the decision.
- Do not add features outside Version 1 unless explicitly requested.
- Preserve the real workflow of the tailoring shop.
- Keep the architecture suitable for future cloud migration.

## Phase 0 status

**Planning baseline — approved for implementation.**

Phase 1 should begin only after these documents are placed in:

```text
docs/
└── phase-0/
```
