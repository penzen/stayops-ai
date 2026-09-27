import type {
  QueueEntry,
} from "../types";

import {
  priorityClasses,
} from "../utils";


type EscalationPanelProps = {
  entry: QueueEntry;

  isActionLoading: boolean;

  onResolveEscalation: (
    escalationId: string
  ) => void;
};


export default function EscalationPanel({
  entry,
  isActionLoading,
  onResolveEscalation,
}: EscalationPanelProps) {
  return (
    <div className="border-t border-zinc-800 p-6">

      <h3 className="font-medium">
        Escalations
      </h3>


      <div className="mt-4 space-y-3">

        {entry.escalations.length === 0 ? (

          <p className="text-sm text-zinc-500">
            No linked escalations.
          </p>

        ) : (

          entry.escalations.map(
            (escalation) => (

              <div
                key={
                  escalation.escalation_id
                }
                className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4"
              >

                <div className="flex items-center justify-between gap-4">

                  <span className="text-sm font-medium capitalize">
                    {
                      escalation.category
                    }
                  </span>


                  <span
                    className={`rounded-full border px-2.5 py-1 text-xs capitalize ${priorityClasses(
                      escalation.priority
                    )}`}
                  >
                    {
                      escalation.priority
                    }
                  </span>

                </div>


                <p className="mt-3 text-sm leading-relaxed text-zinc-400">
                  {
                    escalation.reason
                  }
                </p>


                {entry.operator &&
                  escalation.status ===
                    "open" && (

                    <div className="mt-4 border-t border-zinc-800 pt-4">

                      <button
                        onClick={() =>
                          void onResolveEscalation(
                            escalation.escalation_id
                          )
                        }
                        disabled={
                          isActionLoading
                        }
                        className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                      >
                        {isActionLoading
                          ? "Resolving..."
                          : "Resolve Escalation"}
                      </button>

                    </div>

                  )}

              </div>

            )
          )

        )}

      </div>

    </div>
  );
}