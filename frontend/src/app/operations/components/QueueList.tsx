import type {
  QueueEntry,
} from "../types";

import {
  priorityClasses,
} from "../utils";


type QueueListProps = {
  queue: QueueEntry[];
  isLoading: boolean;
  selectedCaseId: string | null;
  onSelectCase: (
    caseId: string
  ) => void;
};


export default function QueueList({
  queue,
  isLoading,
  selectedCaseId,
  onSelectCase,
}: QueueListProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60">

      <div className="border-b border-zinc-800 px-5 py-4">

        <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
          Human queue
        </p>

        <h2 className="mt-1 font-semibold">
          Cases requiring attention
        </h2>

      </div>


      <div className="max-h-[760px] overflow-y-auto">

        {isLoading &&
        queue.length === 0 ? (

          <div className="p-8 text-center text-sm text-zinc-500">
            Loading queue...
          </div>

        ) : queue.length === 0 ? (

          <div className="p-10 text-center">

            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-300">
              ✓
            </div>

            <p className="mt-4 text-sm font-medium">
              Queue clear
            </p>

            <p className="mt-1 text-xs text-zinc-500">
              No Cases are waiting for human action.
            </p>

          </div>

        ) : (

          queue.map(
            (entry) => {
              const selected =
                selectedCaseId ===
                entry.case.case_id;

              const openTaskCount =
                entry.tasks.filter(
                  (task) =>
                    task.task_status ===
                    "open"
                ).length;

              const openEscalationCount =
                entry.escalations.filter(
                  (escalation) =>
                    escalation.status ===
                    "open"
                ).length;

              return (
                <button
                  key={
                    entry.case.case_id
                  }
                  onClick={() =>
                    onSelectCase(
                      entry.case.case_id
                    )
                  }
                  className={`w-full border-b border-zinc-800 p-5 text-left transition last:border-b-0 ${
                    selected
                      ? "bg-zinc-800/80"
                      : "hover:bg-zinc-800/40"
                  }`}
                >

                  <div className="flex items-start justify-between gap-4">

                    <div>

                      <div className="flex items-center gap-2">

                        <span className="text-sm font-semibold capitalize">
                          {
                            entry.case.category
                          }
                        </span>

                        {entry.handoff.priority && (
                          <span
                            className={`rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${priorityClasses(
                              entry.handoff.priority
                            )}`}
                          >
                            {
                              entry.handoff.priority
                            }
                          </span>
                        )}

                      </div>


                      <p className="mt-1 text-xs text-zinc-500">
                        {entry.guest
                          ? `${entry.guest.first_name} ${entry.guest.last_name}`
                          : entry.case.booking_id}
                      </p>

                    </div>


                    <span
                      className={
                        entry.operator
                          ? "rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-300"
                          : "rounded-full border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-300"
                      }
                    >
                      {entry.operator
                        ? "Claimed"
                        : "Unclaimed"}
                    </span>

                  </div>


                  <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-zinc-400">
                    {
                      entry.case.summary ??
                      entry.handoff.reason ??
                      "Human intervention required."
                    }
                  </p>


                  <div className="mt-4 flex items-center gap-4 text-[11px] text-zinc-600">

                    <span>
                      {openTaskCount}{" "}
                      open tasks
                    </span>

                    <span>
                      {openEscalationCount}{" "}
                      escalations
                    </span>

                  </div>

                </button>
              );
            }
          )

        )}

      </div>

    </section>
  );
}