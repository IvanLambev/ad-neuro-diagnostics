import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useJobsQuery } from "@/api/hooks";
import { JobStatusBadge } from "@/components/job-status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatDateTime } from "@/lib/utils";

export function LibraryPage() {
  const jobsQuery = useJobsQuery();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [brand, setBrand] = useState("all");
  const [campaign, setCampaign] = useState("all");
  const [dateRange, setDateRange] = useState("all");

  const jobs = jobsQuery.data ?? [];
  const brands = [...new Set(jobs.map((job) => job.brand).filter(Boolean))].sort();
  const campaigns = [...new Set(jobs.map((job) => job.campaign).filter(Boolean))].sort();

  const filtered = useMemo(() => {
    return jobs.filter((job) => {
      const matchesSearch = `${job.title} ${job.brand} ${job.campaign}`
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchesStatus = status === "all" ? true : job.status === status;
      const matchesBrand = brand === "all" ? true : job.brand === brand;
      const matchesCampaign = campaign === "all" ? true : job.campaign === campaign;

      const createdAt = new Date(job.created_at).getTime();
      const now = Date.now();
      const days = dateRange === "7d" ? 7 : dateRange === "30d" ? 30 : dateRange === "90d" ? 90 : null;
      const matchesDate = days === null ? true : createdAt >= now - days * 24 * 60 * 60 * 1000;

      return matchesSearch && matchesStatus && matchesBrand && matchesCampaign && matchesDate;
    });
  }, [jobs, search, status, brand, campaign, dateRange]);

  return (
    <div className="space-y-10">
      <section className="max-w-3xl">
        <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Historical library</div>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Browse prior analyzed ads and reopen any report.</h1>
        <p className="mt-3 text-base leading-7 text-muted-foreground">
          Use brand, campaign, date, and status filters to move through the archive quickly instead of relying on a single catch-all search field.
        </p>
      </section>

      <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
        <CardHeader className="px-7 py-6">
          <CardTitle>Filter the library</CardTitle>
          <CardDescription>Narrow the list by title, brand, campaign, date, or status.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 px-7 pb-7 md:grid-cols-2 xl:grid-cols-[minmax(0,1.2fr)_220px_220px_220px_180px]">
          <div className="space-y-2">
            <Label htmlFor="search">Search by title, brand, or campaign</Label>
            <Input id="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search the library" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="brand">Brand</Label>
            <select
              id="brand"
              value={brand}
              onChange={(event) => setBrand(event.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <option value="all">All brands</option>
              {brands.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="campaign">Campaign</Label>
            <select
              id="campaign"
              value={campaign}
              onChange={(event) => setCampaign(event.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <option value="all">All campaigns</option>
              {campaigns.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <option value="all">All statuses</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="queued">Queued</option>
              <option value="running_tribe">Running</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="date-range">Date</Label>
            <select
              id="date-range"
              value={dateRange}
              onChange={(event) => setDateRange(event.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <option value="all">All time</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {filtered.length === 0 ? (
          <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardContent className="px-7 py-10 text-center text-sm text-muted-foreground">
              No ads match the current brand, campaign, date, and status filters.
            </CardContent>
          </Card>
        ) : null}

        {filtered.map((job) => (
          <Card key={job.id} className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardContent className="flex flex-wrap items-start justify-between gap-4 px-7 py-6">
              <div>
                <CardTitle>{job.title}</CardTitle>
                <CardDescription className="mt-2">{[job.brand, job.campaign].filter(Boolean).join(" / ")}</CardDescription>
                <div className="mt-3 text-sm text-muted-foreground">Created {formatDateTime(job.created_at)}</div>
              </div>
              <div className="flex flex-col items-end gap-3">
                <JobStatusBadge status={job.status} />
                <Link className="text-sm font-medium text-primary" to={job.status === "completed" ? `/app/jobs/${job.id}/report` : `/app/jobs/${job.id}`}>
                  {job.status === "completed" ? "Open report" : "View progress"}
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
