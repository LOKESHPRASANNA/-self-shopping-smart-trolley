from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, url_for, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import qrcode
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime
import os
import random
from dotenv import load_dotenv
import requests

# Fix DNS resolution for mongodb+srv ONLY on Windows where local router DNS drops SRV queries
# On Linux (Render), keep the system default resolver from /etc/resolv.conf
if os.name == 'nt':
    try:
        import dns.resolver
        dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
        dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']
    except Exception:
        pass

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Global State & Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-me-secret-key-123')

# Determine environment
is_production = (
    os.environ.get('RENDER') == 'true'
    or os.environ.get('VERCEL') == '1'
    or os.environ.get('COOKIE_SECURE', '').lower() == 'true'
    or os.environ.get('FLASK_ENV') == 'production'
)

# CORS Setup: Allow local development, Render, Vercel, and configured frontend origins
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5003",
    "http://127.0.0.1:5003",
    re.compile(r"^https:\/\/.*\.onrender\.com$"),
    re.compile(r"^https:\/\/.*\.vercel\.app$"),
]
extra_origins = os.environ.get('FRONTEND_URL', '')
if extra_origins:
    for origin in extra_origins.split(','):
        cleaned = origin.strip()
        if cleaned:
            allowed_origins.append(cleaned)

CORS(app, supports_credentials=True, origins=allowed_origins)

app.config.update(
    SESSION_COOKIE_SECURE=is_production,
    SESSION_COOKIE_SAMESITE='None' if is_production else 'Lax',
    SESSION_COOKIE_HTTPONLY=True
)

# MongoDB configuration
PRIMARY_MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://admin:harish123@cluster0.cfoj6si.mongodb.net/barcodedb?retryWrites=true&w=majority&appName=Cluster0'
DIRECT_MONGO_URI = 'mongodb://admin:harish123@ac-kbakxgz-shard-00-00.cfoj6si.mongodb.net:27017,ac-kbakxgz-shard-00-01.cfoj6si.mongodb.net:27017,ac-kbakxgz-shard-00-02.cfoj6si.mongodb.net:27017/barcodedb?ssl=true&replicaSet=atlas-rmgzlh-shard-0&authSource=admin&retryWrites=true&w=majority'
DB_NAME = os.environ.get('DB_NAME', 'barcodedb')

_mongo_client = None
_last_db_error = None

# --- Utility Function for Database Connection ---
def get_db():
    global _mongo_client, _last_db_error
    if _mongo_client is not None:
        try:
            return _mongo_client[DB_NAME]
        except Exception:
            _mongo_client = None

    # First attempt: Connect using primary URI
    try:
        client = MongoClient(
            PRIMARY_MONGO_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            maxPoolSize=50
        )
        client.admin.command('ping')
        _mongo_client = client
        _last_db_error = None
        return _mongo_client[DB_NAME]
    except Exception as e1:
        _last_db_error = str(e1)
        print(f"Primary MongoDB connection failed: {e1}")

    # Fallback attempt: Connect using direct non-SRV replica set URI (bypasses SRV/DNS issues)
    if 'mongodb+srv://' in PRIMARY_MONGO_URI:
        try:
            print("Attempting direct replica set fallback...")
            client = MongoClient(
                DIRECT_MONGO_URI,
                serverSelectionTimeoutMS=8000,
                connectTimeoutMS=8000,
                maxPoolSize=50
            )
            client.admin.command('ping')
            _mongo_client = client
            _last_db_error = None
            print("Direct replica set connection succeeded!")
            return _mongo_client[DB_NAME]
        except Exception as e2:
            _last_db_error = f"Primary: {e1} | Fallback: {e2}"
            print(f"Direct MongoDB fallback failed: {e2}")

    return None

def get_current_user():
    """Retrieve authenticated username from session or X-Username header for cross-domain resilience."""
    if 'username' in session and session.get('loggedin'):
        return session['username']
    header_user = request.headers.get('X-Username')
    if header_user:
        return header_user.strip()
    return None

# --- Health Check ---
@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    db = get_db()
    return jsonify({
        "status": "SnapShop API is running",
        "database": "connected" if db is not None else "unavailable",
        "database_error": _last_db_error if db is None else None,
        "environment": "production" if is_production else "development"
    })

# --- Cart Helper Functions ---
def get_cart_for_user():
    username = get_current_user()
    if not username:
        return {'products': [], 'total_price': 0.0}
    
    db = get_db()
    if db is None:
        return {'products': [], 'total_price': 0.0}

    cart = db.carts.find_one({"username": username})
    if not cart:
        return {'products': [], 'total_price': 0.0}
    
    return cart

