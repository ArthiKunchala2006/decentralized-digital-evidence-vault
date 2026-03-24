# app.py
from flask import Flask, request, jsonify, send_file
import os
import hashlib
import random
import string
import qrcode
from io import BytesIO

app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simulated "blockchain" storage (dictionary)
# txid -> hash
blockchain = {}

# --- HELPER FUNCTIONS ---

def generate_hash(file_path):
    """Generate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_txid():
    """Generate a random transaction ID."""
    return "TX" + ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))

def generate_qr_code(data):
    """Generate QR code as a BytesIO object."""
    qr = qrcode.QRCode(box_size=5, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

# --- ROUTES ---

@app.route("/")
def home():
    return "Decentralized Evidence Vault Backend is running!"

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    filename = file.filename
    if filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    file_hash = generate_hash(file_path)
    txid = generate_txid()
    
    blockchain[txid] = file_hash
    
    # Generate QR code for transaction ID
    qr_img = generate_qr_code(txid)
    
    return send_file(
        qr_img,
        mimetype="image/png",
        as_attachment=False,
        download_name=f"{txid}_qr.png"
    )

@app.route("/verify", methods=["POST"])
def verify_file():
    if "file" not in request.files or "txid" not in request.form:
        return jsonify({"error": "File and Transaction ID required"}), 400
    
    file = request.files["file"]
    txid = request.form["txid"].strip()
    
    if txid not in blockchain:
        return jsonify({"error": "Transaction ID not found"}), 404
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    file_hash = generate_hash(file_path)
    stored_hash = blockchain[txid]
    
    if file_hash == stored_hash:
        status = "Verification Successful ✅"
    else:
        status = "Verification Failed ❌"
    
    return jsonify({
        "status": status,
        "hash": file_hash,
        "txid": txid
    })

# --- RUN SERVER ---
if __name__ == "__main__":
    app.run(debug=True)
