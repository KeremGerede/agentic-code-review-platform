"""
Agentic AI Code Review Test File - Python / FastAPI

Bu dosya GitHub push sonrası AI Code Review sistemini test etmek için
bilerek hatalı yazılmıştır.

Her hatanın üzerinde yorum satırı olarak açıklama bulunmaktadır.

NOT:
Buradaki API key, token, password ve secret değerleri tamamen sahte test verileridir.
Gerçek gizli bilgi kullanma.
"""

import sqlite3
import requests
from fastapi import FastAPI, Request

app = FastAPI()


# HATA 1: Hardcoded API key.
# Beklenen bulgu:
# - API key, token veya secret gibi değerler kaynak koda yazılmamalı.
# - .env veya secret manager üzerinden okunmalı.
PAYMENT_API_KEY = "fake_payment_api_key_123456789"


# HATA 2: Hardcoded JWT secret.
# Beklenen bulgu:
# - JWT secret kaynak koda yazılmamalı.
# - Ortam değişkeni veya güvenli secret yönetimi kullanılmalı.
JWT_SECRET = "fake_jwt_secret_987654321"


# HATA 3: Hardcoded database password.
# Beklenen bulgu:
# - Database credential bilgileri kaynak kodda tutulmamalı.
DB_PASSWORD = "fake_db_password_123"


# HATA 4: Ortam bağımlı database path hardcoded.
# Beklenen bulgu:
# - Production/local gibi ortam bilgileri config üzerinden yönetilmeli.
DB_PATH = "production.db"


@app.get("/users/search")
def search_users(username: str):
    # HATA 5: Debug print production kodunda bırakılmış.
    # Beklenen bulgu:
    # - print yerine structured logger kullanılmalı.
    # - Gereksiz debug çıktıları kaldırılmalı.
    print("DEBUG: searching username:", username)

    # HATA 6: Sensitive data loglanıyor.
    # Beklenen bulgu:
    # - Şifre, token, API key gibi hassas bilgiler loglanmamalı.
    print("DEBUG: database password:", DB_PASSWORD)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # HATA 7: SQL Injection riski.
    # Beklenen bulgu:
    # - Kullanıcı girdisi SQL query içine doğrudan eklenmiş.
    # - Parameterized query kullanılmalı.
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)

    rows = cursor.fetchall()
    connection.close()

    # HATA 8: Error handling yok.
    # Beklenen bulgu:
    # - Database bağlantısı veya query hataları try/except ile yönetilmeli.
    return {"data": rows}


@app.post("/payments")
async def create_payment(request: Request):
    # HATA 9: Input validation yok.
    # Beklenen bulgu:
    # - amount, user_id ve card_number alanları doğrulanmadan kullanılıyor.
    body = await request.json()

    amount = body["amount"]
    user_id = body["user_id"]
    card_number = body["card_number"]

    # HATA 10: Kart bilgisi gibi hassas veri loglanıyor.
    # Beklenen bulgu:
    # - Payment/card data loglanmamalı.
    print("DEBUG payment body:", body)

    # HATA 11: Controller/endpoint içinde business logic var.
    # Beklenen bulgu:
    # - İndirim hesaplama gibi iş kuralları service katmanına taşınmalı.
    if amount > 1000:
        discount = amount * 0.10
    else:
        discount = 0

    final_amount = amount - discount

    # HATA 12: Hardcoded authorization token/API key kullanımı.
    # Beklenen bulgu:
    # - Authorization bilgisi kod içinde olmamalı.
    # - Environment variable veya secret manager kullanılmalı.
    response = requests.post(
        "https://example-payment-provider.com/pay",
        headers={"Authorization": f"Bearer {PAYMENT_API_KEY}"},
        json={
            "user_id": user_id,
            "amount": final_amount,
            "card_number": card_number,
        },
        timeout=5,
    )

    # HATA 13: External API response için hata kontrolü yok.
    # Beklenen bulgu:
    # - response.status_code kontrol edilmeli.
    # - requests exceptions yakalanmalı.
    return response.json()


@app.post("/login")
async def login(request: Request):
    body = await request.json()

    email = body.get("email")
    password = body.get("password")

    # HATA 14: Plain text password karşılaştırması.
    # Beklenen bulgu:
    # - Şifreler hashlenmiş şekilde saklanmalı.
    # - bcrypt veya argon2 gibi güvenli yöntemler kullanılmalı.
    if email == "admin@example.com" and password == "admin123":
        # HATA 15: Sahte ve güvensiz token üretimi.
        # Beklenen bulgu:
        # - Güvenli JWT kütüphanesi ve doğru expiration kullanılmalı.
        token = f"fake-token-for-{email}-signed-with-{JWT_SECRET}"
        return {"token": token}

    return {"message": "Invalid credentials"}


# HATA 16: Duplicate validation logic - birinci kopya.
# Beklenen bulgu:
# - Aynı validasyon mantığı tekrar edilmemeli.
# - Ortak reusable validator fonksiyonuna taşınmalı.
def validate_register_input_v1(email: str, password: str) -> bool:
    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False
    return True


# HATA 17: Duplicate validation logic - ikinci kopya.
# Beklenen bulgu:
# - validate_register_input_v1 ile aynı mantık tekrar edilmiş.
# - Code duplication var.
def validate_register_input_v2(email: str, password: str) -> bool:
    if email is None or email == "":
        return False
    if "@" not in email:
        return False
    if password is None or password == "":
        return False
    if len(password) < 8:
        return False
    return True


# HATA 18: Çok fazla sorumluluğu olan fonksiyon.
# Beklenen bulgu:
# - Toplam hesaplıyor.
# - Vergi hesaplıyor.
# - Ödeme durumunu belirliyor.
# - Bildirim gönderiyor.
# - Log basıyor.
# - Single Responsibility Principle'a aykırı.
def calculate_order_and_notify_user(user, order, payment, notification_service):
    total = 0

    for item in order["items"]:
        total += item["price"] * item["quantity"]

    # HATA 19: Magic number kullanımı.
    # Beklenen bulgu:
    # - 0.90, 1.20, 1.19 gibi değerler named constant veya config olarak tanımlanmalı.
    if user["type"] == "premium":
        total = total * 0.90

    if user["country"] == "TR":
        total = total * 1.20
    elif user["country"] == "DE":
        total = total * 1.19
    else:
        total = total * 1.10

    # HATA 20: Payment logic doğrudan fonksiyon içinde.
    # Beklenen bulgu:
    # - Payment işlemleri ayrı service veya strategy yapısına taşınmalı.
    if payment["method"] == "credit_card":
        payment_status = "paid"
    elif payment["method"] == "bank_transfer":
        payment_status = "pending"
    else:
        payment_status = "failed"

    notification_service.send_email(
        user["email"],
        "Order Update",
        f"Your order total is {total} and payment status is {payment_status}",
    )

    notification_service.send_sms(
        user["phone"],
        f"Order {order['id']} status: {payment_status}",
    )

    # HATA 21: print ile loglama.
    # Beklenen bulgu:
    # - print yerine structured logger kullanılmalı.
    print(f"User {user['id']} order {order['id']} processed with total {total}")

    return {
        "total": total,
        "payment_status": payment_status,
    }


@app.get("/debug/env")
def debug_environment():
    # HATA 22: Production ortamında debug endpoint açık.
    # Beklenen bulgu:
    # - Ortam bilgileri public endpoint üzerinden açığa çıkarılmamalı.
    return {
        "environment": "production",
        "database_path": DB_PATH,
        "payment_api_key_exists": PAYMENT_API_KEY is not None,
    }


print("AAAAAAAAH şifrem: 123123")