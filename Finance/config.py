import os

# MongoDB connection URI
MONGO_URI = "mongodb://localhost:27017/"  # Change if you're using cloud DB

# Database and collection names
DB_NAME = "finance_app"

# Uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Flask Secret Key (change this in production)
SECRET_KEY = "your_secret_key_here"  # 🔐 Replace with a strong secret in production!

