"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";


type ChatMessage = {
  sender: "guest" | "agent";
  text: string;
};

type StoredMessage = {
  message_id: string;
  booking_id: string;
  guest_id: string;
  sender_type: string;
  message_text: string;
  channel: string;
  created_at: string;
};

type Task = {
  task_id: string;
  booking_id: string | null;
  property_id: string;
  category: string;
  title: string;
  task_status: string;
};


type Escalation = {
  escalation_id: string;
  booking_id: string | null;
  property_id: string;
  category: string;
  reason: string;
  priority: string;
  status: string;
};


type DemoStay = {
  booking_id: string;
  guest_id: string;
  property_id: string;

  check_in: string;
  check_out: string;

  book_status: string;

  first_name: string;
  last_name: string;

  guest_lang: string;
  locale: string;

  property_title: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


function formatDate(
  dateString: string
) {
  const date = new Date(
    dateString.replace(" ", "T")
  );

  return date.toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


function languageLabel(
  language: string
) {
  if (language === "en") {
    return "English";
  }

  if (language === "fr") {
    return "Français";
  }

  if (language === "de") {
    return "Deutsch";
  }

  return language.toUpperCase();
}


function languageCode(
  language: string
) {
  if (language === "en") {
    return "EN";
  }

  if (language === "fr") {
    return "FR";
  }

  if (language === "de") {
    return "DE";
  }

  return language.toUpperCase();
}


function priorityClasses(
  priority: string
) {
  const normalized =
    priority.toLowerCase();

  if (
    normalized === "high" ||
    normalized === "critical"
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (normalized === "medium") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  return "border-zinc-700 bg-zinc-800 text-zinc-300";
}


export default function Home() {
  const [
    demoStays,
    setDemoStays,
  ] = useState<DemoStay[]>([]);

  const [
    selectedBookingId,
    setSelectedBookingId,
  ] = useState("");

  const [message, setMessage] =
    useState("");

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [tasks, setTasks] =
    useState<Task[]>([]);

  const [
    escalations,
    setEscalations,
  ] = useState<Escalation[]>([]);

  const [
    activities,
    setActivities,
  ] = useState<string[]>([]);

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    isResetting,
    setIsResetting,
  ] = useState(false);

  const [
    isOperationsLoading,
    setIsOperationsLoading,
  ] = useState(true);


  const selectedStay =
    demoStays.find(
      (stay) =>
        stay.booking_id ===
        selectedBookingId
    ) ?? null;


  // ---------------------------------------------------------
  // LOAD DEMO STAYS
  // ---------------------------------------------------------

  const loadDemoStays =
    useCallback(async () => {
      try {
        const response =
          await fetch(
            `${API_URL}/demo/stays`
          );

        if (!response.ok) {
          throw new Error(
            `Demo stays request failed: ${response.status}`
          );
        }

        const stays: DemoStay[] =
          await response.json();

        setDemoStays(stays);

        if (stays.length > 0) {
          const englishStay =
            stays.find(
              (stay) =>
                stay.guest_lang ===
                "en"
            );

          const defaultStay =
            englishStay ??
            stays[0];

          setSelectedBookingId(
            (current) =>
              current ||
              defaultStay.booking_id
          );
        }
      } catch (error) {
        console.error(
          "Unable to load demo stays:",
          error
        );
      }
    }, []);


  // ---------------------------------------------------------
  // LOAD TASKS + ESCALATIONS
  // ---------------------------------------------------------

const loadConversation =
  useCallback(
    async (
      bookingId: string
    ) => {
      try {
        const response =
          await fetch(
            `${API_URL}/reservations/${bookingId}/messages`,
            {
              cache: "no-store",
            }
          );

        if (!response.ok) {
          throw new Error(
            `Messages request failed: ${response.status}`
          );
        }

        const data: StoredMessage[] =
          await response.json();

        setMessages(
          data.map((item) => ({
            sender:
              item.sender_type ===
              "guest"
                ? "guest"
                : "agent",

            text:
              item.message_text,
          }))
        );

      } catch (error) {
        console.error(
          "Unable to load conversation:",
          error
        );

        setMessages([]);
      }
    },
    []
  );

  const refreshOperations =
    useCallback(
      async (
        bookingId: string,
        propertyId: string
      ) => {
        try {
          setIsOperationsLoading(
            true
          );

          const [
            tasksResponse,
            escalationsResponse,
          ] = await Promise.all([
            fetch(
              `${API_URL}/properties/${propertyId}/tasks`
            ),

            fetch(
              `${API_URL}/escalations`
            ),
          ]);

          if (!tasksResponse.ok) {
            throw new Error(
              `Tasks request failed: ${tasksResponse.status}`
            );
          }

          if (
            !escalationsResponse.ok
          ) {
            throw new Error(
              `Escalations request failed: ${escalationsResponse.status}`
            );
          }

          const taskData: Task[] =
            await tasksResponse.json();

          const escalationData:
            Escalation[] =
            await escalationsResponse.json();


          const bookingTasks =
            taskData.filter(
              (task) =>
                task.booking_id ===
                bookingId
            );


          const bookingEscalations =
            escalationData.filter(
              (escalation) =>
                escalation.booking_id ===
                bookingId
            );


          setTasks(
            bookingTasks
          );

          setEscalations(
            bookingEscalations
          );
        } catch (error) {
          console.error(
            "Unable to refresh operational state:",
            error
          );
        } finally {
          setIsOperationsLoading(
            false
          );
        }
      },
      []
    );


  // ---------------------------------------------------------
// INITIAL LOAD
// ---------------------------------------------------------

useEffect(() => {
  const timer = window.setTimeout(() => {
    void loadDemoStays();
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [loadDemoStays]);


// ---------------------------------------------------------
// REFRESH WHEN GUEST CHANGES
// ---------------------------------------------------------

useEffect(() => {
  if (!selectedStay) {
    return;
  }

  const timer = window.setTimeout(() => {
    void loadConversation(
      selectedStay.booking_id
    );

    void refreshOperations(
      selectedStay.booking_id,
      selectedStay.property_id
    );
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [
  selectedStay,
  loadConversation,
  refreshOperations,
]);


  // ---------------------------------------------------------
  // CHANGE GUEST
  // ---------------------------------------------------------

  function changeGuest(
    bookingId: string
  ) {
    setSelectedBookingId(
      bookingId
    );

    setMessages([]);
    setActivities([]);
    setMessage("");

    setTasks([]);
    setEscalations([]);
  }


  // ---------------------------------------------------------
  // RESET DEMO
  // ---------------------------------------------------------

  async function resetDemo() {
    if (
      !selectedStay ||
      isResetting
    ) {
      return;
    }

    setIsResetting(true);

    try {
      const response =
        await fetch(
          `${API_URL}/demo/reset/${selectedStay.booking_id}`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {
        throw new Error(
          `Demo reset failed: ${response.status}`
        );
      }

      setMessages([]);
      setMessage("");
      setActivities([]);

      await refreshOperations(
        selectedStay.booking_id,
        selectedStay.property_id
      );
    } catch (error) {
      console.error(
        "Unable to reset demo:",
        error
      );
    } finally {
      setIsResetting(false);
    }
  }


  // ---------------------------------------------------------
  // SEND MESSAGE
  // ---------------------------------------------------------

  async function sendMessage() {
    if (!selectedStay) {
      return;
    }

    const trimmedMessage =
      message.trim();

    if (
      !trimmedMessage ||
      isLoading
    ) {
      return;
    }


    setMessages(
      (current) => [
        ...current,
        {
          sender: "guest",
          text: trimmedMessage,
        },
      ]
    );


    setMessage("");
    setActivities([]);
    setIsLoading(true);


    try {
      const response =
        await fetch(
          `${API_URL}/agent/chat`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                guest_id:
                  selectedStay.guest_id,

                booking_id:
                  selectedStay.booking_id,

                message:
                  trimmedMessage,
              }),
          }
        );


      if (!response.ok) {
        throw new Error(
          `Agent request failed: ${response.status}`
        );
      }


      const data =
        await response.json();


      setMessages(
        (current) => [
          ...current,
          {
            sender: "agent",
            text:
              data.response,
          },
        ]
      );


      setActivities(
        data.activities ?? []
      );


      await refreshOperations(
        selectedStay.booking_id,
        selectedStay.property_id
      );
    } catch (error) {
      console.error(error);

      setMessages(
        (current) => [
          ...current,
          {
            sender: "agent",
            text:
              "Unable to contact StayOps right now.",
          },
        ]
      );
    } finally {
      setIsLoading(false);
    }
  }


  // ---------------------------------------------------------
  // QUICK DEMO PROMPTS
  // ---------------------------------------------------------

  function fillPrompt(
    prompt: string
  ) {
    setMessage(prompt);
  }


  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">

      {/* HEADER */}

      <header className="sticky top-0 z-20 border-b border-zinc-800/80 bg-[#09090b]/95 backdrop-blur">

        <div className="mx-auto flex max-w-[1450px] items-center justify-between px-6 py-4">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-zinc-950">
              SO
            </div>

            <div>
              <div className="flex items-center gap-2">

                <h1 className="text-lg font-semibold tracking-tight">
                  StayOps AI
                </h1>

                <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-violet-300">
                  Demo
                </span>

              </div>

              <p className="text-xs text-zinc-500">
                Autonomous Guest Operations
              </p>
            </div>

          </div>

          


          <div className="flex items-center gap-3">

            <a
              href="/operations"
              className="rounded-lg border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-xs font-semibold text-violet-300 transition hover:border-violet-400/50 hover:bg-violet-500/20 hover:text-violet-200"
            >
              Operations
            </a>

            <button
              onClick={() =>
                void resetDemo()
              }

              disabled={
                isResetting ||
                isLoading ||
                !selectedStay
              }

              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3.5 py-2 text-xs font-medium text-zinc-300 transition hover:border-zinc-600 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isResetting
                ? "Resetting..."
                : "Reset Demo"}
            </button>


            <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-400">

              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]" />

              System online

            </div>

          </div>

        </div>

      </header>


      {/* PAGE */}

      <div className="mx-auto max-w-[1450px] px-6 py-6">


        {/* TOP BAR */}

        <div className="mb-6 flex flex-col gap-4 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 lg:flex-row lg:items-center lg:justify-between">

          <div>

            <p className="text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">
              Active guest
            </p>

            <div className="mt-1 flex items-center gap-3">

              <select
                value={
                  selectedBookingId
                }

                onChange={(event) =>
                  changeGuest(
                    event.target.value
                  )
                }

                disabled={
                  isLoading ||
                  isResetting
                }

                className="min-w-[260px] rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm font-medium text-zinc-100 outline-none transition focus:border-zinc-500"
              >

                {demoStays.map(
                  (stay) => (

                    <option
                      key={
                        stay.booking_id
                      }

                      value={
                        stay.booking_id
                      }
                    >
                      {
                        stay.first_name
                      }{" "}
                      {
                        stay.last_name
                      }{" "}
                      ·{" "}
                      {languageLabel(
                        stay.guest_lang
                      )}
                    </option>

                  )
                )}

              </select>


              {selectedStay && (

                <span className="rounded-md border border-blue-500/20 bg-blue-500/10 px-2.5 py-1.5 text-xs font-medium text-blue-300">
                  {languageCode(
                    selectedStay.guest_lang
                  )}
                </span>

              )}

            </div>

          </div>


          <div className="grid grid-cols-3 gap-3">

            <div className="min-w-[110px] rounded-xl border border-zinc-800 bg-zinc-950/70 px-4 py-3">

              <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                Tasks
              </p>

              <p className="mt-1 text-xl font-semibold">
                {tasks.length}
              </p>

            </div>


            <div className="min-w-[110px] rounded-xl border border-zinc-800 bg-zinc-950/70 px-4 py-3">

              <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                Escalations
              </p>

              <p className="mt-1 text-xl font-semibold">
                {
                  escalations.length
                }
              </p>

            </div>


            <div className="min-w-[110px] rounded-xl border border-zinc-800 bg-zinc-950/70 px-4 py-3">

              <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                Agent steps
              </p>

              <p className="mt-1 text-xl font-semibold">
                {
                  activities.length
                }
              </p>

            </div>

          </div>

        </div>


        {/* DASHBOARD */}

        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.85fr]">


          {/* ================================================= */}
          {/* CHAT */}
          {/* ================================================= */}

          <section className="flex min-h-[760px] flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70 shadow-2xl shadow-black/20">


            {/* CHAT HEADER */}

            <div className="border-b border-zinc-800 px-5 py-4">

              <div className="flex items-center justify-between gap-4">

                <div className="flex items-center gap-3">

                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/15 text-sm font-semibold text-blue-300">

                    {selectedStay
                      ? `${selectedStay.first_name[0]}${selectedStay.last_name[0]}`
                      : "--"}

                  </div>


                  <div>

                    <h2 className="text-sm font-semibold">
                      {selectedStay
                        ? `${selectedStay.first_name} ${selectedStay.last_name}`
                        : "Loading guest..."}
                    </h2>

                    <p className="mt-0.5 text-xs text-zinc-500">
                      {selectedStay
                        ? selectedStay.booking_id
                        : "Loading booking..."}
                    </p>

                  </div>

                </div>


                {selectedStay && (

                  <div className="flex items-center gap-2">

                    <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs text-blue-300">
                      {languageLabel(
                        selectedStay.guest_lang
                      )}
                    </span>

                    <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs capitalize text-emerald-300">
                      {
                        selectedStay.book_status
                      }
                    </span>

                  </div>

                )}

              </div>

            </div>


            {/* CHAT BODY */}

            <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-6">

              {messages.length ===
                0 &&
                !isLoading && (

                  <div className="m-auto max-w-lg text-center">

                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-950 text-xl">
                      ✦
                    </div>

                    <h3 className="mt-4 font-medium text-zinc-200">
                      Ready for a guest issue
                    </h3>

                    <p className="mt-2 text-sm leading-relaxed text-zinc-500">
                      StayOps will retrieve the
                      guest context, search
                      operational knowledge,
                      take bounded actions and
                      escalate when needed.
                    </p>


                    <div className="mt-5 flex flex-wrap justify-center gap-2">

                      <button
                        onClick={() =>
                          fillPrompt(
                            "There is water leaking underneath the kitchen sink and it is getting worse."
                          )
                        }
                        className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-400 transition hover:border-zinc-700 hover:text-zinc-200"
                      >
                        Worsening leak
                      </button>


                      <button
                        onClick={() =>
                          fillPrompt(
                            "The heating has stopped working and the apartment is getting cold."
                          )
                        }
                        className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-400 transition hover:border-zinc-700 hover:text-zinc-200"
                      >
                        Heating failure
                      </button>


                      <button
                        onClick={() =>
                          fillPrompt(
                             "The heating has been broken all evening. I want a full refund."
                          )
                        }
                        className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-400 transition hover:border-zinc-700 hover:text-zinc-200"
                      >
                        Refund request
                      </button>

                    </div>

                  </div>

                )}


              {messages.map(
                (
                  chatMessage,
                  index
                ) => {

                  const isGuest =
                    chatMessage.sender ===
                    "guest";

                  return (

                    <div
                      key={index}
                      className={
                        isGuest
                          ? "ml-auto flex max-w-[78%] flex-col items-end gap-1.5"
                          : "mr-auto flex max-w-[82%] flex-col items-start gap-1.5"
                      }
                    >

                      <span className="px-1 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                        {isGuest
                          ? "Guest"
                          : "StayOps"}
                      </span>


                      <div
                        className={
                          isGuest
                            ? "whitespace-pre-wrap rounded-2xl rounded-br-md bg-blue-600 px-4 py-3 text-sm leading-relaxed text-white shadow-lg shadow-blue-950/20"
                            : "whitespace-pre-wrap rounded-2xl rounded-bl-md border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm leading-relaxed text-zinc-200"
                        }
                      >
                        {
                          chatMessage.text
                        }
                      </div>

                    </div>

                  );
                }
              )}


              {isLoading && (

                <div className="mr-auto flex max-w-[80%] flex-col items-start gap-1.5">

                  <span className="px-1 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                    StayOps
                  </span>

                  <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-400">

                    <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />

                    Processing guest issue...

                  </div>

                </div>

              )}

            </div>


            {/* INPUT */}

            <div className="border-t border-zinc-800 bg-zinc-900/90 p-4">

              <div className="flex gap-3">

                <input
                  type="text"

                  value={message}

                  onChange={(event) =>
                    setMessage(
                      event.target.value
                    )
                  }

                  onKeyDown={(event) => {
                    if (
                      event.key ===
                      "Enter"
                    ) {
                      void sendMessage();
                    }
                  }}

                  placeholder="Describe a guest issue..."

                  disabled={
                    isLoading ||
                    !selectedStay
                  }

                  className="flex-1 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/10 disabled:opacity-50"
                />


                <button
                  onClick={() =>
                    void sendMessage()
                  }

                  disabled={
                    isLoading ||
                    !selectedStay
                  }

                  className="min-w-[100px] rounded-xl bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading
                    ? "Working"
                    : "Send"}
                </button>

              </div>

            </div>

          </section>


          {/* ================================================= */}
          {/* OPERATIONS */}
          {/* ================================================= */}

          <aside className="space-y-5">


            {/* CURRENT STAY */}

            <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">

              <div className="mb-5 flex items-center justify-between">

                <div>

                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-600">
                    Reservation
                  </p>

                  <h2 className="mt-1 font-semibold">
                    Current Stay
                  </h2>

                </div>


                {selectedStay && (

                  <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs capitalize text-emerald-300">
                    {
                      selectedStay.book_status
                    }
                  </span>

                )}

              </div>


              {selectedStay ? (

                <div className="space-y-4 text-sm">

                  <div className="flex items-start justify-between gap-5">

                    <span className="text-zinc-500">
                      Guest
                    </span>

                    <span className="text-right font-medium">
                      {
                        selectedStay.first_name
                      }{" "}
                      {
                        selectedStay.last_name
                      }
                    </span>

                  </div>


                  <div className="flex items-start justify-between gap-5">

                    <span className="text-zinc-500">
                      Language
                    </span>

                    <span className="text-right">
                      {languageLabel(
                        selectedStay.guest_lang
                      )}
                    </span>

                  </div>


                  <div className="flex items-start justify-between gap-5">

                    <span className="text-zinc-500">
                      Property
                    </span>

                    <span className="max-w-[65%] text-right leading-relaxed">
                      {
                        selectedStay.property_title
                      }
                    </span>

                  </div>


                  <div className="border-t border-zinc-800" />


                  <div className="grid grid-cols-2 gap-3">

                    <div className="rounded-xl bg-zinc-950/70 p-3">

                      <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                        Check-in
                      </p>

                      <p className="mt-1 text-sm">
                        {formatDate(
                          selectedStay.check_in
                        )}
                      </p>

                    </div>


                    <div className="rounded-xl bg-zinc-950/70 p-3">

                      <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                        Check-out
                      </p>

                      <p className="mt-1 text-sm">
                        {formatDate(
                          selectedStay.check_out
                        )}
                      </p>

                    </div>

                  </div>

                </div>

              ) : (

                <p className="text-sm text-zinc-500">
                  Loading stay...
                </p>

              )}

            </section>


            {/* TASKS */}

            <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">

              <div className="mb-4 flex items-center justify-between">

                <div>

                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-600">
                    Operations
                  </p>

                  <h2 className="mt-1 font-semibold">
                    Open Tasks
                  </h2>

                </div>


                <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-zinc-800 px-2 text-xs font-medium text-zinc-300">
                  {tasks.length}
                </span>

              </div>


              {isOperationsLoading ? (

                <p className="text-sm text-zinc-500">
                  Loading tasks...
                </p>

              ) : tasks.length === 0 ? (

                <div className="rounded-xl border border-dashed border-zinc-800 py-5 text-center">

                  <p className="text-sm text-zinc-500">
                    No open tasks
                  </p>

                </div>

              ) : (

                <div className="space-y-3">

                  {tasks.map(
                    (task) => (

                      <div
                        key={
                          task.task_id
                        }

                        className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-4"
                      >

                        <div className="flex items-center justify-between gap-3">

                          <div className="flex items-center gap-3">

                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-xs font-semibold uppercase text-amber-300">
                              {
                                task.category.slice(
                                  0,
                                  2
                                )
                              }
                            </div>

                            <span className="text-sm font-medium capitalize">
                              {
                                task.category
                              }
                            </span>

                          </div>


                          <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-[11px] capitalize text-amber-300">
                            {
                              task.task_status
                            }
                          </span>

                        </div>


                        <p className="mt-3 text-xs leading-relaxed text-zinc-500">
                          {
                            task.title
                          }
                        </p>

                      </div>

                    )
                  )}

                </div>

              )}

            </section>


            {/* ESCALATIONS */}

            <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">

              <div className="mb-4 flex items-center justify-between">

                <div>

                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-600">
                    Handoffs
                  </p>

                  <h2 className="mt-1 font-semibold">
                    Escalations
                  </h2>

                </div>


                <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-red-500/10 px-2 text-xs font-medium text-red-300">
                  {
                    escalations.length
                  }
                </span>

              </div>


              {isOperationsLoading ? (

                <p className="text-sm text-zinc-500">
                  Loading escalations...
                </p>

              ) :
                escalations.length ===
                0 ? (

                <div className="rounded-xl border border-dashed border-zinc-800 py-5 text-center">

                  <p className="text-sm text-zinc-500">
                    No open escalations
                  </p>

                </div>

              ) : (

                <div className="space-y-3">

                  {escalations.map(
                    (
                      escalation
                    ) => (

                      <div
                        key={
                          escalation.escalation_id
                        }

                        className="rounded-xl border border-red-950 bg-red-950/10 p-4"
                      >

                        <div className="flex items-center justify-between gap-3">

                          <span className="text-sm font-medium capitalize">
                            {
                              escalation.category
                            }
                          </span>


                          <span
                            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium capitalize ${priorityClasses(
                              escalation.priority
                            )}`}
                          >
                            {
                              escalation.priority
                            }
                          </span>

                        </div>


                        <p className="mt-3 text-xs leading-relaxed text-zinc-500">
                          {
                            escalation.reason
                          }
                        </p>

                      </div>

                    )
                  )}

                </div>

              )}

            </section>


            {/* AGENT ACTIVITY */}

            <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">

              <div className="mb-4 flex items-center justify-between">

                <div>

                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-600">
                    Latest run
                  </p>

                  <h2 className="mt-1 font-semibold">
                    Agent Activity
                  </h2>

                </div>


                {isLoading && (

                  <span className="flex items-center gap-2 text-xs text-blue-300">

                    <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />

                    Running

                  </span>

                )}

              </div>


              {activities.length ===
              0 ? (

                <div className="rounded-xl border border-dashed border-zinc-800 py-5 text-center">

                  <p className="text-sm text-zinc-500">
                    No agent activity yet
                  </p>

                </div>

              ) : (

                <div>

                  {activities.map(
                    (
                      activity,
                      index
                    ) => (

                      <div
                        key={`${activity}-${index}`}
                        className="relative flex gap-3 pb-4 last:pb-0"
                      >

                        {index <
                          activities.length -
                            1 && (

                          <div className="absolute left-[7px] top-4 h-full w-px bg-zinc-800" />

                        )}


                        <div className="relative z-10 mt-1 flex h-[15px] w-[15px] shrink-0 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10">

                          <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                        </div>


                        <span className="text-sm leading-relaxed text-zinc-400">
                          {
                            activity
                          }
                        </span>

                      </div>

                    )
                  )}

                </div>

              )}

            </section>

          </aside>

        </div>

      </div>

    </main>
  );
}