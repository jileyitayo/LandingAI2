import { createBrowserClient } from "@supabase/ssr";

/**
 * Creates a Supabase client for use in client-side components
 * This client is used in Client Components and browser contexts
 *
 * @returns Supabase browser client instance
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
