import { createBrowserClient } from "@supabase/ssr";

/**
 * Creates a Supabase client for use in client-side components
 * This client is used in Client Components and browser contexts
 *
 * @returns Supabase browser client instance
 * @throws Error if required environment variables are missing
 */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // Validate environment variables
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing Supabase environment variables. Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set."
    );
  }

  // Validate URL format
  try {
    new URL(supabaseUrl);
  } catch {
    throw new Error(
      `Invalid supabaseUrl: Must be a valid HTTP or HTTPS URL. Got: ${supabaseUrl || "undefined"}`
    );
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
