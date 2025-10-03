import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/client";

/**
 * Auth callback route handler
 * Handles email verification and password reset callbacks from Supabase
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = requestUrl.searchParams.get("next") || "/dashboard";

  if (code) {
    const supabase = createClient();

    // Exchange the code for a session
    await supabase.auth.exchangeCodeForSession(code);
  }

  // Redirect to the next page or dashboard
  return NextResponse.redirect(new URL(next, requestUrl.origin));
}
