import type {
  Operator,
} from "./types";


export function priorityClasses(
  priority: string | null
) {
  const normalized =
    priority?.toLowerCase();

  if (
    normalized === "critical" ||
    normalized === "high"
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (normalized === "medium") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  return "border-zinc-700 bg-zinc-800 text-zinc-300";
}


export function operatorName(
  operator: Operator | null
) {
  if (!operator) {
    return "Unclaimed";
  }

  const name = [
    operator.first_name,
    operator.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return name || operator.team_id;
}


export function formatEventTime(
  dateString: string
) {
  const date = new Date(
    dateString.replace(" ", "T") + "Z"
  );

  return date.toLocaleString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}