import { useEffect, useRef, useState, type RefObject } from "react";
import { Link, useParams } from "react-router-dom";
import { useJobQuery, useReportQuery } from "@/api/hooks";
import { ReportSummaryChart } from "@/components/report-summary-chart";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { type AnalysisReport } from "@/api/types";
import { useAuthState } from "@/lib/auth";
import { cn, titleCase } from "@/lib/utils";

const assetBlobUrlCache = new Map<string, string>();

function formatTimestamp(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const remainder = safeSeconds % 60;
  return `${minutes}:${remainder.toString().padStart(2, "0")}`;
}

function formatPercentile(value: number) {
  return `${Math.round(value)}th percentile`;
}

function resolveBrainFrameUrl(template: string | undefined, frameIndex: number) {
  if (!template) {
    return undefined;
  }
  return template.replace("{index}", String(frameIndex));
}

function useAuthenticatedAssetUrl(sourceUrl?: string) {
  const auth = useAuthState();
  const [state, setState] = useState<{
    url?: string;
    loading: boolean;
    error?: string;
  }>({ loading: Boolean(sourceUrl) });

  useEffect(() => {
    if (!sourceUrl) {
      setState({ loading: false, url: undefined, error: undefined });
      return;
    }

    const cachedUrl = assetBlobUrlCache.get(sourceUrl);
    if (cachedUrl) {
      setState({ loading: false, url: cachedUrl, error: undefined });
      return;
    }

    const requestedUrl = sourceUrl;
    const controller = new AbortController();
    let isCancelled = false;

    async function loadAsset() {
      setState((previous) => ({ loading: true, url: previous.url, error: undefined }));
      try {
        const token = await auth.getToken();
        const response = await fetch(requestedUrl, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Asset request failed with ${response.status}.`);
        }
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        assetBlobUrlCache.set(requestedUrl, objectUrl);
        if (!isCancelled) {
          setState({ loading: false, url: objectUrl, error: undefined });
        }
      } catch (error) {
        if (controller.signal.aborted || isCancelled) {
          return;
        }
        setState({
          loading: false,
          url: undefined,
          error: error instanceof Error ? error.message : "Unable to load secure media.",
        });
      }
    }

    void loadAsset();
    return () => {
      isCancelled = true;
      controller.abort();
    };
  }, [auth, sourceUrl]);

  return state;
}

function ProtectedImage({
  sourceUrl,
  alt,
  className,
  fallback,
}: {
  sourceUrl?: string;
  alt: string;
  className?: string;
  fallback?: string;
}) {
  const asset = useAuthenticatedAssetUrl(sourceUrl);

  if (!sourceUrl) {
    return fallback ? (
      <div className={cn("flex items-center justify-center text-sm text-muted-foreground", className)}>{fallback}</div>
    ) : null;
  }

  if (asset.url) {
    return (
      <div className="relative overflow-hidden">
        <img
          alt={alt}
          className={cn(className, "transition-opacity duration-150", asset.loading ? "opacity-92" : "opacity-100")}
          src={asset.url}
        />
        {asset.loading ? (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-primary/35 to-transparent" />
        ) : null}
      </div>
    );
  }

  return (
    <div className={cn("flex items-center justify-center text-sm text-muted-foreground", className)}>
      {asset.error ?? (asset.loading ? "Loading secure media..." : fallback ?? "Media unavailable.")}
    </div>
  );
}

function ProtectedVideoPlayer({
  sourceUrl,
  videoRef,
  currentTime,
  durationLabel,
  onTimeUpdate,
}: {
  sourceUrl?: string;
  videoRef: RefObject<HTMLVideoElement | null>;
  currentTime: number;
  durationLabel: string;
  onTimeUpdate: (time: number) => void;
}) {
  const asset = useAuthenticatedAssetUrl(sourceUrl);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>Ad playback</span>
        <span>
          {formatTimestamp(currentTime)} / {durationLabel}
        </span>
      </div>
      <div className="overflow-hidden rounded-[1.5rem] border border-border/70 bg-black/90">
        {asset.url ? (
          <video
            ref={videoRef}
            className="aspect-video w-full"
            controls
            preload="metadata"
            src={asset.url}
            onTimeUpdate={(event) => onTimeUpdate(event.currentTarget.currentTime)}
          />
        ) : (
          <div className="flex aspect-video items-center justify-center text-sm text-muted-foreground">
            {asset.error ?? (asset.loading ? "Loading secure video..." : "Source video is not available for this report.")}
          </div>
        )}
      </div>
    </div>
  );
}

function ReportContent({ report }: { report: AnalysisReport }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const scoreCards = [
    { label: "Attention", value: report.summary.attention },
    { label: "Clarity", value: report.summary.clarity },
    { label: "Memorability", value: report.summary.memorability },
  ];

  const fallbackDuration =
    report.ad.duration_sec > 0 ? report.ad.duration_sec : Math.max(...report.moments.map((moment) => moment.end_sec), 1);
  const frameIndex =
    !report.playback.frame_count || !report.playback.seconds_per_frame
      ? report.technical.strongest_timestep ?? 0
      : Math.min(
          report.playback.frame_count - 1,
          Math.max(0, Math.floor(currentTime / report.playback.seconds_per_frame)),
        );
  const currentFrameUrl =
    resolveBrainFrameUrl(report.playback.brain_frame_url_template, frameIndex) ?? report.assets.brain_strongest_url;
  const currentMoment =
    report.moments.find((moment) => currentTime >= moment.start_sec && currentTime < moment.end_sec) ??
    report.moments[0];
  const chapterItems = (report.playback.chapters.length ? report.playback.chapters : report.moments).map((chapter) => ({
    key: "title" in chapter ? chapter.title : chapter.label,
    title: "title" in chapter ? chapter.title : chapter.label,
    timestampLabel: chapter.timestamp_label,
    startSec: chapter.start_sec,
  }));

  const jumpToTime = (seconds: number) => {
    const video = videoRef.current;
    if (!video) {
      setCurrentTime(seconds);
      return;
    }
    video.currentTime = seconds;
    void video.play().catch(() => {
      // Autoplay can be blocked after a seek, which is fine.
    });
    setCurrentTime(seconds);
  };

  return (
    <div className="space-y-10">
      <section className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Report view</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">{report.ad.title}</h1>
          <p className="mt-3 text-base leading-7 text-muted-foreground">
            {[report.ad.brand, report.ad.campaign, `${report.ad.duration_sec}s`].filter(Boolean).join(" / ")}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="outline" className="px-3 py-1 text-xs uppercase tracking-[0.18em]">
            {titleCase(report.confidence.label)} confidence
          </Badge>
          <Button asChild variant="outline">
            <Link to="/app/library">Open historical library</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {scoreCards.map((item) => (
          <Card key={item.label} className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardHeader className="space-y-4 px-6 py-6">
              <div className="flex items-center justify-between gap-3">
                <CardDescription>{item.label}</CardDescription>
                <Badge variant="secondary">{formatPercentile(item.value.percentile)}</Badge>
              </div>
              <CardTitle className="text-4xl">{item.value.score.toFixed(2)}</CardTitle>
              <div className="space-y-2">
                <CardDescription>{item.value.band.replaceAll("_", " ")}</CardDescription>
                <div className="text-sm text-muted-foreground">
                  {titleCase(item.value.confidence_label)} confidence, peer mean {item.value.peer_mean.toFixed(2)}
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </section>

      <section>
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 py-7">
            <CardTitle>Playback Review</CardTitle>
            <CardDescription>
              Review the ad alongside the response map and move through the key moments on the timeline.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 px-8 pb-8">
            <div className="grid gap-5 xl:grid-cols-2">
              <ProtectedVideoPlayer
                sourceUrl={report.assets.video_url}
                videoRef={videoRef}
                currentTime={currentTime}
                durationLabel={formatTimestamp(fallbackDuration)}
                onTimeUpdate={setCurrentTime}
              />

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Predicted response view</span>
                  <span>Frame {frameIndex + 1}{report.playback.frame_count ? ` / ${report.playback.frame_count}` : ""}</span>
                </div>
                <div className="overflow-hidden rounded-[1.5rem] border border-border/70 bg-[radial-gradient(circle_at_top,_rgba(240,178,122,0.12),_rgba(12,10,9,0.92))]">
                  <ProtectedImage
                    alt="Predicted brain response for the current ad moment."
                    className="aspect-video w-full object-contain"
                    sourceUrl={currentFrameUrl}
                    fallback="Brain frames are not available for this report."
                  />
                </div>
              </div>
            </div>

            <div className="rounded-[1.5rem] border border-border/70 bg-secondary/18 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Current chapter</div>
                  <div className="mt-2 text-xl font-semibold text-foreground">
                    {currentMoment?.label ?? "Playback overview"}
                  </div>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                    {currentMoment?.summary ?? "Use the chapters below to jump to the strongest and weakest moments."}
                  </p>
                </div>
                {currentMoment ? (
                  <Badge variant={currentMoment.kind === "strong" ? "success" : "warning"}>
                    {currentMoment.kind === "strong" ? "High-response segment" : "Potential drop-off"}
                  </Badge>
                ) : null}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {chapterItems.map((chapter) => (
                  <button
                    key={`${chapter.key}-${chapter.startSec}`}
                    className="rounded-full border border-border/70 bg-background px-3 py-2 text-left text-sm transition hover:border-primary/50 hover:bg-primary/5"
                    onClick={() => jumpToTime(chapter.startSec)}
                    type="button"
                  >
                    <span className="font-medium text-foreground">{chapter.timestampLabel}</span>
                    <span className="ml-2 text-muted-foreground">{chapter.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-8 xl:grid-cols-[0.96fr_1.04fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 py-7">
            <CardTitle>Quick Read</CardTitle>
            <CardDescription>Benchmark your top-line scores against the wider dataset and similar peers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 px-8 pb-8">
            <ReportSummaryChart report={report} />
            <div className="rounded-[1.35rem] border border-border/70 bg-secondary/18 p-4">
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Overall confidence</div>
              <div className="mt-2 text-2xl font-semibold">{titleCase(report.confidence.label)}</div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                This report is anchored by the nearest rated ads in the current library. Confidence rises when those
                reference ads are both close and well-covered.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>What This Means</CardTitle>
            <CardDescription>Lead with what is working, then make the next edit decisions obvious.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 px-7 pb-7">
            <div>
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Strong moments</div>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-foreground">
                {report.strengths.length ? report.strengths.map((item) => <li key={item}>{item}</li>) : <li>Signal is still exploratory for strong claims.</li>}
              </ul>
            </div>
            <Separator />
            <div>
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Potential weak moments</div>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-foreground">
                {report.risks.length ? report.risks.map((item) => <li key={item}>{item}</li>) : <li>No standout risk rose above the current threshold.</li>}
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Creative Profile</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">{report.creative_profile.label}</h2>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">{report.creative_profile.summary}</p>
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-4">
          {Object.entries(report.tracks).map(([trackId, track]) => (
            <Card key={trackId} className="rounded-[1.6rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
              <CardHeader className="space-y-3 px-6 py-6">
                <div className="flex items-center justify-between gap-3">
                  <CardDescription>{track.label}</CardDescription>
                  <Badge variant="secondary">{formatPercentile(track.percentile)}</Badge>
                </div>
                <CardTitle className="text-3xl">{track.score.toFixed(0)}</CardTitle>
                <CardDescription>{track.band.replaceAll("_", " ")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 px-6 pb-6">
                <p className="text-sm leading-6 text-muted-foreground">{track.short_description}</p>
                <div className="space-y-2">
                  {track.why_it_matters.map((reason) => (
                    <div key={reason} className="rounded-full border border-border/70 bg-secondary/22 px-3 py-1.5 text-xs text-muted-foreground">
                      {reason}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 py-7">
            <CardTitle>Similar Ads You Should Compare Against</CardTitle>
            <CardDescription>Helpful references from the historical library, not just a raw nearest-neighbor dump.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 px-8 pb-8">
            {report.similar_ads.map((ad) => (
              <div key={ad.ad_id} className="rounded-[1.35rem] border border-border/70 bg-secondary/28 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="font-medium text-foreground">{ad.brand}</div>
                  <Badge variant="outline">Distance {ad.distance.toFixed(2)}</Badge>
                </div>
                <div className="mt-2 text-sm leading-6 text-muted-foreground">{ad.why_similar}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-8 xl:grid-cols-[1.02fr_0.98fr]">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Moment Timeline</CardTitle>
            <CardDescription>Use the timestamps like creative review chapters, not just generic peaks.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 px-7 pb-7">
            {report.moments.map((moment) => (
              <button
                key={moment.id}
                className={cn(
                  "w-full rounded-[1.25rem] border border-border/70 bg-background/80 p-4 text-left transition hover:border-primary/45 hover:bg-primary/5",
                  currentMoment?.id === moment.id && "border-primary/60 bg-primary/6",
                )}
                onClick={() => jumpToTime(moment.start_sec)}
                type="button"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="font-medium text-foreground">{moment.label}</div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      {moment.timestamp_label} to {formatTimestamp(moment.end_sec)}
                    </div>
                  </div>
                  <Badge variant={moment.kind === "strong" ? "success" : "warning"}>
                    {moment.kind === "strong" ? "Strong moment" : "Watch closely"}
                  </Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{moment.summary}</p>
                {moment.events?.length ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {moment.events.map((event) => (
                      <div
                        key={`${moment.id}-${event.type}-${event.start_sec}`}
                        className="rounded-full border border-border/70 bg-secondary/20 px-3 py-1.5 text-xs text-muted-foreground"
                      >
                        {event.label}
                      </div>
                    ))}
                  </div>
                ) : null}
                <div className="mt-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  {moment.impact.join(" / ")}
                </div>
              </button>
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
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium capitalize text-foreground">{label}</div>
                  <Badge variant="secondary">{formatPercentile(report.summary[label as keyof typeof report.summary].percentile)}</Badge>
                </div>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                  {reasons.length ? reasons.map((reason) => <li key={reason}>{reason}</li>) : <li>Not enough stable signal yet.</li>}
                </ul>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section>
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Event Alignment</CardTitle>
            <CardDescription>
              Connect the strongest and weakest response windows to pacing, spoken density, brand cues, and CTA timing.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 px-7 pb-7 md:grid-cols-2">
            {report.event_alignment.length ? (
              report.event_alignment.map((event) => (
                <button
                  key={`${event.type}-${event.start_sec}`}
                  className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-left transition hover:border-primary/45 hover:bg-primary/5"
                  onClick={() => jumpToTime(event.start_sec)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="font-medium text-foreground">{event.label}</div>
                    <Badge variant="outline">{formatTimestamp(event.start_sec)}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{event.detail}</p>
                  {event.text ? <div className="mt-3 text-sm text-foreground">"{event.text}"</div> : null}
                  <div className="mt-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">{event.source}</div>
                </button>
              ))
            ) : (
              <div className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-sm text-muted-foreground">
                We do not yet have enough timed transcript or pacing cues to align this report to specific ad events.
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-8">
        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-7 py-6">
            <CardTitle>Visual Evidence</CardTitle>
            <CardDescription>Keep the technical evidence close enough to trust without leading with it.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 px-7 pb-7">
            <div className="grid gap-5 xl:grid-cols-2">
              <div className="space-y-3">
                <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Activation Curve</div>
                <ProtectedImage
                  alt="Activation curve across the ad."
                  className="min-h-72 w-full rounded-[1.25rem] border border-border/70 bg-background/80 object-contain"
                  sourceUrl={report.assets.activation_curve_url}
                />
              </div>
              <div className="space-y-3">
                <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Top ROI Timecourses</div>
                <ProtectedImage
                  alt="Top ROI response curves over time."
                  className="min-h-72 w-full rounded-[1.25rem] border border-border/70 bg-background/80 object-contain"
                  sourceUrl={report.assets.top_roi_timecourses_url}
                />
              </div>
            </div>
            <div className="space-y-3">
              <div className="text-sm uppercase tracking-[0.18em] text-muted-foreground">Whole-Ad Brain Animation</div>
              <ProtectedImage
                alt="Animated predicted brain response over the whole ad."
                className="min-h-80 w-full rounded-[1.25rem] border border-border/70 bg-background/80 object-contain"
                sourceUrl={report.assets.brain_animation_url}
              />
            </div>
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
                <div className="grid gap-4 pt-2 md:grid-cols-2">
                  <div className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-sm leading-6 text-muted-foreground">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Top ROIs</div>
                    <div className="mt-2 text-foreground">{report.technical.top_rois.join(", ") || "Not available"}</div>
                  </div>
                  <div className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-sm leading-6 text-muted-foreground">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Strongest timestep</div>
                    <div className="mt-2 text-foreground">{report.technical.strongest_timestep}</div>
                  </div>
                  <div className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-sm leading-6 text-muted-foreground">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Frame count</div>
                    <div className="mt-2 text-foreground">{report.playback.frame_count}</div>
                  </div>
                  <div className="rounded-[1.25rem] border border-border/70 bg-secondary/18 p-4 text-sm leading-6 text-muted-foreground">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Seconds per frame</div>
                    <div className="mt-2 text-foreground">{report.playback.seconds_per_frame.toFixed(2)}</div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}

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

  return <ReportContent report={reportQuery.data} />;
}
