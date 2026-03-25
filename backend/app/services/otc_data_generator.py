"""
Order-to-Cash data generator.

Produces realistic order-to-cash lifecycle data:
- 50 Orders linked to approved quotes
- 5 provisioning steps per order (license_validation, entitlement_setup, workspace_config, billing_setup, activation)
- 95% succeed fully, 3% fail at provisioning, 2% have billing warnings
- Billing records: 90% paid, 5% pending, 3% overdue, 2% failed
- Validation results: product compatibility, discount thresholds, contract terms
- Timeline: 1-3 days creation → activation, billing starts next cycle
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from ..models.order_to_cash import (
    BillingRecord,
    BillingStatus,
    LineItem,
    Order,
    OrderStatus,
    ProvisioningStatus,
    ProvisioningStep,
    ValidationResult,
    ValidationStatus,
)

PROVISIONING_STEPS = [
    "license_validation",
    "entitlement_setup",
    "workspace_config",
    "billing_setup",
    "activation",
]

PRODUCTS = [
    ("Intercom Essential", 79.0),
    ("Intercom Advanced", 132.0),
    ("Intercom Expert", 199.0),
    ("Fin AI Agent", 0.99),  # per resolution
    ("Proactive Support Plus", 49.0),
    ("Product Tours", 29.0),
    ("Surveys", 19.0),
    ("WhatsApp Add-on", 9.0),
]

ACCOUNT_NAMES = [
    "Acme Corp", "TechFlow Inc", "Meridian Health", "FinLeap GmbH",
    "ShopWave", "DataPulse", "CloudNine SaaS", "NovaPay",
    "HealthBridge", "CyberVault", "GreenStack", "Pixel Labs",
    "OmniRetail", "SwiftLogistics", "BrightPath Education",
    "FintechPro", "AeroConnect", "FoodChain AI", "LegalEase",
    "PropTech Solutions", "InsureTech Co", "MediaFlow",
    "EduSpark", "TravelMesh", "AgriSense", "AutoDrive Labs",
    "BioGenix", "ClearView Analytics", "DevOps Central",
    "EnergyGrid", "Falcon Security", "GameForge",
    "HorizonAI", "InfraCore", "JetCommerce", "KineticHR",
    "LunarPay", "MegaScale", "NetPulse", "OptiRoute",
    "PeakPerform", "QuantumLeap", "RapidDeploy", "SkyBridge",
    "TurboStack", "UrbanTech", "VeloCity", "WaveOps",
    "XenithData", "ZephyrCloud",
]

PROVISIONING_ERRORS = [
    "License key generation failed: upstream licensing service timeout after 30s",
    "Entitlement conflict: existing trial entitlements must be migrated before activation",
    "Workspace provisioning error: region 'eu-west-1' capacity limit reached, retry with 'eu-central-1'",
    "Billing system sync failed: Stripe customer object creation returned 429 rate limit",
    "Activation blocked: pending compliance review for healthcare-regulated account",
    "SSO configuration failed: SAML metadata endpoint unreachable for customer IdP",
    "Workspace config error: custom subdomain 'app' is reserved, customer must choose another",
]

BILLING_OVERDUE_REASONS = [
    "Payment method declined — card expired",
    "Invoice disputed by accounts payable",
    "PO number mismatch — awaiting correction",
    "Wire transfer not yet received (net-30 terms)",
    "ACH payment returned — insufficient funds",
]


def _seeded_random(seed_str: str) -> random.Random:
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:16], 16)
    return random.Random(h)


class OTCDataGenerator:
    """Generates deterministic order-to-cash demo data."""

    def __init__(self, seed: str = "otc-demo-2026", num_orders: int = 50):
        self._seed = seed
        self._num_orders = num_orders
        self._rng = _seeded_random(seed)
        self._base_date = datetime(2026, 1, 5, 9, 0, 0)

    def generate(self) -> Dict[str, Any]:
        orders, line_items_map = self._generate_orders()
        provisioning = self._generate_provisioning(orders)
        validations = self._generate_validations(orders, line_items_map)
        self._apply_provisioning_outcomes(orders, provisioning)
        billing = self._generate_billing(orders)

        return {
            "orders": [o.to_dict() for o in orders],
            "provisioning_steps": [s.to_dict() for s in provisioning],
            "billing_records": [b.to_dict() for b in billing],
            "validation_results": [v.to_dict() for v in validations],
            "summary": self._compute_summary(orders, provisioning, billing, validations),
        }

    def _generate_orders(self) -> Tuple[List[Order], Dict[str, List[LineItem]]]:
        orders: List[Order] = []
        line_items_map: Dict[str, List[LineItem]] = {}

        for i in range(self._num_orders):
            order_id = f"ORD-2026-{i + 1:04d}"
            quote_id = f"QT-2026-{i + 1:04d}"
            account_id = f"ACC-{i + 1:05d}"
            account_name = ACCOUNT_NAMES[i % len(ACCOUNT_NAMES)]

            created_offset = timedelta(
                days=self._rng.randint(0, 60),
                hours=self._rng.randint(8, 17),
                minutes=self._rng.randint(0, 59),
            )
            created_date = self._base_date + created_offset

            items = self._generate_line_items()
            total = round(sum(li.total for li in items), 2)
            line_items_map[order_id] = items

            order = Order(
                id=order_id,
                quote_id=quote_id,
                account_id=account_id,
                account_name=account_name,
                status=OrderStatus.PENDING,
                total=total,
                line_items=items,
                created_date=created_date,
            )
            orders.append(order)

        return orders, line_items_map

    def _generate_line_items(self) -> List[LineItem]:
        num_items = self._rng.choices([1, 2, 3, 4], weights=[15, 40, 30, 15])[0]
        selected = self._rng.sample(PRODUCTS, min(num_items, len(PRODUCTS)))

        items = []
        for product_name, base_price in selected:
            if "Fin AI" in product_name:
                quantity = self._rng.choice([500, 1000, 2000, 5000])
            else:
                quantity = self._rng.choice([1, 5, 10, 25, 50, 100])
            unit_price = base_price
            total = round(unit_price * quantity, 2)
            items.append(LineItem(product=product_name, quantity=quantity, unit_price=unit_price, total=total))
        return items

    def _generate_provisioning(self, orders: List[Order]) -> List[ProvisioningStep]:
        steps: List[ProvisioningStep] = []

        for order in orders:
            step_base_time = order.created_date + timedelta(hours=self._rng.randint(1, 4))

            for j, step_name in enumerate(PROVISIONING_STEPS):
                started_at = step_base_time + timedelta(hours=j * self._rng.randint(2, 8))
                duration_minutes = self._rng.randint(5, 120)
                completed_at = started_at + timedelta(minutes=duration_minutes)

                step = ProvisioningStep(
                    order_id=order.id,
                    step_name=step_name,
                    status=ProvisioningStatus.SUCCESS,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                steps.append(step)

        return steps

    def _apply_provisioning_outcomes(
        self, orders: List[Order], steps: List[ProvisioningStep]
    ) -> None:
        """Apply the 95%/3%/2% distribution across orders."""
        order_ids = [o.id for o in orders]
        self._rng.shuffle(order_ids)

        num_failed = max(1, round(self._num_orders * 0.03))
        num_warning = max(1, round(self._num_orders * 0.02))
        failed_ids = set(order_ids[:num_failed])
        warning_ids = set(order_ids[num_failed : num_failed + num_warning])

        steps_by_order: Dict[str, List[ProvisioningStep]] = {}
        for s in steps:
            steps_by_order.setdefault(s.order_id, []).append(s)

        for order in orders:
            order_steps = steps_by_order.get(order.id, [])

            if order.id in failed_ids:
                fail_index = self._rng.randint(1, len(PROVISIONING_STEPS) - 1)
                for idx, s in enumerate(order_steps):
                    if idx == fail_index:
                        s.status = ProvisioningStatus.FAILED
                        s.error_message = self._rng.choice(PROVISIONING_ERRORS)
                        s.completed_at = None
                    elif idx > fail_index:
                        s.status = ProvisioningStatus.PENDING
                        s.started_at = None
                        s.completed_at = None
                order.status = OrderStatus.FAILED

            elif order.id in warning_ids:
                order.status = OrderStatus.ACTIVE
                activation_delay = timedelta(days=self._rng.randint(1, 3), hours=self._rng.randint(0, 12))
                order.activated_date = order.created_date + activation_delay

            else:
                order.status = OrderStatus.ACTIVE
                activation_delay = timedelta(days=self._rng.randint(1, 3), hours=self._rng.randint(0, 12))
                order.activated_date = order.created_date + activation_delay

        for order in orders:
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.ACTIVE
                activation_delay = timedelta(days=self._rng.randint(1, 3))
                order.activated_date = order.created_date + activation_delay

    def _generate_validations(
        self, orders: List[Order], line_items_map: Dict[str, List[LineItem]]
    ) -> List[ValidationResult]:
        results: List[ValidationResult] = []

        for order in orders:
            items = line_items_map.get(order.id, [])

            results.append(ValidationResult(
                order_id=order.id,
                field="product_compatibility",
                status=ValidationStatus.PASS,
                message="All selected products are compatible with the account plan",
            ))

            if order.total > 50000:
                results.append(ValidationResult(
                    order_id=order.id,
                    field="discount_approval",
                    status=ValidationStatus.WARNING,
                    message=f"Order total ${order.total:,.2f} exceeds auto-approval threshold ($50,000). VP sign-off required.",
                ))
            else:
                results.append(ValidationResult(
                    order_id=order.id,
                    field="discount_approval",
                    status=ValidationStatus.PASS,
                    message="Order total within auto-approval threshold",
                ))

            has_annual = any(li.quantity >= 50 for li in items)
            if has_annual:
                results.append(ValidationResult(
                    order_id=order.id,
                    field="contract_term",
                    status=ValidationStatus.PASS,
                    message="Annual commitment validated — volume discount applied",
                ))
            else:
                results.append(ValidationResult(
                    order_id=order.id,
                    field="contract_term",
                    status=ValidationStatus.PASS,
                    message="Monthly billing terms confirmed",
                ))

            if any("WhatsApp" in li.product for li in items):
                results.append(ValidationResult(
                    order_id=order.id,
                    field="regional_compliance",
                    status=ValidationStatus.PASS,
                    message="WhatsApp Business API compliance verified for account region",
                ))

            if any("Fin AI" in li.product for li in items) and any(li.quantity >= 5000 for li in items):
                results.append(ValidationResult(
                    order_id=order.id,
                    field="ai_usage_cap",
                    status=ValidationStatus.WARNING,
                    message="Fin AI resolution volume (5000+) may require dedicated capacity — flag for CSM review",
                ))

        return results

    def _generate_billing(self, orders: List[Order]) -> List[BillingRecord]:
        records: List[BillingRecord] = []
        billing_counter = 0

        active_orders = [o for o in orders if o.status == OrderStatus.ACTIVE and o.activated_date]

        for order in active_orders:
            period_start = order.activated_date.replace(day=1, hour=0, minute=0, second=0) + timedelta(days=32)
            period_start = period_start.replace(day=1)

            num_months = self._rng.randint(1, 3)
            for m in range(num_months):
                billing_counter += 1
                month_start = period_start + timedelta(days=30 * m)
                month_start = month_start.replace(day=1)
                next_month = month_start + timedelta(days=32)
                month_end = next_month.replace(day=1) - timedelta(seconds=1)

                invoice_number = f"INV-2026-{billing_counter:05d}"
                record = BillingRecord(
                    id=f"BILL-{billing_counter:05d}",
                    order_id=order.id,
                    account_id=order.account_id,
                    amount=order.total,
                    period_start=month_start,
                    period_end=month_end,
                    status=BillingStatus.PAID,
                    invoice_number=invoice_number,
                )
                records.append(record)

        # Apply 90/5/3/2 distribution across all billing records
        rng2 = _seeded_random(self._seed + "-billing")
        indices = list(range(len(records)))
        rng2.shuffle(indices)
        num_pending = max(1, round(len(records) * 0.05))
        num_overdue = max(1, round(len(records) * 0.03))
        num_failed = max(1, round(len(records) * 0.02))
        for i in indices[:num_pending]:
            records[i].status = BillingStatus.PENDING
        for i in indices[num_pending : num_pending + num_overdue]:
            records[i].status = BillingStatus.OVERDUE
        for i in indices[num_pending + num_overdue : num_pending + num_overdue + num_failed]:
            records[i].status = BillingStatus.INVOICED  # "failed" billing = stuck at invoiced

        return records

    def _compute_summary(
        self,
        orders: List[Order],
        steps: List[ProvisioningStep],
        billing: List[BillingRecord],
        validations: List[ValidationResult],
    ) -> Dict[str, Any]:
        total_orders = len(orders)
        active = sum(1 for o in orders if o.status == OrderStatus.ACTIVE)
        failed = sum(1 for o in orders if o.status == OrderStatus.FAILED)

        total_invoiced = sum(b.amount for b in billing)
        total_collected = sum(b.amount for b in billing if b.status == BillingStatus.PAID)
        total_overdue = sum(b.amount for b in billing if b.status == BillingStatus.OVERDUE)
        collection_rate = round(total_collected / total_invoiced * 100, 1) if total_invoiced else 0

        prov_success = sum(1 for s in steps if s.status == ProvisioningStatus.SUCCESS)
        prov_failed = sum(1 for s in steps if s.status == ProvisioningStatus.FAILED)
        prov_total = sum(1 for s in steps if s.status != ProvisioningStatus.PENDING)

        val_warnings = sum(1 for v in validations if v.status == ValidationStatus.WARNING)
        val_fails = sum(1 for v in validations if v.status == ValidationStatus.FAIL)

        activation_times = []
        for o in orders:
            if o.activated_date:
                delta = (o.activated_date - o.created_date).total_seconds() / 3600
                activation_times.append(delta)
        avg_activation_hours = round(sum(activation_times) / len(activation_times), 1) if activation_times else 0

        return {
            "total_orders": total_orders,
            "active_orders": active,
            "failed_orders": failed,
            "success_rate": round(active / total_orders * 100, 1) if total_orders else 0,
            "avg_activation_hours": avg_activation_hours,
            "total_revenue": round(sum(o.total for o in orders if o.status == OrderStatus.ACTIVE), 2),
            "billing": {
                "total_invoiced": round(total_invoiced, 2),
                "total_collected": round(total_collected, 2),
                "total_overdue": round(total_overdue, 2),
                "collection_rate": collection_rate,
                "record_count": len(billing),
                "status_breakdown": {
                    "paid": sum(1 for b in billing if b.status == BillingStatus.PAID),
                    "pending": sum(1 for b in billing if b.status == BillingStatus.PENDING),
                    "overdue": sum(1 for b in billing if b.status == BillingStatus.OVERDUE),
                    "invoiced": sum(1 for b in billing if b.status == BillingStatus.INVOICED),
                },
            },
            "provisioning": {
                "total_steps": prov_total,
                "success": prov_success,
                "failed": prov_failed,
                "success_rate": round(prov_success / prov_total * 100, 1) if prov_total else 0,
            },
            "validation": {
                "warnings": val_warnings,
                "failures": val_fails,
            },
        }
