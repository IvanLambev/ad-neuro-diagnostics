import { AlertTriangle, RotateCcw } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useJobEventsQuery, useJobQuery, useRetryJobMutation } from "@/api/hooks";
import { JobStatusBadge } from "@/components/job-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatDateTime, titleCase } from "@/lib/utils";

export function JobProgressPage() {
  const { jobId = "" } = useParams();
  const jobQuery = useJobQuery(jobId);
  const eventsQuery = useJobEventsQuery(jobId);
  const retryMutation = useRetryJobMutation(jobId);

  if (!jobQuery.data) {
    return <div className="py-14 text-center text-muted-foreground">Loading job progress...</div>;
  }

  const job = jobQuery.data;

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_0.95fr]">
      <section className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Job progress</div>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight">{job.title}</h1>
            <p className="mt-3 text-base leading-7 text-muted-foreground">{[job.brand, job.campaign].filter(Boolean).join(" / ")}</p>
          </div>
          <JobStatusBadge status={job.status} />
        </div>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="flex flex-row items-end justify-between gap-3 px-8 py-7">
            <div className="space-y-2">
              <CardDescription>Current stage</CardDescription>
              <CardTitle className="text-3xl">{titleCase(job.current_step)}</CardTitle>
            </div>
            <div className="text-sm text-muted-foreground">{job.progress}% complete</div>
          </CardHeader>
          <CardContent className="space-y-5 px-8 pb-8">
            <Progress value={job.progress} />
            <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
              <span>Created {formatDateTime(job.created_at)}</span>
              {job.started_at ? <span>Started {formatDateTime(job.started_at)}</span> : null}
            </div>
          </CardContent>
        </Card>

        {job.status === "failed" ? (
          <Card className="rounded-[1.75rem] border-destructive/30 bg-card/96 shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
            <CardHeader className="px-7 py-6">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-1 h-5 w-5 text-destructive" />
                <div className="space-y-2">
                  <CardTitle>Analysis failed</CardTitle>
                  <CardDescription>{job.error_message ?? "The backend reported a failure."}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="px-7 pb-7">
              <Button variant="destructive" onClick={() => retryMutation.mutate()} disabled={retryMutation.isPending}>
                <RotateCcw className="h-4 w-4" />
                {retryMutation.isPending ? "Retrying..." : "Retry analysis"}
              </Button>
            </CardContent>
          </Card>
        ) : null}

        {job.status === "completed" ? (
          <Button asChild size="lg">
            <Link to={`/app/jobs/${job.id}/report`}>Open report</Link>
          </Button>
        ) : null}
      </section>

      <section>
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Stage timeline</CardTitle>
            <CardDescription>Polling stops automatically when the job reaches completed or failed.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 px-7 pb-7">
            {(eventsQuery.data ?? []).map((event) => (
              <div key={`${event.step}-${event.at}`} className="flex gap-4 rounded-[1.35rem] border border-border/70 bg-secondary/28 px-4 py-4">
                <div
                  className={
                    event.status === "done"
                      ? "mt-1 h-3 w-3 rounded-full bg-primary"
                      : event.status === "current"
                        ? "mt-1 h-3 w-3 rounded-full bg-accent"
                        : event.status === "failed"
                          ? "mt-1 h-3 w-3 rounded-full bg-destructive"
                          : "mt-1 h-3 w-3 rounded-full bg-border"
                  }
                />
                <div className="space-y-1">
                  <div className="font-medium text-foreground">{titleCase(event.step)}</div>
                  <div className="text-sm leading-6 text-muted-foreground">{event.label}</div>
                  <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{formatDateTime(event.at)}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
