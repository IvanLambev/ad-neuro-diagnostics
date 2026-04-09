import { ArrowRight, BarChart3, CircleAlert, Clock3, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import { useJobsQuery } from "@/api/hooks";
import { JobStatusBadge } from "@/components/job-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";

export function DashboardPage() {
  const jobsQuery = useJobsQuery();
  const jobs = jobsQuery.data ?? [];

  const stats = {
    active: jobs.filter((job) => !["completed", "failed"].includes(job.status)).length,
    completed: jobs.filter((job) => job.status === "completed").length,
    failed: jobs.filter((job) => job.status === "failed").length,
  };

  return (
    <div className="space-y-10">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Dashboard</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-foreground">Track what is in flight and what is ready to read.</h1>
          <p className="mt-3 text-base leading-7 text-muted-foreground">
            Keep recent jobs, failed retries, and completed reports in one place so the workflow feels operational instead of experimental.
          </p>
        </div>
        <Button asChild size="lg">
          <Link to="/app/new">
            Start a new analysis
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          { icon: Clock3, label: "Active jobs", value: stats.active },
          { icon: FileText, label: "Completed reports", value: stats.completed },
          { icon: CircleAlert, label: "Failed jobs", value: stats.failed },
        ].map((item) => (
          <Card key={item.label} className="rounded-[1.75rem] border-border/70 bg-card/95 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardHeader className="px-6 py-6">
              <item.icon className="mb-4 h-5 w-5 text-primary" />
              <CardDescription>{item.label}</CardDescription>
              <CardTitle className="text-4xl">{item.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </section>

      <Card className="overflow-hidden rounded-[2rem] border-border/70 bg-card/95 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
        <CardHeader className="flex flex-row items-start justify-between gap-4 px-7 py-6">
          <div className="space-y-2">
            <CardTitle>Recent jobs</CardTitle>
            <CardDescription>Includes current statuses, completed reports, and failures that need a retry.</CardDescription>
          </div>
          <Button asChild variant="outline">
            <Link to="/app/library">
              Explore library
              <BarChart3 className="h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <div className="border-t border-border/70">
          {jobs.length === 0 ? (
            <div className="px-7 py-14 text-center text-muted-foreground">No jobs yet. Start with a new analysis to create the first one.</div>
          ) : (
            jobs.map((job) => (
              <Link
                key={job.id}
                to={job.status === "completed" ? `/app/jobs/${job.id}/report` : `/app/jobs/${job.id}`}
                className="grid gap-4 border-b border-border/70 px-7 py-5 transition hover:bg-secondary/35 md:grid-cols-[1.3fr_0.85fr_0.6fr_0.7fr]"
              >
                <div>
                  <div className="font-medium text-foreground">{job.title}</div>
                  <div className="mt-1 text-sm text-muted-foreground">{[job.brand, job.campaign].filter(Boolean).join(" / ")}</div>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Created {formatDateTime(job.created_at)}</div>
                  <div className="mt-1">{job.status === "completed" ? "Report ready" : `${job.progress}% complete`}</div>
                </div>
                <div className="flex items-center">
                  <JobStatusBadge status={job.status} />
                </div>
                <div className="text-sm font-medium text-primary">{job.status === "completed" ? "Open report" : "View progress"}</div>
              </Link>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
