"""
Agentic Code Review Test File

This file intentionally contains security, code quality, architecture,
and maintainability problems so your GitHub code review agent can detect them.

IMPORTANT:
All secrets below are fake test values. Do not use real API keys or passwords.
"""

import sqlite3
import requests
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify

app = Flask(__name__)

# Intentional issue: hardcoded secret/API key
API_KEY = "fake_api_key_123456789"
DATABASE_PASSWORD = "fake_password_123"

DB_PATH = "production.db"


@app.route("/users/search", methods=["GET"])
def search_users():
    """
    Intentional issues:
    - Business logic inside controller/route
    - SQL injection risk
    - No proper error handling
    - Sensitive data logging
    - Debug print left in code
    """
    username = request.args.get("username")

    print("DEBUG: searching user:", username)
    print("DEBUG: database password:", DATABASE_PASSWORD)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Intentional issue: unsafe string formatting in SQL query
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    return jsonify({"data": rows})


@app.route("/payments", methods=["POST"])
def create_payment():
    """
    Intentional issues:
    - Controller contains business logic
    - No input validation
    - No error handling
    - External API token is hardcoded
    """
    data = request.json

    amount = data["amount"]
    user_id = data["user_id"]
    card_number = data["card_number"]

    print("DEBUG payment data:", data)

    if amount > 1000:
        discount = amount * 0.10
    else:
        discount = 0

    final_amount = amount - discount

    response = requests.post(
        "https://example-payment-provider.com/pay",
        headers={"Authorization": "Bearer fake_payment_token_987654321"},
        json={
            "user_id": user_id,
            "amount": final_amount,
            "card_number": card_number,
        },
        timeout=5,
    )

    return jsonify(response.json())


def very_long_function_with_multiple_responsibilities(user, order, payment, notification_service):
    """
    Intentional issue:
    This function does too many things and should be split into smaller functions.
    """
    total = 0

    for item in order["items"]:
        total += item["price"] * item["quantity"]

    if user["type"] == "premium":
        total = total * 0.90

    if user["country"] == "TR":
        total = total * 1.20
    elif user["country"] == "DE":
        total = total * 1.19
    elif user["country"] == "FR":
        total = total * 1.20
    else:
        total = total * 1.10

    if payment["method"] == "credit_card":
        print("Processing credit card payment")
        payment_status = "paid"
    elif payment["method"] == "bank_transfer":
        print("Processing bank transfer")
        payment_status = "pending"
    elif payment["method"] == "crypto":
        print("Processing crypto payment")
        payment_status = "paid"
    else:
        payment_status = "failed"

    if payment_status == "paid":
        order["status"] = "confirmed"
    elif payment_status == "pending":
        order["status"] = "waiting_payment"
    else:
        order["status"] = "cancelled"

    email_subject = "Order Update"
    email_body = f"Your order status is {order['status']}"

    notification_service.send_email(user["email"], email_subject, email_body)

    sms_message = f"Order {order['id']} status: {order['status']}"
    notification_service.send_sms(user["phone"], sms_message)

    log_message = f"User {user['id']} order {order['id']} status changed to {order['status']}"
    print(log_message)

    return {
        "total": total,
        "payment_status": payment_status,
        "order_status": order["status"],
    }


def duplicated_validation_one(email, password):
    """Intentional issue: duplicate validation logic."""
    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False
    return True


def duplicated_validation_two(email, password):
    """Intentional issue: same logic duplicated from duplicated_validation_one."""
    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False
    return True


if __name__ == "__main__":
    # Intentional issue: debug mode enabled
    app.run(debug=True)
