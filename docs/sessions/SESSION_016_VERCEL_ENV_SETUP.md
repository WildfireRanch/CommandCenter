# Setting Up Vercel Environment Variables

## 📝 Variables to Add

Copy these exact values to add to Vercel:

```bash
# 1. Google OAuth Client ID
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com

# 2. Google OAuth Client Secret
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj

# 3. NextAuth URL (your Vercel deployment)
NEXTAUTH_URL=https://mcp.wildfireranch.us

# 4. NextAuth Secret (generated)
NEXTAUTH_SECRET=bE2tr+Az+/jG23Igu3myX2kdHUo9eJlF2/4OgUUi0B8=

# 5. Allowed Email (⚠️ UPDATE WITH YOUR EMAIL)
ALLOWED_EMAIL=your-email@gmail.com

# 6. Railway API URL (already public)
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
```

---

## 🌐 How to Add via Vercel Dashboard

### **Step 1: Go to Vercel Project Settings**

1. Visit: https://vercel.com/dashboard
2. Select your **CommandCenter** project (should be `mcp.wildfireranch.us`)
3. Click **Settings** tab
4. Click **Environment Variables** in the left sidebar

### **Step 2: Add Each Variable**

For each variable above:

1. Click **Add New**
2. Enter the **Key** (e.g., `GOOGLE_CLIENT_ID`)
3. Enter the **Value** (copy from above)
4. Select **Environment:**
   - ✅ Production
   - ✅ Preview (optional, but recommended)
   - ❌ Development (not needed, uses local `.env`)
5. Click **Save**

### **Step 3: Verify**

After adding all 6 variables, you should see:

```
✅ GOOGLE_CLIENT_ID          Production
✅ GOOGLE_CLIENT_SECRET      Production
✅ NEXTAUTH_URL              Production
✅ NEXTAUTH_SECRET           Production
✅ ALLOWED_EMAIL             Production
✅ NEXT_PUBLIC_API_URL       Production
```

---

## ⚠️ IMPORTANT: Update ALLOWED_EMAIL

The `ALLOWED_EMAIL` variable restricts who can sign in. You MUST update it:

```bash
# Change from:
ALLOWED_EMAIL=your-email@gmail.com

# To your actual email:
ALLOWED_EMAIL=bret@westwood5.com  # (or whatever email you use with Google)
```

---

## 🔄 Trigger Redeployment

After adding environment variables, Vercel needs to redeploy:

**Option 1: Automatic (via Git push)**
```bash
git add .
git commit -m "Add NextAuth environment variables"
git push origin main
```

**Option 2: Manual (via Vercel Dashboard)**
1. Go to **Deployments** tab
2. Click **...** on latest deployment
3. Click **Redeploy**
4. Select **Use existing Build Cache** (faster)
5. Click **Redeploy**

---

## ✅ Verification

After redeployment completes (~2 min):

1. Visit: https://mcp.wildfireranch.us/kb
2. You should see a "Sign in with Google" button
3. Click it - should redirect to Google OAuth
4. Sign in with your allowed email
5. Should redirect back to KB page (authenticated)

---

## 🐛 Troubleshooting

**Error: "Configuration invalid"**
- Check that `NEXTAUTH_URL` matches your exact Vercel domain
- No trailing slash: `https://mcp.wildfireranch.us` ✅ not `https://mcp.wildfireranch.us/` ❌

**Error: "Access denied"**
- Check `ALLOWED_EMAIL` matches the email you're signing in with
- Check email is spelled correctly (case-insensitive)

**Error: "Redirect URI mismatch"**
- Continue to next step: Update Google Cloud Console redirect URIs

---

Next: Update Google Cloud Console OAuth settings
