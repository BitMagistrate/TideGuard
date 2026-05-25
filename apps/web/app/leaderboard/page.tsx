import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Entry = { rank: number; name: string; xp: number };

async function fetchLeaderboard(): Promise<Entry[]> {
  try {
    const res = await fetch(`${API}/leaderboard`, { next: { revalidate: 30 } });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function LeaderboardPage() {
  const entries = await fetchLeaderboard();
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-6 py-12">
      <Link href="/" className="text-teal-700 text-sm">← Back home</Link>
      <h1 className="text-4xl font-bold mt-2 mb-8">Leaderboard</h1>
      {entries.length === 0 ? (
        <p className="text-zinc-600 dark:text-zinc-400">
          No entries yet. Be the first to submit a report or complete a lesson!
        </p>
      ) : (
        <ol className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {entries.map((e) => (
            <li key={e.rank} className="py-3 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <span className="font-bold text-zinc-400 w-10">#{e.rank}</span>
                <span className="font-medium">{e.name}</span>
              </div>
              <span className="text-teal-700 font-semibold">{e.xp} XP</span>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
