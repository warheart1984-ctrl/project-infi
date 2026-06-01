import { DailyProtocol } from "@/components/daily-protocol";
  opposingArchetype: "shadow",
  trial: "Reaction vs control",
  nextAction: "Pause for 10 seconds before acting when anger rises.",
  meaning: "You are replacing reaction with deliberate choice.",
  risk: "Ignoring the pause can reactivate regret loops.",
};

export default function HomePage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="space-y-3">
          <div className="inline-flex items-center rounded-full border border-zinc-700 px-3 py-1 text-sm text-zinc-300">
            Mythic AI • Next.js V1
          </div>
          <h1 className="text-4xl md:text-6xl font-semibold tracking-tight">Evolution Dashboard</h1>
          <p className="text-zinc-400 max-w-3xl text-base md:text-lg">
            A mythic reflection system that turns emotional states into structure, trial, and action.
          </p>
        </header>

        <MetricsGrid reading={initialReading} streak={1} />

        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <ReadingCard reading={initialReading} />
          <DailyProtocol />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TimelineCard />
          <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
            <h2 className="text-2xl font-semibold">Future Modules</h2>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              {[
                "Memory system",
                "Daily scoring",
                "Archetype trends",
                "Crisis stabilization mode",
                "Reflection history",
                "AI-guided responses",
              ].map((item) => (
                <div key={item} className="rounded-xl border border-zinc-800 px-3 py-3 bg-zinc-950">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <JournalForm />
      </div>
    </main>
  );
}