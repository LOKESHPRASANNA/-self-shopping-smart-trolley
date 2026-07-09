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
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Global State & Setup ---
app = Flask(__name__)
app.secret_key = 'your_super_secure_secret_key' # Use a strong key sessions
# CORS Setup: Must specify exact origins for credentials (cookies) to work
CORS(app, supports_credentials=True, origins=["http://localhost:5173", re.compile(r"https://.*\.vercel\.app")])

app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://127.0.0.1:27017/'
DB_NAME = 'barcodedb'

# --- Utility Function for Database Connection ---
def get_db():
    try:
        client = MongoClient(MONGO_URI)
        return client[DB_NAME]
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "SnapShop API is running", "environment": "Vercel"})

# --- Cart Helper Functions ---
def get_cart_for_user():
    # ... logic using session or user_id ...
    # Note: Sessions across domains (Frontend on Vercel -> Backend on Vercel) require careful cookie settings (SameSite=None, Secure).
    # For simplicity, we might assume the frontend sends a custom header 'X-User-ID' or similar if cookies fail, 
    # but let's try standard session first.
    if 'username' not in session:
        return {'products': [], 'total_price': 0.0}
    
    db = get_db()
    if db is None: return {'products': [], 'total_price': 0.0}

    username = session['username']
    cart = db.carts.find_one({"username": username})
    
    if not cart:
         return {'products': [], 'total_price': 0.0}
    
    return cart

def update_cart_in_db(products, total_price):
    if 'username' not in session:
        return
    
    db = get_db()
    if db is None: return

    username = session['username']
    db.carts.update_one(
        {"username": username},
        {"$set": {"products": products, "total_price": total_price, "updated_at": datetime.now()}},
        upsert=True
    )


# --- Routes ---

@app.route('/api/scan-item', methods=['POST'])
def scan_item():
    """API endpoint to handle barcode scan from frontend."""
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
        
    data = request.json
    barcode = data.get('barcode').strip()
    
    db = get_db()
    product = db.products.find_one({"barcodedata": barcode})
    
    if not product:
         return jsonify({"status": "error", "message": "Product not found"})
    
    try:
        # Get current cart
        cart = get_cart_for_user()
        current_products = cart.get('products', [])
        
        # Check if item exists in cart
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
                print(f"Price conversion error for {product['product_name']}: {product['product_price']}")
                price = 0.0 # Fallback
                
            current_products.append({
                "name": product['product_name'],
                "price": price,
                "quantity": 1
            })
            
        # Recalculate total
        total_price = sum(float(p['price']) * int(p['quantity']) for p in current_products)
        
        # Save back to DB
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
    if 'username' not in session: return jsonify({"status": "error"}), 401
    
    data = request.json
    product_name = data.get('product_name')
    
    try:
        cart = get_cart_for_user()
        current_products = cart.get('products', [])
        
        # Filter out the item to remove
        new_products = [p for p in current_products if p['name'] != product_name]
        
        # Recalculate total
        total_price = sum(float(p['price']) * int(p['quantity']) for p in new_products)
        
        update_cart_in_db(new_products, total_price)
        
        return jsonify({"status": "success", "message": "Item removed"})
    except Exception as e:
        print(f"Remove error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_scanning():
    # Only useful if we want to CLEAR the cart
    if 'username' in session:
         update_cart_in_db([], 0.0)
    return jsonify({"status": "Cart cleared"})

@app.route('/')
def home():
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    return redirect(url_for('login'))

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handles raw JSON from axios (react) OR form data (html)
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
            
        try:
            account = db.users.find_one({"username": username})

            if account and check_password_hash(account['password'], password):
                session['loggedin'] = True
                session['username'] = account['username']
                return jsonify({"status": "success"}) if request.is_json else redirect(url_for('home_page'))
            else:
                msg = 'Invalid credentials'
                return jsonify({"status": "error", "message": msg}) if request.is_json else render_template('login.html', error=msg)
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({"status": "error", "message": "Database authentication or connection error"}), 500

    return render_template('login.html')

@app.route('/home')
def home_page():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            
        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
            
        hashed_password = generate_password_hash(password)
        
        try:
            if db.users.find_one({"username": username}):
                 return jsonify({"status": "error", "message": "User exists"}) if request.is_json else "User exists"
                 
            db.users.insert_one({
                "username": username,
                "password": hashed_password,
                "email": email,
                "created_at": datetime.now()
            })
            
            return jsonify({"status": "success"}) if request.is_json else redirect(url_for('login'))
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({"status": "error", "message": "Database authentication or connection error"}), 500
        
    return render_template('register.html')

# Stock/Sales Routines (kept relatively same)
@app.route('/api/stock')
def get_stock():
    db = get_db()
    stock_data = list(db.products.find({}, {'_id': 0}))
    return jsonify(stock_data)

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    db = get_db()
    results = []
    if db is not None:
        # Simple regex search
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
        
    data = request.json
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
            
    # Also fetch the user's cart if logged in to provide more context
    cart_context = "User's Cart: Empty"
    if 'username' in session and db is not None:
        cart = db.carts.find_one({"username": session['username']})
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
            if msg['sender'] == 'ai' and len(contents) == 0:
                continue
            role = "user" if msg['sender'] == 'user' else "model"
            contents.append({"role": role, "parts": [{"text": msg['text']}]})
            
        last_message = history[-1]['text']
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

# --- Vercel requires app to be exported as 'app' or 'application' ---

if __name__ == '__main__':
    app.run(debug=True, port=5003)
