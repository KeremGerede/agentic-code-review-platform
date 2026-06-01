"""
Agentic AI Code Review Test File

Bu dosya, GitHub push sonrası AI Code Review sistemini test etmek için
bilerek hatalı yazılmıştır.

Yorum satırlarında her hatanın ne olduğu özellikle belirtilmiştir.

NOT:
Buradaki API key, token ve password değerleri tamamen sahte test verileridir.
Gerçek gizli bilgi kullanma.
"""

import sqlite3
import requests
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify

app = Flask(__name__)


# HATA 1: Hardcoded API key.
# Beklenen bulgu:
# - Secrets, API key, token veya password gibi değerler kod içine yazılmamalı.
# - Bu değerler .env dosyasından veya güvenli secret manager üzerinden okunmalı.
API_KEY = "fake_api_key_123456789"


# HATA 2: Hardcoded database password.
# Beklenen bulgu:
# - Şifre doğrudan kaynak koda yazılmış.
# - Bu güvenlik riski oluşturur.
DATABASE_PASSWORD = "fake_database_password_123"


# HATA 3: Production database path kod içine yazılmış.
# Beklenen bulgu:
# - Ortam bağımlı ayarlar kod içinde hardcoded olmamalı.
DB_PATH = "production.db"


@app.route("/users/search", methods=["GET"])
def search_users():
    """
    Bu endpoint kullanıcı araması yapıyor gibi görünür,
    ancak içinde birçok bilinçli hata vardır.
    """

    username = request.args.get("username")

    # HATA 4: Debug print production kodunda bırakılmış.
    # Beklenen bulgu:
    # - print/debug logları production kodunda kalmamalı.
    print("DEBUG: searching user:", username)

    # HATA 5: Sensitive data loglanıyor.
    # Beklenen bulgu:
    # - Şifre, token, API key gibi hassas veriler loglanmamalı.
    print("DEBUG: database password:", DATABASE_PASSWORD)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # HATA 6: SQL Injection riski.
    # Beklenen bulgu:
    # - Kullanıcı girdisi doğrudan SQL query içine eklenmiş.
    # - Parameterized query kullanılmalı.
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    # HATA 7: Error handling yok.
    # Beklenen bulgu:
    # - Database bağlantısı, query hatası veya invalid input için try/except yok.
    return jsonify({"data": rows})


@app.route("/payments", methods=["POST"])
def create_payment():
    """
    Bu endpoint ödeme oluşturuyor gibi görünür,
    ancak controller içinde business logic ve güvenlik açıkları vardır.
    """

    data = request.json

    # HATA 8: Input validation yok.
    # Beklenen bulgu:
    # - amount, user_id, card_number gibi alanlar doğrulanmadan kullanılıyor.
    amount = data["amount"]
    user_id = data["user_id"]
    card_number = data["card_number"]

    # HATA 9: Kart bilgisi gibi hassas veri loglanıyor.
    # Beklenen bulgu:
    # - Payment/card data loglanmamalı.
    print("DEBUG payment data:", data)

    # HATA 10: Controller içinde business logic var.
    # Beklenen bulgu:
    # - Discount hesaplama gibi iş kuralları route/controller içinde olmamalı.
    # - Service katmanına taşınmalı.
    if amount > 1000:
        discount = amount * 0.10
    else:
        discount = 0

    final_amount = amount - discount

    # HATA 11: Hardcoded bearer token.
    # Beklenen bulgu:
    # - Authorization token kod içine yazılmamalı.
    # - Environment variable veya secret manager kullanılmalı.
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

    # HATA 12: External API response için hata kontrolü yok.
    # Beklenen bulgu:
    # - response status code kontrol edilmiyor.
    # - requests exceptions yakalanmıyor.
    return jsonify(response.json())


def calculate_order_total_and_notify_user(user, order, payment, notification_service):
    """
    HATA 13: Bu fonksiyon çok fazla sorumluluğa sahip.

    Beklenen bulgu:
    - Toplam hesaplıyor.
    - Vergi hesaplıyor.
    - Ödeme durumunu belirliyor.
    - Sipariş durumunu güncelliyor.
    - E-posta gönderiyor.
    - SMS gönderiyor.
    - Log basıyor.
    - Bu yapı Single Responsibility Principle'a aykırı.
    """

    total = 0

    for item in order["items"]:
        total += item["price"] * item["quantity"]

    # HATA 14: Magic number kullanımı.
    # Beklenen bulgu:
    # - 0.90, 1.20, 1.19 gibi değerler sabit olarak kod içine yazılmış.
    # - Named constant veya config kullanılmalı.
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

    # HATA 15: Payment logic doğrudan fonksiyon içinde.
    # Beklenen bulgu:
    # - Ödeme yöntemi işleme ayrı bir service veya strategy yapısına ayrılmalı.
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

    # HATA 16: print ile loglama.
    # Beklenen bulgu:
    # - print yerine structured logger kullanılmalı.
    log_message = f"User {user['id']} order {order['id']} status changed to {order['status']}"
    print(log_message)

    return {
        "total": total,
        "payment_status": payment_status,
        "order_status": order["status"],
    }


def validate_user_input_v1(email, password):
    """
    HATA 17: Duplicate validation logic - birinci kopya.

    Beklenen bulgu:
    - Aynı validasyon mantığı başka fonksiyonda tekrar edilmiş.
    - Ortak reusable validation fonksiyonuna taşınmalı.
    """

    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False

    return True


def validate_user_input_v2(email, password):
    """
    HATA 18: Duplicate validation logic - ikinci kopya.

    Beklenen bulgu:
    - validate_user_input_v1 ile aynı mantık tekrar edilmiş.
    - Code duplication var.
    """

    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False

    return True


def get_user_profile(user_id):
    """
    HATA 19: Kullanıcı girdisiyle güvenli olmayan URL oluşturma riski.

    Beklenen bulgu:
    - user_id validate edilmeden external URL içine eklenmiş.
    - SSRF veya hatalı request riskleri değerlendirilmeli.
    """

    url = f"https://internal-api.example.com/users/{user_id}"
    response = requests.get(url, timeout=5)
    return response.json()


if __name__ == "__main__":
    # HATA 20: Flask debug mode açık.
    # Beklenen bulgu:
    # - Production ortamında debug=True kullanılmamalı.
    app.run(debug=True)
