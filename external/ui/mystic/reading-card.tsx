import { MythicReading } from "@/lib/types";

export function ReadingCard({ reading }: { reading: MythicReading }) {
  return (
    <div className="xl:col-span-2 rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-semibold">Today&apos;s Reading</h2>
          <p className="text-zinc-400 mt-1">The current mythic interpretation of your inner state.</p>
        </div>
        <div className="rounded-2xl border border-zinc-700 px-4 py-2 text-sm text-zinc-300">
          Active rule: {reading.nextAction}
        </div>
      </div>

      <div className="mt-6 grid md:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-4">
          <div className="text-sm text-zinc-400">Trial</div>
          <div className="mt-3 text-lg font-medium">{reading.trial}</div>
        </div>

        <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-4">
          <div className="text-sm text-zinc-400">Meaning</div>
          <div className="mt-3 text-lg font-medium">{reading.meaning}</div>
        </div>

        <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-4 md:col-span-2">
          <div className="text-sm text-zinc-400">Risk</div>
          <div className="mt-3 text-lg font-medium">{reading.risk}</div>
        </div>
      </div>
    </div>
  );
}