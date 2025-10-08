import { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const authOptions: NextAuthOptions = {
  providers: [
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
            'https://www.googleapis.com/auth/documents.readonly'
          ].join(' '),
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    })
  ],

  callbacks: {
    // Restrict to your email only
    async signIn({ user, account, profile }) {
      const allowedEmail = process.env.ALLOWED_EMAIL;

      // Debug logging
      console.log('=== OAUTH SIGNIN CALLBACK DEBUG ===');
      console.log('User email from Google:', user.email);
      console.log('ALLOWED_EMAIL env var:', allowedEmail);
      console.log('Email match result:', user.email === allowedEmail);
      console.log('User object:', JSON.stringify(user, null, 2));
      console.log('Account object:', JSON.stringify(account, null, 2));
      console.log('Profile object:', JSON.stringify(profile, null, 2));
      console.log('=== END DEBUG ===');

      if (!allowedEmail) {
        console.error('[AUTH ERROR] ALLOWED_EMAIL environment variable is not set!');
        return false;
      }

      if (user.email === allowedEmail) {
        console.log('[AUTH SUCCESS] Email matches, allowing signin');
        return true;
      }

      console.error('[AUTH REJECTED] Email does not match:', {
        provided: user.email,
        expected: allowedEmail,
        providedLength: user.email?.length,
        expectedLength: allowedEmail?.length
      });
      return false; // Reject all other emails
    },

    // Include access token in session
    async jwt({ token, account }) {
      console.log('[JWT CALLBACK] Processing JWT token');
      if (account) {
        console.log('[JWT CALLBACK] Adding access token to JWT');
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
      }
      return token;
    },

    async session({ session, token }) {
      console.log('[SESSION CALLBACK] Creating session');
      // @ts-ignore
      session.accessToken = token.accessToken as string;
      return session;
    }
  }
};
