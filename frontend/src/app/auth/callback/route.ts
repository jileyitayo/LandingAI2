import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Normalizes an origin URL by converting 0.0.0.0 to localhost
 * This ensures consistent redirect URLs regardless of how the app is accessed
 */
function normalizeOrigin(origin: string): string {
  try {
    const url = new URL(origin);
    // Replace 0.0.0.0 with localhost
    if (url.hostname === "0.0.0.0") {
      url.hostname = "localhost";
    }
    return url.origin;
  } catch {
    // If URL parsing fails, try simple string replacement
    return origin.replace(/0\.0\.0\.0/g, "localhost");
  }
}

/**
 * Auth callback route handler
 * Handles OAuth, email verification and password reset callbacks from Supabase
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = requestUrl.searchParams.get("next") || "/dashboard";

  // Normalize origin to ensure consistent redirects (0.0.0.0 -> localhost)
  const normalizedOrigin = normalizeOrigin(requestUrl.origin);

  if (code) {
    const supabase = await createClient();

    // Exchange the code for a session
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (error) {
      console.error("Error exchanging code for session:", error);
      // Redirect to login with error using normalized origin
      return NextResponse.redirect(
        new URL(`/auth/login?error=${encodeURIComponent(error.message)}`, normalizedOrigin)
      );
    }
  }

  // Redirect to the next page or dashboard using normalized origin
  return NextResponse.redirect(new URL(next, normalizedOrigin));
}
