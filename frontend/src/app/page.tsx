import Link from "next/link";

function ArrowIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M5 12h14M14 7l5 5-5 5" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path d="m5 12 4 4L19 6" />
    </svg>
  );
}

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-[1280px] flex-col px-6">
        <header className="flex items-center justify-between py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold tracking-tight text-zinc-950">
              SO
            </div>

            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold tracking-tight">StayOps</p>
                <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-violet-300">
                  Demo
                </span>
              </div>
              <p className="text-[11px] text-zinc-600">
                AI guest operations
              </p>
            </div>
          </div>

          <Link
            href="/guest-ops"
            className="rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-xs font-semibold text-zinc-300 transition hover:border-zinc-700 hover:text-white"
          >
            Enter demo
          </Link>
        </header>

        <section className="grid flex-1 items-center gap-12 py-14 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Interactive demo · no account required
            </div>

            <h1 className="mt-6 max-w-xl text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
              Guest operations that can reason, act and hand off safely.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-zinc-400">
              StayOps is an agentic operations workspace for short-term rental
              teams. The agent handles guest issues, uses operational tools,
              creates work and escalates decisions that require a human.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="/guest-ops"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200"
              >
                Try interactive demo
                <ArrowIcon />
              </Link>

              <span className="text-xs text-zinc-600">
                Uses fictional guest and reservation data
              </span>
            </div>

            <div className="mt-9 grid gap-3 text-sm text-zinc-400 sm:grid-cols-3">
              {[
                "Bounded tool execution",
                "Human handoffs",
                "Auditable operations",
              ].map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950 text-emerald-300">
                    <CheckIcon />
                  </span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-zinc-800 bg-zinc-950/60 p-3 shadow-2xl shadow-black/30">
            <div className="rounded-[22px] border border-zinc-800 bg-[#0d0d10] p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
                    Start demo
                  </p>
                  <h2 className="mt-2 text-xl font-semibold tracking-tight">
                    Choose how to enter StayOps
                  </h2>
                </div>

                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950 text-zinc-500">
                  ✦
                </div>
              </div>

              <div className="mt-6 space-y-3">
                <Link
                  href="/guest-ops"
                  className="group block rounded-2xl border border-blue-500/25 bg-blue-500/10 p-5 transition hover:border-blue-400/40 hover:bg-blue-500/[0.14]"
                >
                  <div className="flex items-start justify-between gap-5">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-blue-100">
                          Use a sample stay
                        </h3>
                        <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-emerald-300">
                          Ready
                        </span>
                      </div>

                      <p className="mt-2 text-xs leading-5 text-zinc-500">
                        Jump directly into a prepared reservation and test
                        plumbing, heating, escalation and refund workflows.
                      </p>
                    </div>

                    <span className="mt-1 text-blue-300 transition group-hover:translate-x-1">
                      <ArrowIcon />
                    </span>
                  </div>
                </Link>

                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                  <div className="flex items-start justify-between gap-5">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-zinc-300">
                          Create a fictional guest
                        </h3>
                        <span className="rounded-full border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-zinc-500">
                          Next
                        </span>
                      </div>

                      <p className="mt-2 text-xs leading-5 text-zinc-600">
                        Build a custom guest and reservation, then run that stay
                        through the same operational workflow.
                      </p>
                    </div>

                    <span className="mt-1 text-zinc-700">
                      <ArrowIcon />
                    </span>
                  </div>

                  <p className="mt-4 border-t border-zinc-800 pt-3 text-[11px] text-zinc-700">
                    Custom guest creation is enabled in the next V5 milestone.
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-xl border border-zinc-800/80 bg-zinc-950/60 px-4 py-3">
                <p className="text-[11px] leading-5 text-zinc-600">
                  Demo data is fictional. The public demo does not require a
                  registration or login.
                </p>
              </div>
            </div>
          </div>
        </section>

        <footer className="flex flex-col gap-2 border-t border-zinc-900 py-5 text-[11px] text-zinc-700 sm:flex-row sm:items-center sm:justify-between">
          <span>StayOps · V5 interactive product demo</span>
          <span>Agent decisions are bounded by deterministic operational services.</span>
        </footer>
      </div>
    </main>
  );
}
