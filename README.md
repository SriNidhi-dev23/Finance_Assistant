# Finance_Assistant

# Personal Finance Assistant

A web-based finance dashboard that helps users manage income, expenses, and savings with auto transaction extraction and visual analytics.

## Features

- User registration and login
- Dashboard with total balance, income, expenses, and savings rate
- Upload receipts and PDF bank statements
- Automatic transaction extraction using Gemini AI
- Transactions stored and categorized in MongoDB
- Date-range transaction analysis
- Visual analytics using charts (pie, bar)
- Typing effect and responsive design

## Technologies Used

- Frontend: HTML, Tailwind CSS, JavaScript, Chart.js
- Backend: Python (Flask)
- Database: MongoDB
- AI Integration: Gemini API for OCR and PDF parsing
- Libraries: Flask, PyMongo, requests, Chart.js

## Folder Structure

finance-assistant/
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transactions.html
│   └── upload_receipt.html
├── app.py
├── gemini_utils.py
├── config.py


## How It Works

- User logs in and views financial summary on dashboard
- Receipts and PDF bank statements can be uploaded
- Gemini AI parses the file and extracts transaction data
- Data is stored in MongoDB and displayed in charts
- Users can analyze data by category and by date range

## Requirements

- Python 3.8 or higher
- MongoDB installed or use a cloud instance
- Gemini API key from Google AI
- Flask==2.3.2
-Flask-PyMongo==2.3.0
-pymongo==4.6.1
-Werkzeug==2.3.6
-requests==2.31.0





