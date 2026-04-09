import { Badge } from "@/components/ui/badge";
import type { JobStatus } from "@/api/types";
import { titleCase } from "@/lib/utils";

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const variant =
    status === "completed"
      ? "success"
      : status === "failed"
        ? "destructive"
        : status === "benchmarking" || status === "running_tribe"
          ? "accent"
          : "warning";

  return <Badge variant={variant}>{titleCase(status)}</Badge>;
}
