import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Fix DNS resolution for mongodb+srv on Windows where router DNS drops SRV queries
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']
except Exception:
    pass

# Connect to MongoDB
MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://admin:harish123@cluster0.cfoj6si.mongodb.net/barcodedb?retryWrites=true&w=majority&appName=Cluster0'
DB_NAME = os.environ.get('DB_NAME', 'barcodedb')

print(f"Connecting to MongoDB database: {DB_NAME}...")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
db = client[DB_NAME]

# Ping database to verify connection
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

# --- Products Data ---
products_data = [
    {"barcodedata": "3010000012191", "product_name": "Maaza juice", "product_price": 60.00, "quantity": 10, "image": "/static/images/2.jpeg"},
    {"barcodedata": "3010000018797", "product_name": "Maaza juice", "product_price": 60.00, "quantity": 10, "image": "/static/images/2.jpeg"},
    {"barcodedata": "8901491101837", "product_name": "Lays", "product_price": 5.00, "quantity": 25, "image": "/static/images/1.jpeg"},
    {"barcodedata": "6291007901047", "product_name": "Good Day biscuit", "product_price": 10.00, "quantity": 30, "image": "/static/images/4.jpeg"},
    {"barcodedata": "6297001907047", "product_name": "Good Day biscuit", "product_price": 10.00, "quantity": 30, "image": "/static/images/4.jpeg"},
    {"barcodedata": "8901063164291", "product_name": "Tiger biscuit", "product_price": 10.00, "quantity": 20, "image": "/static/images/3.jpeg"},
    {"barcodedata": "8901063092716", "product_name": "Good Day biscuit", "product_price": 10.00, "quantity": 15, "image": "/static/images/4.jpeg"},
    {"barcodedata": "8904043901015", "product_name": "Tata salt 1kg", "product_price": 25.00, "quantity": 40, "image": "/static/images/5.jpeg"},
    {"barcodedata": "8906010261078", "product_name": "Gold winner sunflower oil 1L", "product_price": 190.00, "quantity": 12, "image": "/static/images/6.jpeg"},
    {"barcodedata": "8901725132873", "product_name": "Dark Fantasy Choco Fills Luxuria", "product_price": 128.00, "quantity": 18, "image": "/static/images/7.jpeg"},
    {"barcodedata": "8901725017927", "product_name": "Sunfeast YiPPee Family pack", "product_price": 153.00, "quantity": 22, "image": "/static/images/8.jpeg"},
    {"barcodedata": "6001067021995", "product_name": "Colgate MaxFresh Toothpaste", "product_price": 72.00, "quantity": 15, "image": "/static/images/9.jpeg"},
    {"barcodedata": "8901207027437", "product_name": "Dabur Honey - 1kg", "product_price": 391.00, "quantity": 8, "image": "/static/images/10.jpeg"},
    {"barcodedata": "8901287400991", "product_name": "Mysore Sandal Soap 450g", "product_price": 232.00, "quantity": 14, "image": "/static/images/11.jpeg"},
    {"barcodedata": "6161100950900", "product_name": "Harpic 1 Litre (Pack of 2)", "product_price": 396.00, "quantity": 10, "image": "/static/images/12.jpg"},
    {"barcodedata": "8901088203630", "product_name": "Parachute Coconut Oil", "product_price": 126.00, "quantity": 20, "image": "/static/images/13.jpg"},
    {"barcodedata": "8901399111013", "product_name": "Santoor Soap (Pack of 4)", "product_price": 163.00, "quantity": 16, "image": "/static/images/14.jpg"},
    {"barcodedata": "8901030602983", "product_name": "Kellogg’s Choco Flakes 1kg", "product_price": 229.00, "quantity": 9, "image": "/static/images/23.jpeg"},
    {"barcodedata": "8901399336812", "product_name": "Softouch 2X French Perfume 2L Fabric Conditioner", "product_price": 345.00, "quantity": 7, "image": "/static/images/24.jpeg"},
    {"barcodedata": "8901063017221", "product_name": "Britannia 50-50 Maska Chaska 105g", "product_price": 28.00, "quantity": 35, "image": "/static/images/25.jpg"}
]

print("Seeding products (upserting to avoid wiping custom data)...")
for p in products_data:
    db.products.update_one(
        {"barcodedata": p["barcodedata"]},
        {"$set": p},
        upsert=True
    )
print(f"Upserted {len(products_data)} products.")

# --- Users Data with clear Werkzeug password hashing ---
users_to_seed = [
    {"username": "Lokesh25", "password_raw": "Lokesh@123", "email": "mlokeshprasanna@gmail.com"},
    {"username": "lokesh", "password_raw": "Lokesh@123", "email": "lokesh@gmail.com"},
    {"username": "harish", "password_raw": "Harish@123", "email": "harish@gmail.com"},
    {"username": "admin", "password_raw": "Admin@123", "email": "admin@gmail.com"},
    {"username": "girish", "password_raw": "Girish@123", "email": "girish@gmail.com"},
    {"username": "sakthi", "password_raw": "Sakthi@123", "email": "sakthi@gmail.com"},
    {"username": "ajith", "password_raw": "Ajith@123", "email": "ajithkumar@gmail.com"},
    {"username": "mathesh", "password_raw": "Mathesh@123", "email": "mathesh@gmail.com"},
    {"username": "leo", "password_raw": "Leo@123", "email": "leo@gmail.com"},
]

print("\nSeeding user accounts (using werkzeug.security.generate_password_hash)...")
for u in users_to_seed:
    hashed_pw = generate_password_hash(u["password_raw"])
    db.users.update_one(
        {"username": {"$regex": f"^{u['username']}$", "$options": "i"}},
        {
            "$set": {
                "username": u["username"],
                "password": hashed_pw,
                "email": u["email"],
                "updated_at": datetime.now()
            },
            "$setOnInsert": {
                "created_at": datetime.now()
            }
        },
        upsert=True
    )

print("Seeding complete! Available test accounts:")
print("--------------------------------------------------")
for u in users_to_seed:
    print(f"Username: {u['username']:<12} | Password: {u['password_raw']:<12} | Email: {u['email']}")
print("--------------------------------------------------")
