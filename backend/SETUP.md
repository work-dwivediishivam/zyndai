# Quick Setup Guide

## 🚀 Get Started in 3 Steps

### Step 1: Get Your Google API Key

1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Step 2: Configure Backend

```bash
cd backend

# Add your API key to .env file
echo "GOOGLE_API_KEY=your_api_key_here" >> .env
```

### Step 3: Start the Server (if not already running)

The backend server is already running on port 8000. If you need to restart:

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

## ✅ Test It Out

1. Open frontend at http://localhost:5173
2. Login: `demo@uniflow.com` / `demo123`
3. Create a new proposal
4. Try these prompts:
   - "Create a proposal for an AI-powered document management system"
   - Click 📎 to attach PDFs, DOCX, Excel, or images
   - Ask "Summarize this document" with a PDF attached

## 📋 Supported File Types

- **PDF** (.pdf) - Text extraction
- **Word** (.docx, .doc) - Full document processing
- **Excel** (.xlsx, .xls) - All sheets
- **Images** (.jpg, .png, .gif, .webp) - Vision analysis

## 🔍 Features

✅ Gemini 2.5 Flash AI model
✅ Multi-file upload support
✅ Intelligent context management
✅ Conversation history tracking
✅ Automatic file chunking for large documents
✅ Vision model for image analysis

## ⚠️ Important Notes

- Without `GOOGLE_API_KEY`, the backend will work but AI features will be disabled
- Files are processed in-memory (not saved to disk)
- Chat history is stored per-proposal
- Maximum context window: ~1M tokens
