"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Question = { q: string; options: string[]; correct: number; explain: string };

export default function Quiz({
  questions,
  lessonSlug,
}: {
  questions: Question[];
  lessonSlug: string;
}) {
  const [i, setI] = useState(0);
  const [score, setScore] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [done, setDone] = useState(false);
  const [serverResp, setServerResp] = useState<string | null>(null);
  const q = questions[i];

  async function next() {
    const isCorrect = picked === q.correct;
    const nextScore = score + (isCorrect ? 1 : 0);
    setScore(nextScore);
    setPicked(null);

    if (i + 1 === questions.length) {
      setDone(true);
      try {
        const res = await fetch(`${API}/education/progress`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lesson_slug: lessonSlug, score: nextScore / questions.length }),
        });
        if (res.ok) {
          const data = await res.json();
          setServerResp(`+${data.xp_awarded} XP awarded · total ${data.xp_total}`);
        }
      } catch {
        setServerResp(null);
      }
    } else {
      setI(i + 1);
    }
  }

  if (done) {
    return (
      <div>
        <p className="text-xl font-semibold mb-2">
          Score: {score} / {questions.length}
        </p>
        {serverResp && <p className="text-teal-700">{serverResp}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-zinc-500">
        Question {i + 1} / {questions.length}
      </div>
      <h3 className="text-xl font-medium">{q.q}</h3>
      <div className="grid gap-2">
        {q.options.map((o, k) => (
          <button
            key={k}
            onClick={() => setPicked(k)}
            className={`text-left p-3 rounded-lg border transition ${
              picked === k
                ? "border-teal-500 bg-teal-50 dark:bg-teal-900/30"
                : "border-zinc-200 dark:border-zinc-800 hover:border-teal-400"
            }`}
          >
            {o}
          </button>
        ))}
      </div>
      {picked !== null && <p className="text-sm text-zinc-600 dark:text-zinc-400">{q.explain}</p>}
      <button
        onClick={next}
        disabled={picked === null}
        className="px-5 py-2 bg-teal-600 text-white rounded-lg disabled:opacity-50"
      >
        {i + 1 === questions.length ? "Finish" : "Next"}
      </button>
    </div>
  );
}
