import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-6">
            SiteSmith
          </h1>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            AI-powered website builder for African entrepreneurs. Create
            professional websites in minutes, no code required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              href="/auth/signup"
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-colors shadow-lg"
            >
              Get Started Free
            </Link>
            <Link
              href="/auth/login"
              className="px-8 py-3 bg-white text-gray-700 rounded-lg font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Sign In
            </Link>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-3xl mx-auto border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Phase 2: Authentication ✓
            </h2>
            <p className="text-gray-600 mb-6">
              Milestone 2.1: Frontend Authentication UI is complete!
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h3 className="font-medium text-green-900 mb-2">
                  ✓ Features Implemented:
                </h3>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• User login with email/password</li>
                  <li>• User signup with validation</li>
                  <li>• Forgot password flow</li>
                  <li>• Password reset functionality</li>
                  <li>• Email verification</li>
                  <li>• Protected routes</li>
                </ul>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-medium text-blue-900 mb-2">
                  🛠️ Technologies:
                </h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• React Hook Form</li>
                  <li>• Zod validation</li>
                  <li>• Tailwind CSS</li>
                  <li>• Supabase Auth</li>
                  <li>• Next.js App Router</li>
                  <li>• TypeScript</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
