# Authentication Guide - Protecting Pages with Google OAuth

This guide explains how to protect pages with automatic Google OAuth authentication in the CommandCenter frontend.

---

## Overview

The CommandCenter uses NextAuth.js with Google OAuth for authentication. We've created a reusable `ProtectedPage` component that automatically redirects users to Google sign-in if they're not authenticated.

**Key Features:**
- ✅ Automatic redirect to Google OAuth
- ✅ No manual "Sign in" button needed
- ✅ Seamless experience if user is already signed into Google
- ✅ Session persistence across page refreshes
- ✅ Restricted to authorized email only (`bret@westwood5.com`)

---

## Quick Start: Protecting a New Page

### Step 1: Import the ProtectedPage Component

```tsx
'use client';

import ProtectedPage from '@/components/ProtectedPage';
```

### Step 2: Wrap Your Page Content

```tsx
export default function MySecurePage() {
  return (
    <ProtectedPage loadingMessage="Loading your secure content...">
      <MyPageContent />
    </ProtectedPage>
  );
}

function MyPageContent() {
  // Your page content here
  // This only renders when user is authenticated
  return (
    <div>
      <h1>Secure Content</h1>
      <p>User is authenticated!</p>
    </div>
  );
}
```

That's it! Your page is now protected. 🎉

---

## Complete Example: Protected Dashboard

Here's a real-world example from the KB dashboard:

```tsx
'use client';

import { useSession } from 'next-auth/react';
import ProtectedPage from '@/components/ProtectedPage';

function DashboardContent() {
  const { data: session } = useSession();

  return (
    <div className="p-6">
      <h1>Welcome, {session?.user?.name}!</h1>
      <p>Email: {session?.user?.email}</p>
      {/* Your dashboard content */}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedPage loadingMessage="Loading Dashboard...">
      <DashboardContent />
    </ProtectedPage>
  );
}
```

---

## How It Works

### 1. User Visits Protected Page
- User navigates to `/kb` (or any protected page)
- `ProtectedPage` component checks authentication status

### 2. Authentication Check
- **If authenticated:** Content renders immediately
- **If not authenticated:** Automatic redirect to Google OAuth
- **While checking:** Shows loading spinner with your custom message

### 3. Google OAuth Flow
- User is redirected to `accounts.google.com`
- If already signed into Google: Nearly instant authentication
- If not signed in: User signs in with Google
- After authentication: Redirected back to original page

### 4. Email Verification
- NextAuth checks if email matches `ALLOWED_EMAIL` env var
- Only `bret@westwood5.com` is allowed
- Other emails are rejected with error message

### 5. Session Persistence
- Session stored in secure HTTP-only cookie
- Persists across page refreshes
- Persists across browser tabs
- Expires after inactivity (configurable)

---

## Component API

### ProtectedPage Props

```tsx
interface ProtectedPageProps {
  children: ReactNode;           // Your protected content
  loadingMessage?: string;       // Custom loading message (optional)
}
```

**Default Loading Message:** `"Checking authentication..."`

### Examples

```tsx
// Basic usage
<ProtectedPage>
  <MyContent />
</ProtectedPage>

// Custom loading message
<ProtectedPage loadingMessage="Loading your trading data...">
  <TradingDashboard />
</ProtectedPage>
```

---

## Accessing User Data

Once authenticated, you can access user information using the `useSession` hook:

```tsx
'use client';

import { useSession } from 'next-auth/react';

function MyComponent() {
  const { data: session } = useSession();

  return (
    <div>
      <p>Name: {session?.user?.name}</p>
      <p>Email: {session?.user?.email}</p>
      <img src={session?.user?.image || ''} alt="Profile" />

      {/* Access token for Google APIs */}
      <p>Token: {session?.accessToken}</p>
    </div>
  );
}
```

**Available Session Data:**
- `session.user.name` - Full name
- `session.user.email` - Email address
- `session.user.image` - Profile picture URL
- `session.accessToken` - OAuth access token (for Google API calls)
- `session.refreshToken` - OAuth refresh token

---

## Configuration

### Environment Variables

The authentication system requires these environment variables in Vercel:

```bash
# NextAuth Configuration
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=<your-secret-here>

# Google OAuth Credentials
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# Access Control
ALLOWED_EMAIL=bret@westwood5.com
```

### Modifying OAuth Scopes

To request additional Google API permissions, edit `/vercel/src/lib/auth.ts`:

```tsx
GoogleProvider({
  clientId: process.env.GOOGLE_CLIENT_ID!,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  authorization: {
    params: {
      scope: [
        'openid',
        'email',
        'profile',
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/documents.readonly',
        // Add more scopes here
        'https://www.googleapis.com/auth/calendar.readonly'
      ].join(' '),
      access_type: 'offline',
      prompt: 'consent'
    }
  }
})
```

---

## Advanced Patterns

### Protecting API Routes

You can also protect API routes using NextAuth:

```tsx
// /app/api/my-protected-route/route.ts
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { NextResponse } from 'next/server';

export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Protected API logic here
  return NextResponse.json({ data: 'secret data' });
}
```

### Multiple Email Allowlist

To allow multiple users, modify `/vercel/src/lib/auth.ts`:

```tsx
async signIn({ user }) {
  const allowedEmails = [
    'bret@westwood5.com',
    'admin@wildfireranch.us',
    'team@example.com'
  ];

  return allowedEmails.includes(user.email || '');
}
```

