# 🚀 Development Environment Setup Guide

This guide helps you run your complete health analysis system locally with proper CORS configuration.

## 🏗️ **Your Complete Architecture**

```
📱 Bio-Coach-Hub (localhost:8080) ↔️ hos-agentic-ai-prod (localhost:8002)
                     ↕️
                hos-fapi-hm-sahha-main (localhost:8000)
                     ↕️
                 Supabase Database
```

## ⚙️ **Step 1: Start hos-agentic-ai-prod Server**

```bash
# Navigate to the prod folder
cd hos-agentic-ai-prod/hos-agentic-ai-prod

# Make sure environment is set to development
# Check your .env file contains:
# ENVIRONMENT=development

# Start the server on localhost:8002
python start_openai.py

# You should see:
# ========================================
#    🧠 HolisticOS AI Service Started
# ========================================
#    URL: http://localhost:8002
#    Health: http://localhost:8002/api/health
# ========================================
```

## ⚙️ **Step 2: Start hos-fapi-hm-sahha-main Server**

```bash
# Navigate to the Sahha API folder
cd hos-fapi-hm-sahha-main

# Start the server on localhost:8000
python -m app.main
# OR
uvicorn app.main:app --reload --port 8000
```

## ⚙️ **Step 3: Start Bio-Coach-Hub Frontend**

```bash
# Navigate to the frontend folder
cd bio-coach-hub

# Install dependencies (if needed)
npm install

# Start the development server on localhost:8080
npm run dev
```

## 🔧 **CORS Configuration Explained**

### **Current CORS Settings (Fixed)**

Your `hos-agentic-ai-prod` now allows these localhost origins in development:

```typescript
// In shared_libs/config/security_settings.py
development_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:5173",
    "http://localhost:8080",  // Bio-Coach-Hub
    "http://localhost:8002"   // Added for your development needs
]
```

### **Environment-Based CORS Logic:**

- **Development (`ENVIRONMENT=development`)**: Allows all localhost origins + production domains
- **Production (`ENVIRONMENT=production`)**: Only allows production domains
- **Staging (`ENVIRONMENT=staging`)**: Allows production + staging domains

## 🧪 **Test Your Setup**

### **1. Test hos-agentic-ai-prod (Port 8002)**
```bash
# Health check
curl http://localhost:8002/api/health

# Should return: {"status": "healthy", "environment": "development"}
```

### **2. Test CORS from Browser**
```javascript
// Open browser console on http://localhost:8080 and run:
fetch('http://localhost:8002/api/health')
  .then(response => response.json())
  .then(data => console.log('CORS working:', data))
  .catch(error => console.error('CORS error:', error));
```

### **3. Test hos-fapi-hm-sahha-main (Port 8000)**
```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

## 🐛 **Troubleshooting CORS Issues**

### **Issue 1: "Access-Control-Allow-Origin header is present"**

**Cause**: Server running in production mode instead of development

**Solution**:
```bash
# Check your .env file in hos-agentic-ai-prod/hos-agentic-ai-prod/.env
# Make sure it contains:
ENVIRONMENT=development

# Restart the server
python start_openai.py
```

### **Issue 2: "ERR_FAILED 200 (OK)" - Mixed Content**

**Cause**: Browser blocking HTTP requests from HTTPS origins

**Solution**: Make sure both frontend and backend are using the same protocol (HTTP or HTTPS)

### **Issue 3: Different ports not working**

**Current ports configuration**:
- Bio-Coach-Hub: `http://localhost:8080`
- hos-agentic-ai-prod: `http://localhost:8002`
- hos-fapi-hm-sahha-main: `http://localhost:8000`

If you need different ports, update the CORS configuration in `security_settings.py`.

## 🔄 **Bio-Coach-Hub API Configuration**

Make sure your frontend is configured to use the correct local endpoints:

### **Option 1: Environment Variables** (Recommended)

Create/update `.env.local` in bio-coach-hub:

```bash
# For development - use local servers
VITE_API_BASE_URL=http://localhost:8002
VITE_SAHHA_API_BASE_URL=http://localhost:8000

# For production testing - use production servers
# VITE_API_BASE_URL=https://hos-agentic-ai-prod.onrender.com
# VITE_SAHHA_API_BASE_URL=https://hos-fapi-hm-sahha.onrender.com
```

### **Option 2: Update API Service Files**

If you want to hardcode for development, update your API service:

```typescript
// In bio-coach-hub/src/services/apiService.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';
const SAHHA_API_BASE_URL = import.meta.env.VITE_SAHHA_API_BASE_URL || 'http://localhost:8000';

// Use these instead of hardcoded production URLs
```

## 📋 **Development Workflow**

### **Daily Development Startup:**

```bash
# Terminal 1: Start AI Service
cd hos-agentic-ai-prod/hos-agentic-ai-prod
python start_openai.py

# Terminal 2: Start Sahha API
cd hos-fapi-hm-sahha-main  
python -m app.main

# Terminal 3: Start Frontend
cd bio-coach-hub
npm run dev

# Your apps:
# 🎯 Frontend: http://localhost:8080
# 🧠 AI Service: http://localhost:8002
# 📊 Health Data API: http://localhost:8000
```

### **Testing API Endpoints:**

```bash
# Test AI service endpoints
curl http://localhost:8002/api/health
curl http://localhost:8002/api/admin/users

# Test Sahha API endpoints  
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health-metrics/overview?profile_id=test

# Test from frontend
# Browser console on localhost:8080:
fetch('http://localhost:8002/api/health').then(r => r.json()).then(console.log)
```

## 🔒 **Security Notes for Development**

1. **CORS is relaxed in development** - allows localhost origins
2. **HTTPS is not enforced** - uses HTTP for easier development  
3. **Debug endpoints are enabled** - `/debug/*` routes available
4. **Detailed error messages** - shown in development mode
5. **Connection pool is disabled** - uses direct Supabase client fallback

## 🚀 **Production Deployment Notes**

When deploying to production:

1. **Environment**: Set `ENVIRONMENT=production`
2. **CORS**: Only production domains allowed
3. **HTTPS**: All traffic must use HTTPS
4. **Database**: Uses connection pooling
5. **Logging**: Minimal error-only logging

---

## 🎯 **Quick Fix Summary**

**What was changed:**
- ✅ Added `http://localhost:8002` to CORS allowed origins
- ✅ Verified `ENVIRONMENT=development` in .env
- ✅ Confirmed server runs on port 8002

**Next steps:**
1. Restart `hos-agentic-ai-prod` server: `python start_openai.py`
2. Verify frontend uses `http://localhost:8002` for AI service calls
3. Test CORS with browser console fetch request

Your CORS errors should be resolved now! 🎉