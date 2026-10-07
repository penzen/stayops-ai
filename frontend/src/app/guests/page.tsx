import Link from "next/link";

export default function GuestsPage() {
  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">Guests</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">Guest directory</h1>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              The Guests route is wired into the V5 shell. The searchable
              directory and guest detail experience will be implemented in M6.
            </p>
          </div>

          <Link
            href="/guest-ops"
            className="inline-flex items-center justify-center rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-800"
          >
            Open Guest Ops
          </Link>
        </div>

        <section className="mt-8 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50">
          <div className="grid grid-cols-[1.2fr_1fr_1fr_auto] gap-4 border-b border-zinc-800 px-5 py-3 text-[11px] font-medium uppercase tracking-[0.14em] text-zinc-600">
            <span>Guest</span>
            <span>Reservation</span>
            <span>Status</span>
            <span>Cases</span>
          </div>

          <div className="flex min-h-64 items-center justify-center px-6 text-center">
            <div className="max-w-sm">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950 text-zinc-500">
                ···
              </div>
              <p className="mt-4 text-sm font-medium text-zinc-300">Directory coming in M6</p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-600">
                V5 will populate this workspace with session-scoped guests,
                reservations, active Cases and global search.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
