import { MythicReading } from "@/lib/types";

export function MetricsGrid({ reading, streak }: { reading: MythicReading; streak: number }) {
  const metrics = [
    { label: "State", value: reading.state },
    { label: "Dominant", value: reading.dominantArchetype },
    { label: "Opposing", value: reading.opposingArchetype },
    { label: "Streak", value: `${streak} day` },
  ];

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-5 shadow-lg"
        >
          <div className="text-sm text-zinc-400 capitalize">{metric.label}</div>
          <div className="mt-2 text-xl font-medium capitalize">{metric.value}</div>
        </div>
      ))}
    </section>
  );
}