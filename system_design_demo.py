"""
System Design & Architecture: teaching demonstration
Python 3.10+, standard library only.

This is an educational simulation, NOT production payment code.
It does not connect to M-Pesa or any payment provider.
"""
from dataclasses import dataclass
from collections import deque
from time import perf_counter
from typing import Dict, Optional


@dataclass
class Invoice:
    invoice_id: str
    amount_due: float
    status: str = "UNPAID"


@dataclass
class Payment:
    provider_transaction_id: str
    invoice_id: str
    amount: float
    status: str = "CONFIRMED"


class RentPaymentSystem:
    """Tiny in-memory model of billing, idempotent callbacks, and notifications."""

    def __init__(self):
        self.invoices: Dict[str, Invoice] = {}
        self.payments_by_provider_id: Dict[str, Payment] = {}
        self.balance_cache: Dict[str, float] = {}
        self.notification_queue = deque()

    def create_invoice(self, invoice_id: str, amount_due: float) -> None:
        if amount_due <= 0:
            raise ValueError("Invoice amount must be positive.")
        if invoice_id in self.invoices:
            raise ValueError("Invoice ID already exists.")
        self.invoices[invoice_id] = Invoice(invoice_id, amount_due)
        self.balance_cache.pop(invoice_id, None)
        print(f"[billing] Created invoice {invoice_id}: KES {amount_due:,.2f}")

    def get_balance(self, invoice_id: str) -> float:
        """Cache-aside pattern: cache hit first, otherwise calculate from source data."""
        if invoice_id in self.balance_cache:
            print(f"[cache] HIT for {invoice_id}")
            return self.balance_cache[invoice_id]

        print(f"[cache] MISS for {invoice_id}; reading source data")
        invoice = self.invoices[invoice_id]
        paid = sum(
            p.amount for p in self.payments_by_provider_id.values()
            if p.invoice_id == invoice_id and p.status == "CONFIRMED"
        )
        balance = max(invoice.amount_due - paid, 0.0)
        self.balance_cache[invoice_id] = balance
        return balance

    def process_provider_callback(
        self, provider_transaction_id: str, invoice_id: str, amount: float,
        provider_verified: bool
    ) -> str:
        """
        Demonstrates idempotency. In production, verify provider signatures,
        validate account/reference/currency, and persist atomically with a DB.
        """
        if not provider_verified:
            raise PermissionError("Callback authenticity check failed.")
        if invoice_id not in self.invoices:
            raise KeyError("Unknown invoice reference.")
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        # Unique provider transaction IDs prevent duplicate callback processing.
        if provider_transaction_id in self.payments_by_provider_id:
            print(f"[payments] Duplicate callback ignored: {provider_transaction_id}")
            return "DUPLICATE_IGNORED"

        self.payments_by_provider_id[provider_transaction_id] = Payment(
            provider_transaction_id, invoice_id, amount
        )
        self.balance_cache.pop(invoice_id, None)  # invalidate stale cached balance

        invoice = self.invoices[invoice_id]
        new_balance = self.get_balance(invoice_id)
        invoice.status = "PAID" if new_balance == 0 else "PARTIALLY_PAID"

        # Notification is decoupled from the core payment record.
        self.notification_queue.append({
            "type": "PAYMENT_RECEIPT",
            "provider_transaction_id": provider_transaction_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "attempts": 0,
        })
        print(f"[payments] Confirmed {provider_transaction_id}; balance KES {new_balance:,.2f}")
        return "PAYMENT_RECORDED"

    def process_notifications(self, simulated_failure: bool = False) -> None:
        """A simple worker loop. Production queues need persistence and monitoring."""
        while self.notification_queue:
            job = self.notification_queue.popleft()
            job["attempts"] += 1
            if simulated_failure and job["attempts"] == 1:
                print("[worker] Notification provider unavailable; scheduling retry")
                self.notification_queue.append(job)
                simulated_failure = False
                continue
            print(
                f"[worker] Sent receipt for {job['provider_transaction_id']} "
                f"(attempt {job['attempts']})"
            )


def estimate_capacity(daily_actions: int, peak_multiplier: float,
                      average_latency_seconds: float) -> None:
    average_rps = daily_actions / 86_400
    peak_rps = average_rps * peak_multiplier
    average_in_flight = peak_rps * average_latency_seconds
    print("\n[capacity estimate]")
    print(f"Daily actions: {daily_actions:,}")
    print(f"Average RPS: {average_rps:.2f}")
    print(f"Assumed peak RPS ({peak_multiplier:g}x): {peak_rps:.2f}")
    print(
        f"Approx. in-flight requests at peak using Little's Law: "
        f"{average_in_flight:.1f}"
    )
    print("Reminder: estimates are assumptions; validate with load tests and telemetry.")


def main():
    print("=== Rent payment platform: system design demo ===")
    system = RentPaymentSystem()
    system.create_invoice("INV-2026-001", 12_000.00)

    print("\n1) Read balance (cache miss)")
    print(f"Balance: KES {system.get_balance('INV-2026-001'):,.2f}")

    print("\n2) Process a provider callback")
    system.process_provider_callback(
        provider_transaction_id="MPESA-DEMO-ABC123",
        invoice_id="INV-2026-001",
        amount=5_000.00,
        provider_verified=True,  # demo flag only; not a real verification mechanism
    )

    print("\n3) Read updated balance (cache should have been invalidated)")
    print(f"Balance: KES {system.get_balance('INV-2026-001'):,.2f}")

    print("\n4) Receive the same callback again (idempotency check)")
    system.process_provider_callback(
        provider_transaction_id="MPESA-DEMO-ABC123",
        invoice_id="INV-2026-001",
        amount=5_000.00,
        provider_verified=True,
    )

    print("\n5) Process notification with one simulated transient failure")
    system.process_notifications(simulated_failure=True)

    estimate_capacity(
        daily_actions=160_000,
        peak_multiplier=8,
        average_latency_seconds=0.2,
    )


if __name__ == "__main__":
    main()
