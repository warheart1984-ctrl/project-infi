const dailyProtocol = [
  "Drink water",
  "Eat something real",
  "Move your body",
  "Pause 10 seconds before reacting",
  "Write one honest sentence at night",
];

export function DailyProtocol() {
  return (
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
  );
}