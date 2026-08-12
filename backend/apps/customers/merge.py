"""Safe consolidation of duplicate Customer records by normalized mobile.

Purpose
-------
The Customers API rejects duplicate mobile numbers on create/update, but
legacy/seed data can still contain two or more Customer rows whose primary
mobiles normalize (``normalize_mobile_number``) to the same key. Deleting the
extras outright would cascade-delete or null out their business history
(orders, measurements, payments, invoices, reminders).

This module implements the sanctioned cleanup flow:

1. Detect duplicate groups by normalized primary mobile.
2. Choose one canonical Customer per group (most related records, oldest id).
3. Reassign every related record (Order, Measurement, ManualReminder) to the
   canonical customer, renumbering measurement versions so the
   ``(customer, garment_type, version)`` uniqueness constraint holds and the
   ``is_current`` marker stays on exactly the newest version.
4. Merge useful profile fields that the canonical customer is missing.
5. Delete the duplicate Customer only after every relationship is moved.

The whole operation runs inside a single transaction: a failure rolls back
everything, so the database is never left partially merged.

Design rules
------------
- Nothing is ever deleted before its relations are moved; ``Order`` and
  ``Measurement`` use CASCADE and ``ManualReminder`` uses SET_NULL, so a naive
  ``Customer.delete()`` would silently destroy or detach business history.
- Financial history is never modified: orders, order items, invoices,
  invoice items and payments keep their ids, numbers and amounts. Only the
  ``customer`` foreign key on the parent rows moves.
- Measurement rows are preserved in full (values, notes, created_at); only the
  owning customer and the version sequence are adjusted when required by the
  database constraint.
- The canonical customer's identity (id, primary mobile) is never changed.
"""

from collections import defaultdict

from django.db import transaction
from django.db.models import Count, Max

from apps.billing.models import ManualReminder
from apps.customers.models import Customer, Measurement
from apps.customers.serializers import normalize_mobile_number
from apps.orders.models import Order

PROFILE_FIELDS = ("full_name", "address", "notes", "alternate_mobile_number")

# Direct foreign keys to Customer. Every model below must be fully reassigned
# before a duplicate Customer is deleted.
CUSTOMER_RELATED_MODELS = (Order, Measurement, ManualReminder)


def normalized_primary(customer):
    """Return the normalized lookup key for a customer's primary mobile."""
    return normalize_mobile_number(customer.mobile_number)


def related_counts(customer):
    """Count meaningful related records for a customer."""
    return {
        "orders": customer.orders.count(),
        "measurements": customer.measurements.count(),
        "manual_reminders": customer.manual_reminders.count(),
    }


def find_duplicate_groups():
    """Return {normalized_key: [Customer, ...]} groups with more than one member.

    Only customers whose primary mobile normalizes are considered; records with
    unusable numbers are reported separately by ``unnormalizable_customers``.
    """
    groups = defaultdict(list)
    for customer in Customer.objects.all().order_by("id"):
        key = normalized_primary(customer)
        if key is None:
            continue
        groups[key].append(customer)
    return {key: value for key, value in groups.items() if len(value) > 1}


def unnormalizable_customers():
    """Customers whose primary mobile cannot be normalized (reported, never merged)."""
    return [
        customer
        for customer in Customer.objects.all().order_by("id")
        if normalized_primary(customer) is None
    ]


def choose_canonical(group):
    """Pick the canonical customer for a duplicate group.

    Rule (from the cleanup spec):
    1. Most meaningful/historical related records (orders weighted highest,
       then payments/invoices via orders, measurements, reminders).
    2. If tied, the oldest record (lowest id / earliest creation).
    """
    def score(customer):
        orders = customer.orders.count()
        invoices = customer.orders.filter(invoice__isnull=False).count()
        payments = customer.orders.filter(invoice__payments__isnull=False).count()
        return (
            orders * 4
            + payments * 3
            + invoices * 2
            + customer.measurements.count() * 2
            + customer.manual_reminders.count()
        )

    return max(group, key=lambda customer: (score(customer), -customer.id))


