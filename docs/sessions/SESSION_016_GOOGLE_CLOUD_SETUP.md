# Google Cloud Console OAuth Setup

## 🎯 Goal

Update your existing Google Cloud OAuth client to work with NextAuth.js on Vercel.

---

## 📋 Step-by-Step Instructions

### **Step 1: Go to Google Cloud Console**

1. Visit: https://console.cloud.google.com
2. Select your project (or the project where your OAuth client was created)
3. If you don't have a project yet, create one: **"CommandCenter KB"**

---

### **Step 2: Enable Required APIs**

1. In the left sidebar, click **APIs & Services** → **Library**
2. Search for and enable:
   - ✅ **Google Drive API**
   - ✅ **Google Docs API**

(If already enabled, you'll see "Manage" instead of "Enable")

---

### **Step 3: Configure OAuth Consent Screen**

1. Click **APIs & Services** → **OAuth consent screen**

2. If not already configured, set up:
   - **User Type:** External
   - Click **Create**

3. Fill in **App information:**
   ```
   App name: CommandCenter
   User support email: [your-email@gmail.com]
   Developer contact: [your-email@gmail.com]
   ```

4. Click **Save and Continue**

5. **Add Scopes:**
   - Click **Add or Remove Scopes**
   - Check these scopes:
     ```
     ✅ .../auth/userinfo.email
     ✅ .../auth/userinfo.profile
     ✅ openid
     ```
   - Click **Add** and manually add:
     ```
     https://www.googleapis.com/auth/drive.readonly
     https://www.googleapis.com/auth/documents.readonly
     ```
   - Click **Update**
   - Click **Save and Continue**

6. **Add Test Users** (if app is not published):
   - Click **Add Users**
   - Enter your email: `your-email@gmail.com`
   - Click **Add**
   - Click **Save and Continue**

7. Click **Back to Dashboard**

---

### **Step 4: Update OAuth Client Redirect URIs**

1. Click **APIs & Services** → **Credentials**

2. Under **OAuth 2.0 Client IDs**, find your existing client:
   ```
   643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
   ```

3. Click the **✏️ Edit** icon (or client name)

4. Scroll to **Authorized redirect URIs**

5. **Add these URIs** (keep existing ones if any):
   ```
   https://mcp.wildfireranch.us/api/auth/callback/google
   http://localhost:3000/api/auth/callback/google
   ```

6. Click **Save**

---

### **Step 5: Verify Credentials**

Double-check your credentials match what's in Vercel:

```
Client ID: 643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
Client Secret: GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
```

If they don't match, update Vercel environment variables with the correct values.

---

## ✅ Verification Checklist

After setup:

- [ ] Google Drive API enabled
- [ ] Google Docs API enabled
- [ ] OAuth consent screen configured
- [ ] Your email added as test user (if not published)
- [ ] Scopes include Drive and Docs readonly
- [ ] Redirect URIs include Vercel callback URL
- [ ] Credentials match Vercel environment variables

---

## 🧪 Test the Setup

1. Visit: https://mcp.wildfireranch.us/kb
2. Click "Sign in with Google"
3. You should see Google's consent screen
4. After approving, should redirect back to your app
5. Should be signed in ✅

---

## 🐛 Common Issues

**"Redirect URI mismatch" error:**
- Check spelling of redirect URI exactly: `/api/auth/callback/google`
- No extra spaces or characters
- Must be HTTPS in production (Vercel provides this)

**"Access blocked: This app's request is invalid":**
- OAuth consent screen not configured
- Missing required scopes (email, profile, openid)

**"Access blocked: Authorization Error":**
- Your email not added to test users
- App needs to be published (or use test users list)

**"This app hasn't been verified":**
- Normal for test apps
- Click "Advanced" → "Go to CommandCenter (unsafe)"
- Or publish app for verification (later)

---

Next: Get your Google Drive folder ID
