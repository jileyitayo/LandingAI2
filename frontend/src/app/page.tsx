import Link from "next/link";

export default function Home() {
  return (
    <div className="relative min-h-screen bg-surface overflow-hidden">
      {/* Ambient brand glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-56 left-1/2 -translate-x-1/2 h-[32rem] w-[48rem] rounded-full bg-brand/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-64 -right-32 h-[28rem] w-[36rem] rounded-full bg-brand-2/10 blur-3xl"
      />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          <h1 className="font-display text-6xl sm:text-7xl font-bold bg-brand-gradient bg-clip-text text-transparent mb-6 text-balance">
            SiteSmith
          </h1>
          <p className="text-xl text-muted mb-12 max-w-2xl mx-auto text-balance">
            AI-powered website builder for African entrepreneurs. Create
            professional websites in minutes, no code required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              href="/auth/signup"
              className="px-8 py-3 bg-brand-gradient text-brand-fg rounded-full font-medium shadow-glow-sm hover:shadow-glow hover:-translate-y-0.5 active:translate-y-0 transition-all"
            >
              Get Started Free
            </Link>
            <Link
              href="/auth/login"
              className="px-8 py-3 bg-card text-fg rounded-full font-medium border border-border hover:bg-card-muted transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
