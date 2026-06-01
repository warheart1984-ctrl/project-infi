"use client";
              onChange={(event) => setInput(event.target.value)}
              rows={6}
              className="w-full rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-zinc-100 outline-none focus:border-zinc-600"
              placeholder="Write one honest sentence about your state..."
            />

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={loading}
                className="rounded-2xl border border-zinc-700 px-5 py-3 font-medium transition hover:border-zinc-500 disabled:opacity-50"
              >
                {loading ? "Reading..." : "Generate Reading"}
              </button>
              {error ? <span className="text-sm text-red-400">{error}</span> : null}
            </div>
          </form>
        </div>

        <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <h2 className="text-2xl font-semibold">Current Reading</h2>
            <div className="rounded-full border border-zinc-700 px-3 py-1 text-sm capitalize">
              Streak: {streak} day
            </div>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
              <div className="text-sm text-zinc-400">State</div>
              <div className="mt-2 text-lg font-medium capitalize">{reading.state}</div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
              <div className="text-sm text-zinc-400">Dominant Archetype</div>
              <div className="mt-2 text-lg font-medium capitalize">{reading.dominantArchetype}</div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
              <div className="text-sm text-zinc-400">Trial</div>
              <div className="mt-2 text-lg font-medium">{reading.trial}</div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
              <div className="text-sm text-zinc-400">Next Action</div>
              <div className="mt-2 text-lg font-medium">{reading.nextAction}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-lg">
        <h2 className="text-2xl font-semibold">Recent Entries</h2>
        <div className="mt-4 space-y-3">
          {entries.length === 0 ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-zinc-400">
              No entries yet. Generate your first reading.
            </div>
          ) : (
            entries.slice(0, 5).map((entry) => (
              <div key={entry.createdAt} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
                <div className="text-sm text-zinc-400 capitalize">{entry.reading.state}</div>
                <div className="mt-2 text-sm text-zinc-300">{entry.input}</div>
                <div className="mt-3 text-xs text-zinc-500">{new Date(entry.createdAt).toLocaleString()}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}