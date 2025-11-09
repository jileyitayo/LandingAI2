import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Gets the correct app origin for redirects
 * Prioritizes environment variable to handle Railway/production deployments correctly
 */
function getAppOrigin(request: Request): string {
  // Priority 1: Environment variable (for production/Railway)
  if (process.env.NEXT_PUBLIC_SITE_URL) {
    return process.env.NEXT_PUBLIC_SITE_URL;
  }

  // Priority 2: X-Forwarded-Host header (for proxied environments)
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") || "https";
  if (forwardedHost) {
    return `${forwardedProto}://${forwardedHost}`;
  }

  // Priority 3: Host header
  const host = request.headers.get("host");
  if (host) {
    const proto = host.includes("localhost") || host.includes("127.0.0.1") ? "http" : "https";
    return `${proto}://${host}`;
  }

  // Fallback: request URL origin (normalize 0.0.0.0 to localhost)
  const requestUrl = new URL(request.url);
  if (requestUrl.hostname === "0.0.0.0") {
    requestUrl.hostname = "localhost";
  }
  return requestUrl.origin;
}

/**
 * Auth callback route handler
 * Handles OAuth, email verification and password reset callbacks from Supabase
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = requestUrl.searchParams.get("next") || "/dashboard";

  // Get the correct app origin for redirects
  const appOrigin = getAppOrigin(request);

  if (code) {
    const supabase = await createClient();

    // Exchange the code for a session
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (error) {
      console.error("Error exchanging code for session:", error);
      // Redirect to login with error
      return NextResponse.redirect(
        new URL(`/auth/login?error=${encodeURIComponent(error.message)}`, appOrigin)
      );
    }
  }

  // Redirect to the next page or dashboard
  return NextResponse.redirect(new URL(next, appOrigin));
}
