import Link from "next/link";
import Quiz from "@/components/Quiz";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type QuizQuestion = { q: string; options: string[]; correct: number; explain: string };
type Lesson = {
  slug: string;
  title: string;
  content_md: string;
  quiz: { questions: QuizQuestion[] };
  xp_reward: number;
};

async function fetchLesson(slug: string): Promise<Lesson | null> {
  try {
    const res = await fetch(`${API}/education/lessons/${slug}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function LessonPage({ params }: { params: { slug: string } }) {
  const lesson = await fetchLesson(params.slug);
  if (!lesson) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-12">
        <Link href="/learn" className="text-teal-700 text-sm">← Lessons</Link>
        <h1 className="text-3xl font-bold mt-2">Lesson not loaded</h1>
        <p className="text-zinc-600 mt-2">
          The API is not reachable. Make sure the backend is running and the DB is seeded.
        </p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <Link href="/learn" className="text-teal-700 text-sm">← Lessons</Link>
      <h1 className="text-3xl md:text-4xl font-bold mt-2">{lesson.title}</h1>
      <article className="prose dark:prose-invert mt-6 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">
        {lesson.content_md}
      </article>

      {lesson.quiz?.questions?.length > 0 && (
        <section className="mt-12 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-2xl font-semibold mb-4">Quick quiz</h2>
          <Quiz questions={lesson.quiz.questions} lessonSlug={lesson.slug} />
        </section>
      )}
    </main>
  );
}
