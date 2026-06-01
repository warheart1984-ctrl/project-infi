onst timeline = [
  { step: "Despair", detail: "Felt trapped in self-blame" },
  { step: "Witness", detail: "Recognized guilt instead of identity" },
  { step: "Learner", detail: "Saw pain → reaction → regret" },
  { step: "Builder", detail: "Created a new response rule" },
];

export function TimelineCard() {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
      <h2 className="text-2xl font-semibold">Transformation Timeline</h2>
      <div className="mt-5 space-y-4">
        {timeline.map((entry, index) => (
          <div key={entry.step} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="h-10 w-10 rounded-full border border-zinc-700 bg-zinc-950 flex items-center justify-center text-sm">
                {index + 1}
              </div>
              {index < timeline.length - 1 && <div className="w-px flex-1 bg-zinc-800 mt-2" />}
            </div>
            <div className="pb-6">
              <div className="text-lg font-medium">{entry.step}</div>
              <div className="text-zinc-400 mt-1">{entry.detail}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}