"""Merge duplicate customer records by normalized mobile number.

Run without arguments for a read-only audit of duplicate groups, the
related-record counts, and the canonical customer that would be kept for each
group. Add ``--apply`` to actually consolidate duplicates inside a single
database transaction and print a post-merge audit.

Safety: ``--apply`` never touches financial history (orders, invoices,
payments keep their ids/numbers/amounts) and rolls back entirely if any part
of the merge fails.
"""

from django.core.management.base import BaseCommand

from apps.customers.merge import (
    audit_database,
    choose_canonical,
    find_alternate_conflicts,
    find_duplicate_groups,
    related_counts,
    run_merge,
    unnormalizable_customers,
)


class Command(BaseCommand):
    help = (
        "Audit and consolidate duplicate Customer records by normalized mobile "
        "number, preserving all related business history."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Perform the merge. Without this flag the command is read-only.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        groups = find_duplicate_groups()
        self.stdout.write("=== DUPLICATE CUSTOMER AUDIT ===")
        self.stdout.write("")
        if not groups:
            self.stdout.write("No duplicate groups found by normalized primary mobile.")
        else:
            for normalized, group in sorted(groups.items()):
                canonical = choose_canonical(group)
                self.stdout.write(f"Normalized mobile: {normalized}")
                for customer in group:
                    marker = "  <-- CANONICAL" if customer.id == canonical.id else ""
                    counts = related_counts(customer)
                    self.stdout.write(
                        f"  Customer #{customer.id} {customer.full_name!r} "
                        f"primary={customer.mobile_number!r} "
                        f"alternate={customer.alternate_mobile_number!r} "
                        f"orders={counts['orders']} "
                        f"measurements={counts['measurements']} "
                        f"reminders={counts['manual_reminders']}{marker}"
                    )
                self.stdout.write("")

        unnormalizable = unnormalizable_customers()
        if unnormalizable:
            self.stdout.write("=== CUSTOMERS WITH UNNORMALIZABLE PRIMARY MOBILE (reported, not merged) ===")
            for customer in unnormalizable:
                self.stdout.write(
                    f"  Customer #{customer.id} {customer.full_name!r} "
                    f"primary={customer.mobile_number!r}"
                )
            self.stdout.write("")

        conflicts = find_alternate_conflicts()
        self.stdout.write("=== PRIMARY vs ALTERNATE CONFLICTS (pre-existing, manual review) ===")
        if not conflicts:
            self.stdout.write("  None.")
        else:
            for conflict in conflicts:
                self.stdout.write(f"  {conflict}")
        self.stdout.write("")

        if apply:
            self.stdout.write("=== APPLYING MERGE (single transaction) ===")
            results = run_merge()
            total_deleted = 0
            total_reassigned = 0
            for group_result in results:
                self.stdout.write(
                    f"Group {group_result['normalized']}: canonical customer "
                    f"#{group_result['canonical_id']}"
                )
                for merge in group_result["merges"]:
                    self.stdout.write(
                        f"  merged #{merge['duplicate_id']} ({merge['duplicate_name']!r}) "
                        f"-> #{merge['canonical_id']}"
                    )
                    reassigned = merge["reassigned"]
                    total_deleted += 1
                    total_reassigned += (
                        len(reassigned["orders"])
                        + len(reassigned["measurements"])
                        + len(reassigned["manual_reminders"])
                    )
                    self.stdout.write(
                        f"    orders moved: {len(reassigned['orders'])}"
                    )
                    self.stdout.write(
                        f"    measurements moved: {len(reassigned['measurements'])}"
                    )
                    self.stdout.write(
                        f"    manual reminders moved: {len(reassigned['manual_reminders'])}"
                    )
                    if merge["profile"]["merged_fields"]:
                        self.stdout.write(
                            f"    profile fields merged: {list(merge['profile']['merged_fields'])}"
                        )
                    if merge["profile"]["conflicts"]:
                        self.stdout.write(
                            f"    profile conflicts (left as-is, manual review): "
                            f"{merge['profile']['conflicts']}"
                        )
            self.stdout.write(f"Deleted {total_deleted} duplicate customer(s), "
                              f"reassigned {total_reassigned} related record(s).")
            self.stdout.write("")

            audit = audit_database()
            self.stdout.write("=== POST-MERGE DATABASE AUDIT ===")
            self.stdout.write(f"  total customers: {audit['total_customers']}")
            self.stdout.write(
                f"  unique normalized primary mobiles: {audit['unique_normalized_primaries']}"
            )
            self.stdout.write(
                f"  duplicate normalized primary mobiles: {audit['duplicate_normalized_primaries']}"
            )
            self.stdout.write(f"  duplicate keys: {audit['duplicate_keys']}")
        else:
            self.stdout.write(
                "Read-only audit complete. Re-run with --apply to consolidate "
                "the duplicate groups above."
            )
