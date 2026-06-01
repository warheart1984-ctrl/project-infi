export default function MythicAIDashboard() {
  const todayReading = {
    state: "Awakening / Control",
    dominantArchetypes: ["Witness", "Hero", "Builder"],
    shadow: "Judge / Reaction",
    trial: "Reaction vs control",
    nextRule: "Take 10 seconds to think before acting.",
    streak: 1,
  };

  const timeline = [
    { step: "Despair", detail: "Felt trapped in self-blame" },
    { step: "Witness", detail: "Recognized guilt instead of identity" },
    { step: "Learner", detail: "Saw pain → reaction → regret" },
    { step: "Builder", detail: "Created a new response rule" },
  ];

  const dailyProtocol = [
    "Drink water",
    "Eat something real",
    "Move your body",
    "Pause 10 seconds before reacting",
    "Write one honest sentence at night",
  ];

  const metrics = [
    { label: "State", value: todayReading.state },
    { label: "Streak", value: `${todayReading.streak} day` },
    { label: "Current Trial", value: todayReading.trial },
    { label: "Shadow", value: todayReading.shadow },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="space-y-3">
          <div className="inline-flex items-center rounded-full border border-zinc-700 px-3 py-1 text-sm text-zinc-300">
            Mythic AI • Dashboard V1
          </div>
          <h1 className="text-4xl md:text-6xl font-semibold tracking-tight">
            Evolution Dashboard
          </h1>
          <p className="text-zinc-400 max-w-3xl text-base md:text-lg">
            A personal transformation system that turns emotional states into
            structure, reflection, and action.
          </p>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-5 shadow-lg"
            >
              <div className="text-sm text-zinc-400">{metric.label}</div>
              <div className="mt-2 text-xl font-medium">{metric.value}</div>
            </div>
          ))}
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h2 className="text-2xl font-semibold">Today’s Reading</h2>
                <p className="text-zinc-400 mt-1">
                  The current mythic interpretation of your inner state.
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-700 px-4 py-2 text-sm text-zinc-300">
                Active rule: {todayReading.nextRule}
              </div>
            </div>

            <div className="mt-6 grid md:grid-cols-2 gap-4">
              <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-4">
                <div className="text-sm text-zinc-400">Dominant Archetypes</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {todayReading.dominantArchetypes.map((a) => (
                    <span
                      key={a}
                      className="rounded-full border border-zinc-700 px-3 py-1 text-sm"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-4">
                <div className="text-sm text-zinc-400">Next Action</div>
                <div className="mt-3 text-lg font-medium">
                  Pause for 10 seconds before acting when anger rises.
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
            <h2 className="text-2xl font-semibold">Daily Protocol</h2>
            <div className="mt-4 space-y-3">
              {dailyProtocol.map((item, index) => (
                <div
                  key={item}
                  className="rounded-2xl border border-zinc-800 bg-zinc-950 px-4 py-3 flex items-center gap-3"
                >
                  <div className="h-8 w-8 rounded-full border border-zinc-700 flex items-center justify-center text-sm text-zinc-300">
                    {index + 1}
                  </div>
                  <div>{item}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
            <h2 className="text-2xl font-semibold">Transformation Timeline</h2>
            <div className="mt-5 space-y-4">
              {timeline.map((entry, index) => (
                <div key={entry.step} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-10 w-10 rounded-full border border-zinc-700 bg-zinc-950 flex items-center justify-center text-sm">
                      {index + 1}
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="w-px flex-1 bg-zinc-800 mt-2" />
                    )}
                  </div>
                  <div className="pb-6">
                    <div className="text-lg font-medium">{entry.step}</div>
                    <div className="text-zinc-400 mt-1">{entry.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
            <h2 className="text-2xl font-semibold">Journal Input</h2>
            <p className="text-zinc-400 mt-1">
              The engine starts with one honest sentence.
            </p>
            <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-zinc-300">
              “Right now I am in the state of awakening and control because I
              created a new rule instead of staying trapped in reaction.”
            </div>

            <div className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
              <div className="text-sm text-zinc-400">Suggested future modules</div>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                {[
                  "Memory system",
                  "Daily scoring",
                  "Archetype trends",
                  "Crisis stabilization mode",
                  "Reflection history",
                  "AI-guided responses",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-xl border border-zinc-800 px-3 py-2"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
