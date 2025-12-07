from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
import os
from pathlib import Path
import hashlib

app = FastAPI(title="GPT Wrapped Backend")

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration (use environment variables in production)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "anupam99911@gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail App Password

# Storage directory
STORAGE_DIR = Path("uploaded_files")
STORAGE_DIR.mkdir(exist_ok=True)

def send_email_with_attachment(file_path, file_hash, upload_time):
    """Send uploaded file to admin email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"GPT Wrapped - New File Upload [{upload_time}]"
        
        # Email body
        body = f"""
New file uploaded to GPT Wrapped:

📁 Filename: {file_path.name}
🔐 SHA256: {file_hash}
⏰ Upload Time: {upload_time}
📊 File Size: {file_path.stat().st_size / 1024:.2f} KB

The file is attached for your verification.

---
GPT Wrapped Backend
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach file
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={file_path.name}')
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.get("/")
async def root():
    return {"message": "GPT Wrapped Backend API", "status": "running"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Receive and process uploaded conversations.json"""
    try:
        # Read file content
        content = await file.read()
        
        # Validate JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        
        # Generate hash and timestamp
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        upload_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save file with timestamp
        filename = f"conversations_{upload_time}_{file_hash}.json"
        file_path = STORAGE_DIR / filename
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Send to admin email
        email_sent = send_email_with_attachment(file_path, file_hash, upload_time)
        
        # Return success (file is already saved)
        return JSONResponse({
            "status": "success",
            "message": "File received and forwarded to admin",
            "file_hash": file_hash,
            "email_sent": email_sent,
            "data": data  # Return processed data to frontend
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Get upload statistics"""
    files = list(STORAGE_DIR.glob("*.json"))
    return {
        "total_uploads": len(files),
        "storage_used_mb": sum(f.stat().st_size for f in files) / (1024 * 1024)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
