import { Link, useParams } from "react-router-dom";
import { useJobQuery, useReportQuery } from "@/api/hooks";
import { ReportSummaryChart } from "@/components/report-summary-chart";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export function ReportPage() {
  const { jobId = "" } = useParams();
  const jobQuery = useJobQuery(jobId);
  const reportQuery = useReportQuery(jobId, jobQuery.data?.status === "completed");

  if (!jobQuery.data) {
    return <div className="py-14 text-center text-muted-foreground">Loading report...</div>;
  }

  if (jobQuery.data.status !== "completed") {
    return (
      <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_16px_50px_rgba(15,23,42,0.06)]">
        <CardHeader className="px-7 py-7">
          <CardTitle>Report not ready yet</CardTitle>
          <CardDescription>This job is still running. Keep watching progress until the report is completed.</CardDescription>
        </CardHeader>
        <CardContent className="px-7 pb-7">
          <Button className="w-fit" asChild>
            <Link to={`/app/jobs/${jobId}`}>Back to progress</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!reportQuery.data) {
    return <div className="py-14 text-center text-muted-foreground">Loading structured report...</div>;
  }

  const report = reportQuery.data;
  const scoreCards = [
    { label: "Attention", value: report.summary.attention },
    { label: "Clarity", value: report.summary.clarity },
    { label: "Memorability", value: report.summary.memorability },
  ];

  return (
    <div className="space-y-10">
      <section className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Report view</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">{report.ad.title}</h1>
          <p className="mt-3 text-base leading-7 text-muted-foreground">{[report.ad.brand, report.ad.campaign, `${report.ad.duration_sec}s`].join(" / ")}</p>
        </div>
        <Button asChild variant="outline">
          <Link to="/app/library">Open historical library</Link>
        </Button>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {scoreCards.map((item) => (
          <Card key={item.label} className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardHeader className="px-6 py-6">
              <CardDescription>{item.label}</CardDescription>
              <CardTitle className="text-4xl">{item.value.score.toFixed(2)}</CardTitle>
              <CardDescription>{item.value.band.replaceAll("_", " ")}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </section>

      <section className="grid gap-8 xl:grid-cols-[1fr_0.92fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 py-7">
            <CardTitle>Quick Read</CardTitle>
            <CardDescription>Benchmark your top-line scores against the wider dataset and similar peers.</CardDescription>
          </CardHeader>
          <CardContent className="px-8 pb-8">
            <ReportSummaryChart report={report} />
          </CardContent>
        </Card>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 py-7">
            <CardTitle>What This Means</CardTitle>
            <CardDescription>Lead with what is working, then make the next edit decisions obvious.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 px-8 pb-8">
            <div>
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Strong moments</div>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-foreground">
                {report.strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <Separator />
            <div>
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Potential weak moments</div>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-foreground">
                {report.risks.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-8 lg:grid-cols-[0.98fr_1.02fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Similar Ads You Should Compare Against</CardTitle>
            <CardDescription>Helpful references from the historical library, not just a raw nearest-neighbor dump.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 px-7 pb-7">
            {report.similar_ads.map((ad) => (
              <div key={ad.ad_id} className="rounded-[1.35rem] border border-border/70 bg-secondary/28 p-5">
                <div className="font-medium text-foreground">{ad.brand}</div>
                <div className="mt-1 text-sm text-muted-foreground">{ad.why_similar}</div>
                <div className="mt-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">Distance {ad.distance.toFixed(2)}</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Historical Benchmark</CardTitle>
            <CardDescription>Use the benchmark as context, not a verdict.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 px-7 pb-7 md:grid-cols-3">
            {[
              ["Attention", report.summary.attention.dataset_mean, report.summary.attention.peer_mean],
              ["Clarity", report.summary.clarity.dataset_mean, report.summary.clarity.peer_mean],
              ["Memorability", report.summary.memorability.dataset_mean, report.summary.memorability.peer_mean],
            ].map(([label, datasetMean, peerMean]) => (
              <div key={label} className="rounded-[1.25rem] border border-border/70 bg-secondary/22 p-4">
                <div className="font-medium text-foreground">{label}</div>
                <div className="mt-3 text-sm text-muted-foreground">Dataset mean: {Number(datasetMean).toFixed(2)}</div>
                <div className="mt-1 text-sm text-muted-foreground">Peer mean: {Number(peerMean).toFixed(2)}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-8 lg:grid-cols-[0.96fr_1.04fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Strong moments</CardTitle>
            <CardDescription>Moment-level readout phrased for creative review.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 px-7 pb-7">
            {report.moments.map((moment) => (
              <div key={`${moment.label}-${moment.start_sec}`} className="rounded-[1.25rem] border border-border/70 bg-background/80 p-4">
                <div className="font-medium text-foreground">{moment.label}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {moment.start_sec}s to {moment.end_sec}s
                </div>
                <div className="mt-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">{moment.impact.join(" / ")}</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Why The System Thinks That</CardTitle>
            <CardDescription>Translate the structured signals into plain rationale.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 px-7 pb-7">
            {Object.entries(report.why).map(([label, reasons]) => (
              <div key={label} className="rounded-[1.25rem] border border-border/70 bg-secondary/22 p-4">
                <div className="font-medium capitalize text-foreground">{label}</div>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                  {reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
        <CardHeader className="px-7 py-6">
          <CardTitle>Technical Appendix</CardTitle>
          <CardDescription>Keep the raw analysis visible but safely tucked behind an expandable section.</CardDescription>
        </CardHeader>
        <CardContent className="px-7 pb-7">
          <Accordion type="single" collapsible>
            <AccordionItem value="technical">
              <AccordionTrigger>Open the technical appendix</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2">
                  <div>Top ROIs: {report.technical.top_rois.join(", ")}</div>
                  <div>Strongest timestep: {report.technical.strongest_timestep}</div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}
