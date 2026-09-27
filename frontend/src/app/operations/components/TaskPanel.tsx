import type {
  QueueEntry,
  Technician,
} from "../types";


type TaskPanelProps = {
  entry: QueueEntry;

  technicians: Technician[];

  selectedWorkerId: string;

  isActionLoading: boolean;

  onWorkerChange: (
    workerId: string
  ) => void;

  onAssignTask: (
    taskId: string
  ) => void;

  onCompleteTask: (
    taskId: string
  ) => void;
};


export default function TaskPanel({
  entry,
  technicians,
  selectedWorkerId,
  isActionLoading,
  onWorkerChange,
  onAssignTask,
  onCompleteTask,
}: TaskPanelProps) {
  return (
    <div className="border-t border-zinc-800 p-6">

      <h3 className="font-medium">
        Operational work
      </h3>


      <div className="mt-4 space-y-3">

        {entry.tasks.length === 0 ? (

          <p className="text-sm text-zinc-500">
            No linked tasks.
          </p>

        ) : (

          entry.tasks.map(
            (task) => (

              <div
                key={task.task_id}
                className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4"
              >

                <div className="flex items-center justify-between gap-4">

                  <div>

                    <p className="text-sm font-medium">
                      {task.title}
                    </p>

                    <p className="mt-1 text-xs capitalize text-zinc-500">
                      {task.category}
                    </p>

                  </div>


                  <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs capitalize text-zinc-300">
                    {task.task_status}
                  </span>

                </div>


                {/* TECHNICIAN ASSIGNMENT */}

                {entry.operator &&
                  task.task_status ===
                    "open" && (

                    <div className="mt-4 border-t border-zinc-800 pt-4">

                      <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                        Assigned technician
                      </p>


                      {task.assigned_to ? (

                        <div className="mt-2 flex items-center justify-between gap-4">

                          <p className="text-sm font-medium text-emerald-300">

                            {(() => {
                              const worker =
                                technicians.find(
                                  (
                                    item
                                  ) =>
                                    item.team_id ===
                                    task.assigned_to
                                );

                              if (!worker) {
                                return task.assigned_to;
                              }

                              const name = [
                                worker.first_name,
                                worker.last_name,
                              ]
                                .filter(Boolean)
                                .join(" ");

                              return (
                                name ||
                                worker.team_id
                              );
                            })()}

                          </p>


                          <button
                            onClick={() =>
                              void onCompleteTask(
                                task.task_id
                              )
                            }
                            disabled={
                              isActionLoading
                            }
                            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                          >
                            {isActionLoading
                              ? "Completing..."
                              : "Mark Complete"}
                          </button>

                        </div>

                      ) : (

                        <div className="mt-2 flex gap-2">

                          <select
                            value={
                              selectedWorkerId
                            }
                            onChange={(
                              event
                            ) =>
                              onWorkerChange(
                                event.target
                                  .value
                              )
                            }
                            disabled={
                              technicians.length ===
                              0
                            }
                            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-violet-500/60"
                          >

                            {technicians.map(
                              (
                                worker
                              ) => {
                                const name =
                                  [
                                    worker.first_name,
                                    worker.last_name,
                                  ]
                                    .filter(
                                      Boolean
                                    )
                                    .join(
                                      " "
                                    );

                                return (
                                  <option
                                    key={
                                      worker.team_id
                                    }
                                    value={
                                      worker.team_id
                                    }
                                  >
                                    {name ||
                                      worker.team_id}
                                  </option>
                                );
                              }
                            )}

                          </select>


                          <button
                            onClick={() =>
                              void onAssignTask(
                                task.task_id
                              )
                            }
                            disabled={
                              isActionLoading ||
                              !selectedWorkerId
                            }
                            className="rounded-lg bg-violet-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-violet-400 disabled:opacity-50"
                          >
                            {isActionLoading
                              ? "Assigning..."
                              : "Assign"}
                          </button>

                        </div>

                      )}

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