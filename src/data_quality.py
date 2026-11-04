
from datetime import date, datetime
from math import isfinite


def validate_order_amount(amount):
    """Check whether an order amount is valid."""

    if amount is None:
        return False, "Order amount is missing."

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return False, "Order amount must be numeric."

    if not isfinite(amount):
        return False, "Order amount must be a finite number."

    if amount < 0:
        return False, "Order amount cannot be negative."

    return True, "Valid order amount."


def validate_order_status(status):
    """Check whether an order status is allowed."""

    allowed_statuses = [
        "Pending",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status is None or not isinstance(status, str) or not status.strip():
        return False, "Order status is missing."

    if status not in allowed_statuses:
        return False, f"Invalid order status: {status}"

    return True, "Valid order status."


def validate_order_id(order_id):
    """Check whether an order ID is present."""

    if order_id is None or str(order_id).strip() == "":
        return False, "Order ID is missing."

    return True, "Valid order ID."


def validate_order_date(order_date):
    """Validate order date when it is provided."""

    if order_date is None:
        return True, "Order date not provided."

    if not isinstance(order_date, (date, datetime)):
        return False, "Order date must be a valid date or timestamp."

    return True, "Valid order date."


def validate_discount(discount):
    """Check whether discount is between 0 and 100."""

    if discount is None:
        return True, "Valid optional discount."

    if isinstance(discount, bool) or not isinstance(discount, (int, float)):
        return False, "Discount must be numeric."

    if not isfinite(discount):
        return False, "Discount must be a finite number."

    if discount < 0 or discount > 100:
        return False, "Discount must be between 0 and 100."

    return True, "Valid discount."


def find_duplicate_order_ids(order_ids):
    """Find order IDs that appear more than once."""

    seen = set()
    duplicates = set()

    for order_id in order_ids:
        if order_id is None or str(order_id).strip() == "":
            continue

        if order_id in seen:
            duplicates.add(order_id)
        else:
            seen.add(order_id)

    return duplicates


def validate_customer_reference(order, customer_ids):
    """Check whether an order references an existing customer."""

    customer_id = order.get("customer_id")

    if customer_id is None:
        return False, "Customer ID is missing."

    if customer_id not in customer_ids:
        return False, f"Customer ID {customer_id} does not exist."

    return True, "Valid customer reference."


def validate_order_record(order, customer_ids=None):
    """Validate one complete order record."""

    errors = []

    checks = [
        validate_order_id(order.get("order_id")),
        validate_order_amount(order.get("amount")),
        validate_order_status(order.get("status")),
        validate_order_date(order.get("order_date")),
        validate_discount(order.get("discount"))
    ]

    for is_valid, message in checks:
        if not is_valid:
            errors.append(message)

    if customer_ids is not None:
        is_valid, message = validate_customer_reference(
            order, customer_ids
        )

        if not is_valid:
            errors.append(message)

    if errors:
        return {
            "status": "REJECTED",
            "errors": errors
        }

    return {
        "status": "ACCEPTED",
        "errors": []
    }


def separate_valid_and_invalid_orders(orders, customer_ids=None):
    """Separate valid and invalid orders and detect duplicates."""

    valid_orders = []
    invalid_orders = []
    seen_order_ids = set()

    for order in orders:
        order_id = order.get("order_id")

        is_duplicate = (
            order_id is not None
            and str(order_id).strip() != ""
            and order_id in seen_order_ids
        )

        # Track IDs even when their first record is invalid.
        if order_id is not None and str(order_id).strip() != "":
            seen_order_ids.add(order_id)

        result = validate_order_record(order, customer_ids)

        if is_duplicate:
            result["status"] = "REJECTED"
            result["errors"].append("Duplicate order ID.")

        if result["status"] == "REJECTED":
            invalid_orders.append({
                "record": order,
                "errors": result["errors"]
            })
        else:
            valid_orders.append(order)

    return valid_orders, invalid_orders
