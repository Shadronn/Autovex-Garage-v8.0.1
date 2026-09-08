from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import uuid


MONEY_PLACES = Decimal("0.01")


def money(value):
    """Convert numbers to two-decimal Decimal values for payment math."""
    if value is None or value == "":
        return Decimal("0.00")
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def parse_payment_amount(value):
    try:
        amount = money(value)
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid payment amount.")

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    return amount


def generate_receipt_number(invoice_id):
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"RCT-{date_part}-{invoice_id:05d}-{random_part}"


def total_paid(payments):
    return sum((money(payment.amount) for payment in payments), Decimal("0.00"))


def balance_due(invoice, payments=None):
    payments = payments if payments is not None else getattr(invoice, "payments", [])
    balance = money(invoice.total_amount) - total_paid(payments)
    return max(balance, Decimal("0.00"))


def refresh_invoice_payment_status(invoice, payments=None):
    payments = payments if payments is not None else getattr(invoice, "payments", [])
    paid_total = total_paid(payments)
    remaining = max(money(invoice.total_amount) - paid_total, Decimal("0.00"))

    invoice.amount = float(paid_total)
    invoice.Balance = float(remaining)

    if remaining == 0:
        invoice.status = "Paid"
        paid_dates = [payment.paid_at for payment in payments if payment.paid_at]
        invoice.paid_at = max(paid_dates) if paid_dates else datetime.utcnow()
    elif paid_total > 0:
        invoice.status = "Partially Paid"
        invoice.paid_at = None
    else:
        invoice.status = "Unpaid"
        invoice.paid_at = None

    return invoice
