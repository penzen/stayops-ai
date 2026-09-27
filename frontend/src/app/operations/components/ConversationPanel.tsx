import type {
  ConversationMessage,
} from "../types";


type ConversationPanelProps = {
  conversation: ConversationMessage[];
  isLoading: boolean;
};


export default function ConversationPanel({
  conversation,
  isLoading,
}: ConversationPanelProps) {
  return (
    <div className="border-t border-zinc-800 p-6">

      <div className="flex items-center justify-between">

        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-600">
            Booking conversation
          </p>

          <h3 className="mt-1 font-medium">
            Guest Conversation
          </h3>
        </div>

        <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
          {conversation.length} messages
        </span>

      </div>


      <div className="mt-5 space-y-4">

        {isLoading ? (

          <p className="text-sm text-zinc-500">
            Loading conversation...
          </p>

        ) : conversation.length === 0 ? (

          <div className="rounded-xl border border-dashed border-zinc-800 py-6 text-center">

            <p className="text-sm text-zinc-500">
              No conversation recorded.
            </p>

          </div>

        ) : (

          conversation.map(
            (item) => {

              const isGuest =
                item.sender_type ===
                "guest";

              return (
                <div
                  key={item.message_id}
                  className={
                    isGuest
                      ? "flex flex-col items-start"
                      : "flex flex-col items-end"
                  }
                >

                  <span className="mb-1 px-1 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                    {isGuest
                      ? "Guest"
                      : "StayOps"}
                  </span>

                  <div
                    className={
                      isGuest
                        ? "max-w-[85%] rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-3 text-sm leading-relaxed text-zinc-200"
                        : "max-w-[85%] rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm leading-relaxed text-zinc-300"
                    }
                  >
                    {item.message_text}
                  </div>

                </div>
              );
            }
          )

        )}

      </div>

    </div>
  );
}