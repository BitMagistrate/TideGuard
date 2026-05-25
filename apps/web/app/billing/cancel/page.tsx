export default function BillingCancel() {
  return (
    <main className="max-w-md mx-auto px-6 py-20 text-center">
      <h1 className="text-2xl font-bold">Checkout cancelled</h1>
      <p className="text-zinc-500 mt-2">No charge was made. You can return to <a className="underline" href="/pricing">pricing</a>.</p>
    </main>
  );
}