def update_cart_in_db(products, total_price):
    username = get_current_user()
    if not username:
        return
    
    db = get_db()
    if db is None:
        return

    db.carts.update_one(
        {"username": username},
        {"$set": {"products": products, "total_price": total_price, "updated_at": datetime.now()}},
        upsert=True
    )

# --- Routes ---

@app.route('/api/scan-item', methods=['POST'])
def scan_item():
    """API endpoint to handle barcode scan from frontend."""
    username = get_current_user()
    if not username:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
        
    data = request.json or {}
    barcode = str(data.get('barcode', '')).strip()
    
    db = get_db()
    if db is None:
        return jsonify({"status": "error", "message": "Database unavailable"}), 503

    product = db.products.find_one({"barcodedata": barcode})
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404
    
    try:
        cart = get_cart_for_user()
        current_products = cart.get('products', [])
        
        found = False
        for p in current_products:
            if p['name'] == product['product_name']:
                p['quantity'] += 1
                found = True
                break
                
        if not found:
            try:
                price = float(product['product_price'])
            except (ValueError, TypeError):
                price = 0.0
                
            current_products.append({
                "name": product['product_name'],
                "price": price,
                "quantity": 1
            })
            
        total_price = sum(float(p['price']) * int(p['quantity']) for p in current_products)
        update_cart_in_db(current_products, total_price)
        
        return jsonify({"status": "success", "product": product['product_name']})
    except Exception as e:
        print(f"CRITICAL ERROR in scan_item: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-scanned-items', methods=['GET'])
def get_scanned_items():
    """Returns the user's cart."""
    cart = get_cart_for_user()
    return jsonify({"products": cart.get('products', []), "total_prize": cart.get('total_price', 0.0)})

@app.route('/api/remove-item', methods=['POST'])
def remove_item():
    username = get_current_user()
    if not username:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    data = request.json or {}
    product_name = data.get('product_name')
    
    try:
        cart = get_cart_for_user()
        current_products = cart.get('products', [])
        new_products = [p for p in current_products if p['name'] != product_name]
        total_price = sum(float(p['price']) * int(p['quantity']) for p in new_products)
        
        update_cart_in_db(new_products, total_price)
        return jsonify({"status": "success", "message": "Item removed"})
    except Exception as e:
        print(f"Remove error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_scanning():
    username = get_current_user()
    if username:
        update_cart_in_db([], 0.0)
    return jsonify({"status": "Cart cleared"})

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400

        username = username.strip()
        db = get_db()
        if db is None:
            return jsonify({"status": "error", "message": "Database unavailable. Please check MongoDB configuration."}), 503

        try:
            # Case-insensitive username lookup
            account = db.users.find_one({"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}})

            if account and check_password_hash(account['password'], password):
                session['loggedin'] = True
                session['username'] = account['username']
                return jsonify({
                    "status": "success",
                    "username": account['username'],
                    "email": account.get('email', '')
                }) if request.is_json else redirect(url_for('home_page'))
            else:
                msg = 'Invalid username or password'
                return jsonify({"status": "error", "message": msg}), 401 if request.is_json else render_template('login.html', error=msg)
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

    return render_template('login.html')

@app.route('/home')
def home_page():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"status": "success", "message": "Logged out successfully"})
    return redirect(url_for('login'))

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400

        username = username.strip()
        db = get_db()
        if db is None:
            return jsonify({"status": "error", "message": "Database unavailable"}), 503

        try:
            if db.users.find_one({"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}}):
                return jsonify({"status": "error", "message": "Username already exists"}), 409 if request.is_json else "Username already exists"

            hashed_password = generate_password_hash(password)
            db.users.insert_one({
                "username": username,
                "password": hashed_password,
                "email": email.strip() if email else None,
                "created_at": datetime.now()
            })
            
            return jsonify({"status": "success", "message": "Registration successful", "username": username}) if request.is_json else redirect(url_for('login'))
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({"status": "error", "message": f"Registration error: {str(e)}"}), 500
        
    return render_template('register.html')

# Stock & Product Management Routes
@app.route('/api/stock')
def get_stock():
    db = get_db()
    if db is None:
        return jsonify([])
    stock_data = list(db.products.find({}, {'_id': 0}))
    return jsonify(stock_data)

@app.route('/api/product/add', methods=['POST'])
def add_product():
    data = request.get_json() if request.is_json else request.form
    name = data.get('name')
    price = data.get('price')
    barcode = data.get('barcode', name)
    image_url = data.get('image_url', '/static/images/placeholder.svg')
    quantity = data.get('quantity', 1)

    if not name or price is None:
        return jsonify({"status": "error", "message": "Product name and price are required"}), 400

    db = get_db()
    if db is None:
        return jsonify({"status": "error", "message": "Database unavailable"}), 503

    try:
        db.products.update_one(
            {"product_name": name},
            {
                "$set": {
                    "product_name": name,
                    "product_price": float(price),
                    "barcodedata": str(barcode),
                    "image": image_url or '/static/images/placeholder.svg',
                    "quantity": int(quantity)
                }
            },
            upsert=True
        )
        return jsonify({"status": "Product added/updated successfully"})
    except Exception as e:
        print(f"Error adding product: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/product/remove', methods=['POST'])
def remove_product():
    data = request.get_json() if request.is_json else request.form
    barcode_or_name = data.get('barcode')

    if not barcode_or_name:
        return jsonify({"status": "error", "message": "Product identifier is required"}), 400

    db = get_db()
    if db is None:
        return jsonify({"status": "error", "message": "Database unavailable"}), 503

    try:
        res = db.products.delete_one({
            "$or": [
                {"barcodedata": str(barcode_or_name)},
                {"product_name": str(barcode_or_name)}
            ]
        })
        if res.deleted_count > 0:
            return jsonify({"status": "Product removed successfully"})
        else:
            return jsonify({"status": "error", "message": "Product not found"}), 404
    except Exception as e:
        print(f"Error removing product: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    db = get_db()
    results = []
    if db is not None:
        products = list(db.products.find({"product_name": {"$regex": query, "$options": "i"}}))
        seen_names = set()
        for p in products:
            name = p.get('product_name')
            if name not in seen_names:
                results.append({
                    "id": str(p.get('_id')),
                    "name": name,
                    "price": p.get('product_price'),
                    "image": p.get('image', '/static/images/placeholder.svg'),
                    "description": p.get('description', ''),
                    "location": p.get("location", "") 
                })
                seen_names.add(name)
    return jsonify(results)

@app.route('/api/recommended', methods=['GET'])
def recommended():
    db = get_db()
    if db is not None:
        pipeline = [{"$sample": {"size": 5}}]
        products_db = list(db.products.aggregate(pipeline))
        result = []
        for p in products_db:
            result.append({
                "name": p.get("product_name"),
                "price": p.get("product_price"),
                "image": p.get("image", "/static/images/placeholder.svg")
            })
        return jsonify(result)
    return jsonify([])

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        return jsonify({"status": "error", "message": "Gemini API Key is not configured in the backend"}), 500
        
    data = request.json or {}
    history = data.get('history', [])
    
    if not history:
        return jsonify({"status": "error", "message": "No chat history provided"}), 400
        
    db = get_db()
    products_context = ""
    if db is not None:
        products = list(db.products.find({}, {'_id': 0, 'product_name': 1, 'product_price': 1, 'location': 1}))
        products_context = "Current Products available:\n"
        for p in products:
            products_context += f"- {p.get('product_name')} : ₹{p.get('product_price')} (Location: {p.get('location', 'N/A')})\n"
            
    cart_context = "User's Cart: Empty"
    username = get_current_user()
    if username and db is not None:
        cart = db.carts.find_one({"username": username})
        if cart and cart.get('products'):
            cart_context = "User's Current Cart:\n"
            for item in cart['products']:
                cart_context += f"- {item['name']} (x{item['quantity']}) : ₹{item['price']}\n"
            cart_context += f"Total: ₹{cart.get('total_price')}"
        
    system_prompt = f"""You are SnapShop's Advanced AI Shopping Assistant. You are highly persuasive, helpful, and friendly.
Format your responses beautifully using Markdown (bold text for emphasis, bullet points for lists, etc.).

Role & Capabilities:
- Assist customers with finding products, checking prices, and navigating the store.
- **Offers & Discounts**: Actively promote our current offers! Tell them about "10% off on all biscuits", "Buy 2 get 1 free on beverages", and "Free home delivery on orders over ₹500".
- **Reviews**: Guide customers to the product section. If they ask about a product, simulate reviews (e.g., "This product is highly rated at 4.5/5 by our customers!"). Encourage them to leave their own review!
- Keep responses concise but highly engaging. Answer ONLY questions related to shopping, products, and SnapShop.

Here is the list of products in the store:
{products_context}

{cart_context}
"""

    try:
        contents = []
        for msg in history[:-1]:
            if msg.get('sender') == 'ai' and len(contents) == 0:
                continue
            role = "user" if msg.get('sender') == 'user' else "model"
            contents.append({"role": role, "parts": [{"text": msg.get('text', '')}]})
            
        last_message = history[-1].get('text', '')
        contents.append({"role": "user", "parts": [{"text": last_message}]})
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        api_resp = requests.post(url, json=payload, headers=headers, timeout=15)
        api_resp.raise_for_status()
        
        response_data = api_resp.json()
        ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({"status": "success", "response": ai_text})
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"status": "error", "message": "Failed to generate AI response"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port)
