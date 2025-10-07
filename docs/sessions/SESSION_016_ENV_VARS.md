# Session 016: Environment Variables Setup

## ✅ Dependencies Installed

### Frontend (Vercel)
- ✅ `next-auth@4.24.11` installed

### Backend (Railway)
- ✅ `google-api-python-client` installed
- ✅ `google-auth-httplib2` installed
- ✅ `google-auth-oauthlib` installed

---

## 🔐 Environment Variables Needed

### **Vercel Frontend (.env or Vercel Dashboard)**

Add these to your Vercel project:

```bash
# Google OAuth (for NextAuth.js)
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj

# NextAuth Configuration
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=bE2tr+Az+/jG23Igu3myX2kdHUo9eJlF2/4OgUUi0B8=

# Email restriction (only allow your email)
ALLOWED_EMAIL=your-email@gmail.com  # ⚠️ UPDATE THIS

# Railway API (for KB sync)
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
```

**How to add to Vercel:**
```bash
# Option 1: Via CLI
vercel env add GOOGLE_CLIENT_ID production
vercel env add GOOGLE_CLIENT_SECRET production
vercel env add NEXTAUTH_URL production
vercel env add NEXTAUTH_SECRET production
vercel env add ALLOWED_EMAIL production
vercel env add NEXT_PUBLIC_API_URL production

# Option 2: Via Dashboard
# Go to: https://vercel.com/your-project/settings/environment-variables
# Add each variable for "Production" environment
```

---

### **Railway Backend (Already in .env)**

These are already configured in your `.env`:

```bash
# Google OAuth credentials (already set)
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj

# OpenAI for embeddings (already set)
OPENAI_API_KEY=sk-proj-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Database (already set)
DATABASE_URL=postgresql://postgres:1tVY3mhx1Xt3d7tvBrDKU0ZC0JO7u010bcisH25jNkg@postgres.railway.internal:5432/commandcenter

# ⚠️ MISSING: Google Drive folder ID
GOOGLE_DOCS_KB_FOLDER_ID=your-folder-id-here  # Get from Google Drive folder URL
```

**How to get Google Drive Folder ID:**
1. Open Google Drive
2. Navigate to your "command-center" folder
3. Look at URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
4. Copy the `FOLDER_ID_HERE` part
5. Add to `.env` and Railway environment variables

---

## 🔧 Google Cloud Console Setup

### **Required Steps:**

1. **Go to:** https://console.cloud.google.com

2. **Create/Select Project:** "CommandCenter KB"

3. **Enable APIs:**
   - Google Drive API
   - Google Docs API

4. **Configure OAuth Consent Screen:**
   - User Type: External
   - App name: CommandCenter
   - User support email: your-email@gmail.com
   - Developer email: your-email@gmail.com
   - Scopes:
     - `openid`
     - `email`
     - `profile`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/documents.readonly`
   - Test users: Add your email

5. **Update OAuth Credentials:**
   - Go to: Credentials → OAuth 2.0 Client IDs
   - Edit your existing client ID
   - Add to **Authorized redirect URIs:**
     ```
     https://mcp.wildfireranch.us/api/auth/callback/google
     http://localhost:3000/api/auth/callback/google
     ```

---

## ✅ Checklist

Before implementing Session 016:

- [ ] NextAuth dependencies installed (✅ DONE)
- [ ] Google API libraries installed (✅ DONE)
- [ ] NEXTAUTH_SECRET generated (✅ DONE)
- [ ] Add environment variables to Vercel (⚠️ TODO)
- [ ] Get Google Drive folder ID (⚠️ TODO)
- [ ] Update OAuth redirect URIs in Google Cloud (⚠️ TODO)
- [ ] Set ALLOWED_EMAIL to your actual email (⚠️ TODO)

---

## 📝 Next Steps

1. **Update Vercel environment variables** (via dashboard or CLI)
2. **Get your Google Drive folder ID** and add to Railway
3. **Update Google Cloud OAuth redirect URIs**
4. **Start implementing Part 1** of the adapted plan (Database schema)

---

Generated: October 7, 2025
