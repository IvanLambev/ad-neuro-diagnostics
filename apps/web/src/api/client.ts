import { isDemoMode } from "@/lib/config";
import { mockApi } from "@/api/mock";
import type { AnalysisReport, CreateJobInput, CreateJobResponse, Job, JobEvent } from "@/api/types";

export type ApiClientOptions = {
  apiBaseUrl: string;
  getToken: () => Promise<string | null>;
};

export function createApiClient(options: ApiClientOptions) {
  if (isDemoMode) {
    return mockApi;
  }

  function absolutizeUrl(value?: string) {
    if (!value) {
      return value;
    }
    if (/^https?:\/\//.test(value)) {
      return value;
    }
    return `${options.apiBaseUrl}${value}`;
  }

  function normalizeReport(report: AnalysisReport): AnalysisReport {
    const normalizeScore = (score: AnalysisReport["summary"]["attention"]) => ({
      ...score,
      percentile: score.percentile ?? 50,
      confidence_label: score.confidence_label ?? "exploratory",
      confidence_score: score.confidence_score ?? 0.35,
    });
    const normalizedMoments = (report.moments ?? []).map((moment, index) => ({
      id: moment.id ?? `${moment.label}-${index}`,
      start_sec: moment.start_sec,
      end_sec: moment.end_sec,
      label: moment.label,
      summary: moment.summary ?? "This timestamp stands out relative to the rest of the ad.",
      impact: moment.impact ?? [],
      frame_index: moment.frame_index ?? Math.floor(moment.start_sec),
      timestamp_label: moment.timestamp_label ?? `${Math.floor(moment.start_sec / 60)}:${Math.floor(moment.start_sec % 60)
        .toString()
        .padStart(2, "0")}`,
      kind: moment.kind ?? (index === 0 ? "strong" : "weak"),
      events: moment.events ?? [],
    }));
    const normalizedEvents = (report.event_alignment ?? []).map((event) => ({
      ...event,
      start_sec: event.start_sec ?? 0,
      end_sec: event.end_sec ?? event.start_sec ?? 0,
      detail: event.detail ?? "",
      source: event.source ?? "report heuristic",
    }));
    const normalizedTracks = Object.fromEntries(
      Object.entries(report.tracks ?? {}).map(([trackId, track]) => [
        trackId,
        {
          ...track,
          score: track.score ?? 50,
          percentile: track.percentile ?? 50,
          band: track.band ?? "average",
          short_description: track.short_description ?? track.label,
          long_description: track.long_description ?? track.short_description ?? track.label,
          why_it_matters: track.why_it_matters ?? [],
        },
      ]),
    );

    return {
      ...report,
      assets: {
        ...report.assets,
        video_url: absolutizeUrl(report.assets.video_url),
        activation_curve_url: absolutizeUrl(report.assets.activation_curve_url),
        activation_curve_csv_url: absolutizeUrl(report.assets.activation_curve_csv_url),
        brain_strongest_url: absolutizeUrl(report.assets.brain_strongest_url),
        brain_animation_url: absolutizeUrl(report.assets.brain_animation_url),
        top_roi_timecourses_url: absolutizeUrl(report.assets.top_roi_timecourses_url),
      },
      summary: {
        attention: normalizeScore(report.summary.attention),
        clarity: normalizeScore(report.summary.clarity),
        memorability: normalizeScore(report.summary.memorability),
      },
      confidence: report.confidence ?? { score: 0.35, label: "exploratory" },
      creative_profile: report.creative_profile ?? {
        label: "Exploratory profile",
        summary: "The report does not yet have enough structured signals to assign a stronger creative profile.",
      },
      peer_takeaways: report.peer_takeaways ?? [],
      tracks: normalizedTracks,
      event_alignment: normalizedEvents,
      moments: normalizedMoments,
      playback: {
        frame_count: report.playback?.frame_count ?? 0,
        seconds_per_frame: report.playback?.seconds_per_frame ?? 0,
        brain_frame_url_template: absolutizeUrl(report.playback?.brain_frame_url_template),
        chapters:
          report.playback?.chapters ??
          normalizedMoments.map((moment) => ({
            title: moment.label,
            timestamp_label: moment.timestamp_label,
            start_sec: moment.start_sec,
            frame_index: moment.frame_index,
          })),
      },
    };
  }

  type BackendJob = {
    id: string;
    title: string;
    brand: string;
    campaign: string;
    notes?: string | null;
    ad_id?: string | null;
    status: Job["status"];
    progress: number;
    current_step: Job["current_step"];
    error_message?: string | null;
    created_at: string;
    updated_at: string;
    started_at?: string | null;
    completed_at?: string | null;
  };

  async function request<T>(pathname: string, init?: RequestInit) {
    const token = await options.getToken();
    let response: Response;
    try {
      response = await fetch(`${options.apiBaseUrl}${pathname}`, {
        ...init,
        headers: {
          ...(init?.headers ?? {}),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
    } catch (error) {
      throw new Error(
        "The app could not reach the analysis API. If this is a preview deployment, the backend may not allow this domain yet.",
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      try {
        const parsed = JSON.parse(errorText) as { detail?: string };
        throw new Error(parsed.detail || "Request failed.");
      } catch {
        throw new Error(errorText || "Request failed.");
      }
    }

    return (await response.json()) as T;
  }

  function toJob(payload: BackendJob): Job {
    return {
      id: payload.id,
      title: payload.title,
      brand: payload.brand,
      campaign: payload.campaign,
      notes: payload.notes,
      ad_id: payload.ad_id,
      status: payload.status,
      progress: payload.progress,
      current_step: payload.current_step,
      error_message: payload.error_message,
      created_at: payload.created_at,
      updated_at: payload.updated_at,
      started_at: payload.started_at,
      completed_at: payload.completed_at,
    };
  }

  function buildTimeline(job: Job): JobEvent[] {
    const stages: Array<{ step: JobEvent["step"]; label: string }> = [
      { step: "queued", label: "Queued for the next available processing slot" },
      { step: "validating", label: "Checking the file, duration, and metadata" },
      { step: "normalizing", label: "Preparing the clip for analysis" },
      { step: "running_tribe", label: "Running the core TRIBE signal pass" },
      { step: "extracting_features", label: "Extracting temporal features" },
      { step: "benchmarking", label: "Comparing against similar historical ads" },
      { step: "generating_report", label: "Writing the customer-facing report" },
    ];
    const currentIndex = stages.findIndex((stage) => stage.step === job.current_step);
    const eventTime = job.updated_at ?? job.created_at;

    const events = stages.map<JobEvent>((stage, index) => {
      let status: JobEvent["status"] = "pending";
      if (job.status === "failed" && stage.step === job.current_step) {
        status = "failed";
      } else if (job.status === "completed" || (currentIndex >= 0 && index < currentIndex)) {
        status = "done";
      } else if (stage.step === job.current_step) {
        status = "current";
      }

      return {
        step: stage.step,
        at: eventTime,
        label: stage.label,
        status,
      };
    });

    if (job.status === "completed") {
      events.push({
        step: "completed",
        at: job.completed_at ?? eventTime,
        label: "Report ready to review",
        status: "done",
      });
    }

    return events;
  }

  return {
    async getJobs() {
      const payload = await request<BackendJob[]>("/v1/jobs");
      return payload.map(toJob);
    },
    async getJob(jobId: string) {
      const payload = await request<BackendJob>(`/v1/jobs/${jobId}`);
      return toJob(payload);
    },
    async getJobEvents(jobId: string) {
      const payload = await request<BackendJob>(`/v1/jobs/${jobId}`);
      return buildTimeline(toJob(payload));
    },
    async getReport(jobId: string) {
      const report = await request<AnalysisReport>(`/v1/jobs/${jobId}/report`);
      return normalizeReport(report);
    },
    async createJob(input: CreateJobInput): Promise<CreateJobResponse> {
      const formData = new FormData();
      formData.append("file", input.file);
      formData.append("title", input.title);
      formData.append("brand", input.brand);
      formData.append("campaign", input.campaign);
      if (input.notes) {
        formData.append("notes", input.notes);
      }
      return request<CreateJobResponse>("/v1/jobs", {
        method: "POST",
        body: formData,
      });
    },
    async retryJob(jobId: string) {
      await request<CreateJobResponse>(`/v1/jobs/${jobId}/retry`, { method: "POST" });
      const payload = await request<BackendJob>(`/v1/jobs/${jobId}`);
      return toJob(payload);
    },
  };
}