def find_alternate_conflicts():
    """Report primary-vs-alternate conflicts that exist outside the merge.

    Returns a list of dicts describing (a) customers whose primary equals
    another customer's alternate, (b) alternates shared by two customers, and
    (c) a customer whose alternate equals their own primary. These are
    pre-existing data issues surfaced for manual review, never silently fixed.
    """
    customers = list(Customer.objects.all())
    by_primary = defaultdict(list)
    by_alternate = defaultdict(list)
    for customer in customers:
        primary = normalized_primary(customer)
        alternate = normalize_mobile_number(customer.alternate_mobile_number)
        if primary:
            by_primary[primary].append(customer)
        if alternate:
            by_alternate[alternate].append(customer)

    conflicts = []
    for key, holders in sorted(by_alternate.items()):
        if len(holders) > 1:
            conflicts.append(
                {
                    "type": "shared_alternate",
                    "normalized": key,
                    "customers": [h.id for h in holders],
                }
            )
        for holder in holders:
            if normalized_primary(holder) == key:
                conflicts.append(
                    {
                        "type": "primary_equals_alternate",
                        "customer": holder.id,
                        "normalized": key,
                    }
                )
            for owner in by_primary.get(key, []):
                if owner.id != holder.id:
                    conflicts.append(
                        {
                            "type": "primary_equals_other_alternate",
                            "customer": owner.id,
                            "normalized": key,
                            "alternate_owner": holder.id,
                        }
                    )
    return conflicts


def _alternate_is_safe(canonical, value):
    """True if ``value`` can become canonical's alternate without a new conflict."""
    key = normalize_mobile_number(value)
    if not key:
        return False
    if key == normalized_primary(canonical):
        return False
    for other in Customer.objects.exclude(pk=canonical.pk):
        if normalize_mobile_number(other.mobile_number) == key:
            return False
        if normalize_mobile_number(other.alternate_mobile_number) == key:
            return False
    return True


def merge_profile(canonical, duplicate):
    """Fill profile fields the canonical customer is missing from the duplicate.

    The canonical customer's valid data is never overwritten. Conflicting
    non-blank values are reported for manual review instead of being silently
    replaced. Returns ``{"merged_fields": {...}, "conflicts": [...]}``.
    """
    merged = {}
    conflicts = []
    for field in PROFILE_FIELDS:
        canonical_value = getattr(canonical, field)
        duplicate_value = getattr(duplicate, field)
        if not duplicate_value:
            continue
        if field == "alternate_mobile_number":
            if canonical_value:
                if normalize_mobile_number(canonical_value) != normalize_mobile_number(
                    duplicate_value
                ):
                    conflicts.append(
                        {
                            "field": field,
                            "canonical": canonical_value,
                            "duplicate": duplicate_value,
                        }
                    )
                continue
            if not _alternate_is_safe(canonical, duplicate_value):
                continue
            merged[field] = duplicate_value
            continue
        if canonical_value:
            if canonical_value.strip() != duplicate_value.strip():
                conflicts.append(
                    {
                        "field": field,
                        "canonical": canonical_value,
                        "duplicate": duplicate_value,
                    }
                )
            continue
        merged[field] = duplicate_value

    if merged:
        for field, value in merged.items():
            setattr(canonical, field, value)
        canonical.save(update_fields=list(merged))
    return {"merged_fields": merged, "conflicts": conflicts}


def _reassign_orders(duplicate, canonical):
    moved = list(
        Order.objects.filter(customer=duplicate).values_list("id", "order_number")
    )
    Order.objects.filter(customer=duplicate).update(customer=canonical)
    return moved


def _reassign_manual_reminders(duplicate, canonical):
    moved = list(
        ManualReminder.objects.filter(customer=duplicate).values_list("id", "title")
    )
    ManualReminder.objects.filter(customer=duplicate).update(customer=canonical)
    return moved


