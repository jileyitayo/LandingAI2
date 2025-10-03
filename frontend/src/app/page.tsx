export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-primary-50 to-white p-24">
      <div className="text-center">
        <h1 className="mb-4 text-6xl font-bold text-primary-600">
          SiteSmith
        </h1>
        <p className="mb-8 text-2xl text-gray-700">
          AI Website Builder for African Entrepreneurs
        </p>
        <div className="flex gap-4 justify-center">
          <button className="rounded-lg bg-primary px-6 py-3 font-semibold text-white transition hover:bg-primary-600">
            Get Started
          </button>
          <button className="rounded-lg border-2 border-secondary bg-white px-6 py-3 font-semibold text-secondary transition hover:bg-secondary-50">
            Learn More
          </button>
        </div>
      </div>
    </main>
  );
}

