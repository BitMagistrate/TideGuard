export default function BillingSuccess() {
  return (
    <main className="max-w-md mx-auto px-6 py-20 text-center">
      <h1 className="text-3xl font-bold text-teal-600">Welcome!</h1>
      <p className="text-zinc-500 mt-2">
        Your subscription is active. You can now create API keys and start sending requests.
      </p>
      <a href="/dashboard" className="inline-block mt-6 bg-teal-600 text-white rounded-md px-4 py-2">Open dashboard</a>
    </main>
  );
}
