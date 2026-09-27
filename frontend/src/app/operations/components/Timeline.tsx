import type { CaseEvent } from "../types";
import { formatEventTime } from "../utils";

type TimelineProps = {
  timeline: CaseEvent[];
  isLoading: boolean;
};


export default function Timeline({
  timeline,
  isLoading,
}: TimelineProps) {
  return (


 <div className="border-t border-zinc-800 p-6">

                <div className="flex items-center justify-between">

                    <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Audit trail
                    </p>

                    <h3 className="mt-1 font-medium">
                        Case Timeline
                    </h3>
                    </div>

                    <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
                    {timeline.length} events
                    </span>

                </div>


                <div className="mt-5">

                    {isLoading ? (

                    <p className="text-sm text-zinc-500">
                        Loading timeline...
                    </p>

                    ) : timeline.length === 0 ? (

                    <div className="rounded-xl border border-dashed border-zinc-800 py-6 text-center">

                        <p className="text-sm text-zinc-500">
                        No Case events recorded.
                        </p>

                    </div>

                    ) : (

                    timeline.map(
                        (event, index) => (

                        <div
                            key={
                            event.case_event_id
                            }
                            className="relative flex gap-4 pb-6 last:pb-0"
                        >

                            {index <
                            timeline.length - 1 && (

                            <div className="absolute left-[7px] top-5 h-full w-px bg-zinc-800" />

                            )}


                            <div className="relative z-10 mt-1.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/10">

                            <div className="h-1.5 w-1.5 rounded-full bg-violet-400" />

                            </div>


                            <div className="min-w-0 flex-1">

                            <div className="flex flex-wrap items-center justify-between gap-2">

                                <p className="text-sm font-medium text-zinc-200">
                                {event.summary}
                                </p>

                                <span className="text-[11px] text-zinc-600">
                                {formatEventTime(
                                    event.created_at
                                )}
                                </span>

                            </div>


                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">

                                <span className="capitalize">
                                {event.actor_type}
                                </span>

                                {event.actor_id && (
                                <>
                                    <span>·</span>

                                    <span>
                                    {event.actor_id}
                                    </span>
                                </>
                                )}

                                <span>·</span>

                                <span className="font-mono text-[11px] text-zinc-600">
                                {event.event_type}
                                </span>

                            </div>

                            </div>

                        </div>

                        )
                    )

                    )}

                </div>

                </div>   );}
