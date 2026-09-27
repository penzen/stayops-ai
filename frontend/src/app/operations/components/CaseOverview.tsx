import type { QueueEntry } from "../types";
import { operatorName } from "../utils";

type CaseOverviewProps = {
  entry: QueueEntry;
  isActionLoading: boolean;
  onClaimCase: () => void;
};

export default function CaseOverview({
  entry,
  isActionLoading,
  onClaimCase,
}: CaseOverviewProps) {
  return (
    <>
     <div className="border-b border-zinc-800 p-6">

                  <div className="flex items-start justify-between gap-6">

                    <div>

                      <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
                        {
                          entry.case.case_id
                        }
                      </p>

                      <h2 className="mt-2 text-xl font-semibold capitalize">
                        {
                          entry.case.category
                        }{" "}
                        Case
                      </h2>

                      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
                        {
                          entry.case.summary ??
                          entry.handoff.reason
                        }
                      </p>

                    </div>


                    <div className="flex items-center gap-3">

                    <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-xs text-violet-300">
                        waiting_human
                    </span>

                    {!entry.operator && (

                        <button
                        onClick={() =>
                            void onClaimCase()
                        }
                        disabled={isActionLoading}
                        className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                        {isActionLoading
                            ? "Claiming..."
                            : "Claim Case"}
                        </button>

                    )}

                    </div>

                  </div>

                </div>


                <div className="grid gap-6 p-6 md:grid-cols-2">

                  {/* GUEST */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Guest
                    </p>

                    <p className="mt-2 font-medium">
                      {entry.guest
                        ? `${entry.guest.first_name} ${entry.guest.last_name}`
                        : "Unknown guest"}
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      {
                        entry.case.booking_id
                      }
                    </p>

                  </div>


                  {/* PROPERTY */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Property
                    </p>

                    <p className="mt-2 font-medium">
                      {
                        entry.property?.title ??
                        entry.case.property_id
                      }
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      {
                        entry.case.property_id
                      }
                    </p>

                  </div>


                  {/* OWNER */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Current owner
                    </p>

                    <p
                      className={`mt-2 font-medium ${
                        entry.operator
                          ? "text-emerald-300"
                          : "text-amber-300"
                      }`}
                    >
                      {operatorName(
                        entry.operator
                      )}
                    </p>

                    {entry.operator?.team_role && (

                      <p className="mt-1 text-xs text-zinc-500">
                        {
                          entry.operator.team_role
                        }
                      </p>

                    )}

                  </div>


                  {/* HANDOFF */}

                                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Handoff reason
                    </p>

                    <p className="mt-2 text-sm leading-relaxed text-zinc-300">
                      {
                        entry.handoff.reason ??
                        "Human intervention required."
                      }
                    </p>

                  </div>

                </div>

    </>
  );
}