def _reassign_measurements(duplicate, canonical):
    """Move measurements and renumber versions to satisfy the unique constraint.

    For each garment type the duplicate owns, versions are shifted above the
    canonical customer's current maximum version for that garment. Rows are
    preserved (values, notes, created_at); only ``customer`` and ``version``
    change. ``is_current`` is recomputed afterwards so exactly the newest
    version of each (customer, garment_type) is marked current.

    Uses queryset ``update`` (not ``save``) so the ``auto_now`` ``updated_at``
    timestamps of the historical rows are not touched.
    """
    moved = []
    garments = set(
        Measurement.objects.filter(customer=duplicate).values_list(
            "garment_type", flat=True
        )
    )
    for garment_type in garments:
        max_version = (
            Measurement.objects.filter(customer=canonical, garment_type=garment_type)
            .aggregate(max=Max("version"))["max"]
            or 0
        )
        for measurement in Measurement.objects.filter(
            customer=duplicate, garment_type=garment_type
        ).order_by("version"):
            new_version = max_version + measurement.version
            Measurement.objects.filter(pk=measurement.pk).update(
                version=new_version, customer=canonical
            )
            moved.append(
                {
                    "id": measurement.id,
                    "garment_type": garment_type,
                    "old_version": measurement.version,
                    "new_version": new_version,
                }
            )
    _refresh_current_markers(canonical)
    return moved


def _refresh_current_markers(customer):
    """Ensure exactly one ``is_current`` measurement per (customer, garment_type)."""
    for garment_type in Measurement.objects.filter(customer=customer).values_list(
        "garment_type", flat=True
    ).distinct():
        newest = (
            Measurement.objects.filter(customer=customer, garment_type=garment_type)
            .order_by("-version")
            .first()
        )
        if newest is None:
            continue
        Measurement.objects.filter(
            customer=customer, garment_type=garment_type, is_current=True
        ).exclude(pk=newest.pk).update(is_current=False)
        Measurement.objects.filter(pk=newest.pk).update(is_current=True)


def merge_customer(duplicate, canonical):
    """Consolidate one duplicate customer into the canonical customer.

    Steps: reassign orders, measurements, manual reminders -> merge profile ->
    delete the duplicate. All writes happen inside ``run_merge``'s outer
    transaction. Returns a dict describing everything that was moved.
    """
    result = {
        "duplicate_id": duplicate.id,
        "duplicate_name": duplicate.full_name,
        "canonical_id": canonical.id,
        "reassigned": {
            "orders": _reassign_orders(duplicate, canonical),
            "measurements": _reassign_measurements(duplicate, canonical),
            "manual_reminders": _reassign_manual_reminders(duplicate, canonical),
        },
        "profile": merge_profile(canonical, duplicate),
    }

    # Nothing references the duplicate anymore; delete without cascades.
    deleted_count, _ = duplicate.delete()
    result["deleted"] = deleted_count == 1
    return result


@transaction.atomic
def run_merge():
    """Merge every duplicate group. Returns per-group results.

    The outer transaction guarantees atomicity: if any merge raises, the whole
    cleanup rolls back and no partial state is left behind.
    """
    groups = find_duplicate_groups()
    results = []
    for normalized, group in groups.items():
        canonical = choose_canonical(group)
        group_result = {"normalized": normalized, "canonical_id": canonical.id}
        group_result["merges"] = [
            merge_customer(customer, canonical)
            for customer in group
            if customer.id != canonical.id
        ]
        results.append(group_result)
    return results


def audit_database():
    """Post-cleanup audit: total customers, unique normalized primaries, duplicates."""
    customers = list(Customer.objects.all())
    keys = [normalized_primary(c) for c in customers]
    from collections import Counter

    counter = Counter(key for key in keys if key is not None)
    duplicates = {key: count for key, count in counter.items() if count > 1}
    return {
        "total_customers": len(customers),
        "unique_normalized_primaries": len(counter),
        "unnormalizable": sum(1 for key in keys if key is None),
        "duplicate_normalized_primaries": len(duplicates),
        "duplicate_keys": duplicates,
    }