### Role-Based Access Control

Add roles to your session:

```tsx
// In /vercel/src/lib/auth.ts
async jwt({ token, user }) {
  if (user) {
    // Assign roles based on email
    token.role = user.email === 'bret@westwood5.com' ? 'admin' : 'user';
  }
  return token;
}

async session({ session, token }) {
  session.role = token.role as string;
  return session;
}
```

Then check roles in your component:

```tsx
function AdminPanel() {
  const { data: session } = useSession();

  if (session?.role !== 'admin') {
    return <p>Access denied. Admin only.</p>;
  }

  return <div>Admin content</div>;
}
```

---

## Troubleshooting

### Issue: Infinite Redirect Loop

**Cause:** Callback URL mismatch or session not being created

**Solution:**
1. Check `NEXTAUTH_URL` matches your domain exactly
2. Verify `NEXTAUTH_SECRET` is set
3. Clear browser cookies and try again
4. Check Vercel logs for auth errors

### Issue: "Access Denied" Error

**Cause:** Email not in allowlist

**Solution:**
1. Verify `ALLOWED_EMAIL` env var is set correctly
2. Check for whitespace in email address
3. Look at Vercel logs for sign-in callback debug output

### Issue: Session Not Persisting

**Cause:** Cookie settings or HTTPS issues

**Solution:**
1. Ensure your site uses HTTPS
2. Check browser cookie settings
3. Try incognito mode to rule out browser extensions

### Issue: "Invalid Credentials" from Google

**Cause:** OAuth credentials misconfigured

**Solution:**
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
2. Check Google Cloud Console redirect URIs include:
   - `https://mcp.wildfireranch.us/api/auth/callback/google`
3. Ensure OAuth consent screen is configured

---

## Testing Authentication

### Manual Testing Checklist

1. **Initial Sign-In:**
   - [ ] Visit protected page while signed out
   - [ ] Automatically redirected to Google
   - [ ] Sign in with authorized email
   - [ ] Redirected back to protected page
   - [ ] Content loads successfully

2. **Session Persistence:**
   - [ ] Refresh the page
   - [ ] Still signed in (no redirect)
   - [ ] Open new tab to protected page
   - [ ] Still signed in

3. **Sign Out:**
   - [ ] Navigate to `/api/auth/signout`
   - [ ] Confirm sign out
   - [ ] Visit protected page again
   - [ ] Redirected to Google OAuth

4. **Unauthorized Access:**
   - [ ] Sign in with non-allowed email
   - [ ] See "Access Denied" error
   - [ ] Cannot access protected content

---

## Pages Currently Protected

- ✅ `/kb` - Knowledge Base Dashboard

### Future Pages to Protect

Add `ProtectedPage` wrapper to these when ready:
- `/dashboard` - Main dashboard (if needed)
- `/energy` - Energy monitoring
- `/logs` - System logs viewer
- `/studio` - Development studio
- Any new admin pages

---

## File Reference

### Key Files

- **ProtectedPage Component:** `/vercel/src/components/ProtectedPage.tsx`
- **Auth Configuration:** `/vercel/src/lib/auth.ts`
- **Auth API Route:** `/vercel/src/app/api/auth/[...nextauth]/route.ts`
- **Session Provider:** `/vercel/src/lib/providers.tsx`

### Component Structure

```
vercel/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── auth/
│   │   │       └── [...nextauth]/
│   │   │           └── route.ts          # NextAuth API handler
│   │   └── kb/
│   │       └── page.tsx                  # Example protected page
│   ├── components/
│   │   └── ProtectedPage.tsx             # Reusable auth wrapper
│   └── lib/
│       ├── auth.ts                       # Auth configuration
│       └── providers.tsx                 # Session provider
```

---

## Best Practices

### ✅ DO:
- Use `ProtectedPage` for all sensitive pages
- Keep the inner content component separate (like `DashboardContent`)
- Use `useSession()` to access user data
- Provide custom loading messages for better UX
- Test authentication flow in incognito mode

### ❌ DON'T:
- Don't implement custom auth logic (use `ProtectedPage`)
- Don't store sensitive data in client-side state
- Don't expose API keys in frontend code
- Don't bypass authentication for "convenience"
- Don't forget to protect API routes too

---

## Security Considerations

### Current Security Features

✅ **Email Allowlist:** Only approved emails can sign in
✅ **OAuth 2.0:** Industry-standard authentication
✅ **HTTPS Only:** All traffic encrypted
✅ **HTTP-Only Cookies:** Session tokens not accessible via JavaScript
✅ **Access Token Storage:** Secured in server-side session
✅ **Automatic Token Refresh:** Handled by NextAuth

### Future Enhancements

📝 **2FA Support:** Add two-factor authentication
📝 **Session Timeout:** Configurable inactivity timeout
📝 **Audit Logging:** Track all sign-in attempts
📝 **IP Allowlisting:** Additional security layer
📝 **Rate Limiting:** Prevent brute force attacks

---

## Need Help?

- **NextAuth Docs:** https://next-auth.js.org/
- **Google OAuth Setup:** https://console.cloud.google.com/
- **Vercel Deployment:** https://vercel.com/docs

---

**Last Updated:** 2025-10-08
**Maintained By:** Bret Westwood / Claude Code
