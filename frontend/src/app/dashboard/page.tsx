export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
            Overview
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            StayOps command center
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-zinc-500">
            This route is now part of the V5 application shell. The operational
            dashboard itself will be built in M5 after demo onboarding and
            session isolation are in place.
          </p>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            ["Guest activity", "Guest and reservation activity will surface here."],
            ["Active Cases", "Live Case workload and ownership will surface here."],
            ["Human handoffs", "Escalations and financial reviews will surface here."],
          ].map(([title, description]) => (
            <section key={title} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="h-8 w-8 rounded-lg border border-zinc-800 bg-zinc-950" />
              <h2 className="mt-5 text-sm font-semibold text-zinc-200">{title}</h2>
              <p className="mt-2 text-xs leading-relaxed text-zinc-600">{description}</p>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}
