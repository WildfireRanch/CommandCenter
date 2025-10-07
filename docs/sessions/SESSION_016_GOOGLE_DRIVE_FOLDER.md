# Getting Your Google Drive Folder ID

## 🎯 Goal

Get the folder ID for your "command-center" folder in Google Drive to sync documents.

---

## 📋 Step-by-Step Instructions

### **Step 1: Open Google Drive**

1. Visit: https://drive.google.com
2. Sign in with the same Google account you'll use for CommandCenter

---

### **Step 2: Find or Create "command-center" Folder**

**Option A: If folder already exists**
1. Navigate to your "command-center" folder
2. Skip to Step 3

**Option B: If folder doesn't exist**
1. Click **New** → **Folder**
2. Name it: `command-center`
3. Click **Create**
4. Open the folder

---

### **Step 3: Get the Folder ID**

1. With the "command-center" folder open, look at the URL bar:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```

2. Copy the **FOLDER_ID_HERE** part after `/folders/`

   **Example:**
   ```
   URL: https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J

   Folder ID: 1a2B3c4D5e6F7g8H9i0J
   ```

---

### **Step 4: Add to Railway Environment Variables**

**Via Railway Dashboard:**

1. Visit: https://railway.app
2. Select your **CommandCenter** project
3. Click on your **API service** (the Railway backend)
4. Click **Variables** tab
5. Click **New Variable**
6. Add:
   ```
   Key: GOOGLE_DOCS_KB_FOLDER_ID
   Value: [paste your folder ID here]
   ```
7. Click **Add**

**Via Local .env (optional, for local development):**

Update `/workspaces/CommandCenter/.env`:
```bash
# Change from:
GOOGLE_DOCS_KB_FOLDER_ID=your-folder-id-here

# To:
GOOGLE_DOCS_KB_FOLDER_ID=1a2B3c4D5e6F7g8H9i0J  # Your actual folder ID
```

---

## 📁 Recommended Folder Structure

For best results with the two-tier KB system, organize your folder like this:

```
command-center/
├── context/                    # Tier 1: Always-loaded files
│   ├── personal.docx          # Personal info, preferences
│   ├── solar-shack.docx       # Core solar system facts
│   └── financial.docx         # Budget constraints
│
├── solar-shack-technical/     # Tier 2: Searchable docs
│   ├── SolArk Manual.docx
│   ├── Battery Specs.docx
│   └── Wiring Diagrams.docx
│
├── hvac/
│   └── HVAC Specs.docx
│
├── orchard/
│   └── Orchard Care Schedule.docx
│
├── irrigation/
│   └── Irrigation System.docx
│
└── business-plans/
    └── Wildfire Green Q1.docx
```

**Notes:**
- Files in `context/` subfolder will be marked as context files (always loaded)
- All other files are searchable via semantic search
- Only Google Docs files (`.docx` in Drive) are synced
- PDFs, Sheets, Slides are not synced (can be added later)

---

## ✅ Verification

After adding the folder ID to Railway:

1. Railway will auto-deploy with the new environment variable (~2 min)
2. The backend will be able to access your Google Drive folder
3. You can test sync once the frontend KB page is implemented

---

## 🐛 Common Issues

**"Folder not found" error:**
- Double-check the folder ID is copied correctly
- Make sure folder is owned by or shared with the Google account you're using
- Folder must exist (not deleted)

**"Permission denied" error:**
- Make sure you're signing in with the same Google account that owns the folder
- Check OAuth scopes include `drive.readonly`

**Empty folder ID:**
- Don't include `https://` or `/folders/` - just the ID
- ID should be alphanumeric, about 20-40 characters

---

Next: Test the complete setup!
