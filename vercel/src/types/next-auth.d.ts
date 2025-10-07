import { DefaultSession } from "next-auth";

declare module "next-auth" {
  /**
   * Extend the built-in session type to include accessToken
   */
  interface Session {
    accessToken?: string;
    user: {
      id?: string;
    } & DefaultSession["user"];
  }

  /**
   * Extend the built-in user type if needed
   */
  interface User {
    id?: string;
  }
}

declare module "next-auth/jwt" {
  /**
   * Extend the built-in JWT type to include accessToken and refreshToken
   */
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
  }
}
