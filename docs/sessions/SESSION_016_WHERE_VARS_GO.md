# Where Do Environment Variables Go?

## 📊 Quick Reference Table

| Variable | Vercel Frontend | Railway Backend | Google Cloud Console |
|----------|----------------|-----------------|---------------------|
| `GOOGLE_CLIENT_ID` | ✅ **YES** | ✅ YES (already in .env) | ❌ No (this IS the credential) |
| `GOOGLE_CLIENT_SECRET` | ✅ **YES** | ✅ YES (already in .env) | ❌ No (this IS the credential) |
| `OAUTH_REDIRECT_URI` | ❌ No (handled by NextAuth) | ❌ No | ✅ **YES** (add to Authorized redirect URIs) |
| `POST_AUTH_REDIRECT_URI` | ❌ No (not used in our setup) | ❌ No | ❌ No |
| `NEXTAUTH_URL` | ✅ **YES** | ❌ No | ❌ No |
| `NEXTAUTH_SECRET` | ✅ **YES** | ❌ No | ❌ No |
| `ALLOWED_EMAIL` | ✅ **YES** | ❌ No | ❌ No |
| `NEXT_PUBLIC_API_URL` | ✅ **YES** | ❌ No | ❌ No |
| `GOOGLE_DOCS_KB_FOLDER_ID` | ❌ No | ✅ **YES** | ❌ No |

---

## 📝 Detailed Breakdown

### **GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET**

**What they are:**
- Your Google OAuth credentials (like username/password for your app)
- Created in Google Cloud Console

**Where to add them:**

✅ **Vercel Frontend** - NextAuth.js needs these to initiate OAuth
```bash
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
```

✅ **Railway Backend** - Already in your `.env` (for KB sync later)
```bash
# Already set - no action needed
```

❌ **Google Cloud Console** - These ARE the credentials from Google Cloud

---

### **OAUTH_REDIRECT_URI**

**What it is:**
- Where Google sends users after they sign in
- Must be registered in Google Cloud Console

**Where to add it:**

❌ **NOT in Vercel** - NextAuth.js automatically uses:
```
https://mcp.wildfireranch.us/api/auth/callback/google
```

❌ **NOT in Railway** - Frontend handles OAuth, not backend

✅ **In Google Cloud Console:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://mcp.wildfireranch.us/api/auth/callback/google
   http://localhost:3000/api/auth/callback/google
   ```
4. Click Save

**Note:** The value in your `.env` (`http://localhost:3000/auth/callback`) is **wrong** for NextAuth.js. NextAuth uses `/api/auth/callback/google` instead.

---

### **POST_AUTH_REDIRECT_URI**

**What it is:**
- Where to send users after successful login
- NOT needed for our Session 016 implementation

**Where to add it:**

❌ **Nowhere** - We don't use this in our NextAuth.js setup
- NextAuth automatically redirects to the page user tried to access
- Or you can specify in code: `signIn('google', { callbackUrl: '/kb' })`

---

## ✅ Summary: What You Need to Do

### **1. Vercel Dashboard** (if not done yet)
Add these 6 variables:
```bash
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=bE2tr+Az+/jG23Igu3myX2kdHUo9eJlF2/4OgUUi0B8=
ALLOWED_EMAIL=your-email@gmail.com  # ⚠️ UPDATE THIS
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
```

### **2. Google Cloud Console**
Add **Authorized redirect URI**:
```
https://mcp.wildfireranch.us/api/auth/callback/google
```

### **3. Railway Dashboard**
Add folder ID:
```bash
GOOGLE_DOCS_KB_FOLDER_ID=1P6Dez9BRnIxnt-UNJzC4Iwl4AXF5H5DB
```

---

## 🐛 Common Confusion

**"Why is OAUTH_REDIRECT_URI in my .env but I don't add it to Vercel?"**

Your `.env` has old/different OAuth settings. For NextAuth.js:
- NextAuth **automatically** creates the redirect URI
- Format: `{NEXTAUTH_URL}/api/auth/callback/{provider}`
- Example: `https://mcp.wildfireranch.us/api/auth/callback/google`
- You don't set this as an env var
- You just register it in Google Cloud Console

**"What about POST_AUTH_REDIRECT_URI?"**

That's not used in our NextAuth.js setup. Ignore it for Session 016.

---

Ready to continue? Let me know when you've:
✅ Added redirect URI to Google Cloud Console
✅ Added folder ID to Railway

Then we start coding! 🚀
