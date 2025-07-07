from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime
import os

from gemini_utils import extract_receipt_info_gemini
from gemini_utils import extract_transactions_from_pdf

from config import MONGO_URI, DB_NAME, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, SECRET_KEY
from bson.objectid import ObjectId
from flask import jsonify



app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]  # Should be "finance_app"
users = db.users
transactions = db.transactions
receipts = db.receipts

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # ← This is enough


# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# File extension validation
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add')
def add():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('add.html')

@app.route('/profile')
def profile_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = users.find_one({"email": session['user']})
    return render_template('profile.html', user=user)

@app.route('/receipts')
def receipts_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_receipts = list(receipts.find({"user": session['user']}))
    return render_template('receipts.html', receipts=user_receipts)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/analysis')
def range_analysis_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('analysis.html')


@app.route('/')
def index():
    if 'user' not in session or 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_id = ObjectId(session['user_id'])
    except:
        return redirect(url_for('login'))

    user = users.find_one({'_id': user_id})
    if not user:
        return redirect(url_for('login'))

    user_transactions = list(transactions.find({'user_id': user_id}))

    total_income = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'income')
    total_expenses = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'expense')
    balance = total_income - total_expenses
    savings_rate = round((balance / total_income) * 100, 2) if total_income else 0

    return render_template(
        'index.html',
        user=user,
        income=round(total_income, 2),
        expenses=round(total_expenses, 2),
        balance=round(balance, 2),
        savings_rate=savings_rate
    )

@app.route('/force-logout')
def force_logout():
    session.clear()
    return "Session cleared. Now go to /"


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for('register'))

        if users.find_one({"email": email}):
            flash("User already exists.")
            return redirect(url_for('register'))

        users.insert_one({
            "name": name,
            "email": email,
            "password": password  # For extra security, hash this in production
        })

        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        user = users.find_one({"email": email})

        if not user:
            flash("User not found. Please register.")
            return redirect(url_for('register'))

        if user['password'] != password:
            flash("Incorrect password.")
            return redirect(url_for('login'))

        session['user'] = user['email']
        session['user_id'] = str(user['_id'])  # After successful login

        return redirect(url_for('index'))

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/upload-receipts', methods=['POST'])
def upload_receipts():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = ObjectId(session['user_id'])
    uploaded_files = request.files.getlist('file')
    results = []

    for file in uploaded_files:
        if not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            if filename.endswith('.pdf'):
                # Extract multiple transactions from PDF
                transactions_list = extract_transactions_from_pdf(filepath)

                for txn in transactions_list:
                    txn_doc = {
                        'user': session['user'],
                        'user_id': user_id,
                        'date': txn.get('date', datetime.today().strftime("%Y-%m-%d")),
                        'amount': float(txn.get('amount', 0)),
                        'description': txn.get('description', 'PDF Transaction'),
                        'type': txn.get('type', 'expense'),
                        'category': txn.get('category', 'PDF'),
                        'merchant': txn.get('merchant', 'Unknown'),
                        'created_at': datetime.utcnow()
                    }
                    transactions.insert_one(txn_doc)

                for txn in transactions_list:
                   results.append({
                    'filename': filename,
                    'text': "PDF Transaction Summary",
                    'parsed': {
                        'amount': txn.get('amount', 0),
                        'date': txn.get('date', '-'),
                        'description': txn.get('description', '-'),
                        'merchant': txn.get('merchant', 'Unknown')
        }
    })


            else:
                parsed = extract_receipt_info_gemini(filepath)
                transaction = {
                    'user_id': user_id,
                    'user': session['user'],
                    'date': parsed.get('date', datetime.today().strftime("%Y-%m-%d")),
                    'amount': float(parsed.get('amount', 0)),
                    'description': parsed.get('description', 'Receipt Transaction'),
                    'type': parsed.get('type', 'expense'),
                    'category': parsed.get('category', 'Receipt'),
                    'created_at': datetime.utcnow()
                }
                transactions.insert_one(transaction)

                receipts.insert_one({
                    "user": session["user"],
                    "user_id": user_id,
                    "filename": filename,
                    "parsed": parsed,
                    "upload_time": datetime.utcnow()
                })

                results.append({
                    'filename': filename,
                    'parsed': parsed,
                    'text': parsed.get('description', '')
                })

        except Exception as e:
            results.append({
                'filename': filename,
                'parsed': {},
                'text': f"❌ OCR failed: {str(e)}"
            })

    return jsonify({'results': results})




# Profile Page
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = users.find_one({"email": session['user']})
    return render_template('profile.html', user=user)

@app.route('/dashboard-data')
def dashboard_data():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_email = session['user']
    user_txns = list(transactions.find({"user": user_email}))

    if not user_txns:
        return jsonify({
            "income": 0,
            "expenses": 0,
            "balance": 0,
            "categories": {}
        })

    income = sum(txn['amount'] for txn in user_txns if txn['type'] == 'income')
    expenses = sum(txn['amount'] for txn in user_txns if txn['type'] == 'expense')
    balance = income - expenses

    category_breakdown = {}
    for txn in user_txns:
        cat = txn.get("category", "Others")
        category_breakdown[cat] = category_breakdown.get(cat, 0) + txn["amount"]

    return jsonify({
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "categories": category_breakdown
    })

@app.route('/transactions', methods=['GET', 'POST'])
def transactions_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.json
        transaction = {
            "user": session['user'],
            "user_id": ObjectId(session['user_id']),
            "type": data.get("type"),
            "amount": float(data.get("amount")),
            "description": data.get("description"),
            "category": data.get("category"),
            "date": data.get("date"),
            "created_at": datetime.utcnow()
        }
        transactions.insert_one(transaction)
        return jsonify({"success": True})

    user_id = ObjectId(session['user_id'])
    page = int(request.args.get('page', 1))
    per_page = 6
    skip = (page - 1) * per_page

    total_transactions = transactions.count_documents({'user_id': user_id})
    total_pages = (total_transactions + per_page - 1) // per_page

    user_transactions = list(transactions.find({'user_id': user_id})
                             .sort('date', -1)
                             .skip(skip)
                             .limit(per_page))

    return render_template(
        'transactions.html',
        transactions=user_transactions,
        page=page,
        total_pages=total_pages
    )


@app.route('/range-analysis')
def range_analysis():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    start = request.args.get("start")
    end = request.args.get("end")
    user_id = ObjectId(session['user_id'])

    query = {
        'user_id': user_id,
        'date': {'$gte': start, '$lte': end}
    }

    txns = list(transactions.find(query))
    txns_display = []
    income, expenses = 0, 0
    category_breakdown = {}

    for t in txns:
        amount = t['amount']
        txns_display.append({
            "date": t['date'],
            "description": t.get("description", ""),
            "category": t.get("category", "Others"),
            "type": t["type"],
            "amount": round(amount, 2)
        })

        if t["type"] == "income":
            income += amount
        else:
            expenses += amount

        cat = t.get("category", "Others")
        category_breakdown[cat] = category_breakdown.get(cat, 0) + amount

    return jsonify({
        "transactions": txns_display,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "balance": round(income - expenses, 2),
        "category_breakdown": category_breakdown
    })


@app.route('/merchant-spend')
def merchant_spend():
    if 'user_id' not in session:
        return jsonify({})

    user_id = ObjectId(session['user_id'])
    txns = list(transactions.find({'user_id': user_id}))

    summary = {}
    for txn in txns:
        merchant = txn.get('merchant', 'Unknown')
        summary[merchant] = summary.get(merchant, 0) + txn.get('amount', 0)

    return jsonify(summary)


if __name__ == '__main__':
    app.run(debug=True)