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
    async signIn({ user }) {
      const allowedEmail = process.env.ALLOWED_EMAIL;
      if (user.email === allowedEmail) {
        return true;
      }
      return false; // Reject all other emails
    },

    // Include access token in session
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
      }
      return token;
    },

    async session({ session, token }) {
      // @ts-ignore
      session.accessToken = token.accessToken as string;
      return session;
    }
  },

  pages: {
    signIn: '/auth/signin',
    error: '/auth/error'
  }
};
