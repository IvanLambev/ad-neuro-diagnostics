export const jobStatuses = [
  "queued",
  "validating",
  "normalizing",
  "running_tribe",
  "extracting_features",
  "benchmarking",
  "generating_report",
  "completed",
  "failed",
] as const;

export type JobStatus = (typeof jobStatuses)[number];

export type ScoreSummary = {
  band: string;
  score: number;
  dataset_mean: number;
  peer_mean: number;
  percentile: number;
  confidence_label: string;
  confidence_score: number;
};

export type ReportMoment = {
  id: string;
  start_sec: number;
  end_sec: number;
  label: string;
  summary: string;
  impact: string[];
  frame_index: number;
  timestamp_label: string;
  kind: "strong" | "weak";
};

export type AnalysisReport = {
  job_id: string;
  status: "completed";
  ad: {
    ad_id: string;
    title: string;
    brand: string;
    campaign?: string;
    duration_sec: number;
  };
  summary: {
    attention: ScoreSummary;
    clarity: ScoreSummary;
    memorability: ScoreSummary;
  };
  confidence: {
    score: number;
    label: string;
  };
  strengths: string[];
  risks: string[];
  similar_ads: Array<{
    ad_id: string;
    brand: string;
    distance: number;
    why_similar: string;
  }>;
  moments: ReportMoment[];
  why: Record<string, string[]>;
  assets: {
    video_url?: string;
    activation_curve_url?: string;
    activation_curve_csv_url?: string;
    brain_strongest_url?: string;
    brain_animation_url?: string;
    top_roi_timecourses_url?: string;
  };
  playback: {
    frame_count: number;
    seconds_per_frame: number;
    brain_frame_url_template?: string;
    chapters: Array<{
      title: string;
      timestamp_label: string;
      start_sec: number;
      frame_index: number;
    }>;
  };
  technical: {
    top_rois: string[];
    strongest_timestep: number;
    summary?: Record<string, unknown>;
  };
};

export type Job = {
  id: string;
  status: JobStatus;
  progress: number;
  current_step: JobStatus;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  title: string;
  brand: string;
  campaign: string;
  notes?: string | null;
  ad_id?: string | null;
  error_message?: string | null;
};

export type JobEvent = {
  step: JobStatus;
  at: string;
  label: string;
  status: "done" | "current" | "pending" | "failed";
};

export type CreateJobInput = {
  file: File;
  title: string;
  brand: string;
  campaign: string;
  notes?: string;
  durationSeconds: number;
};

export type CreateJobResponse = {
  job_id: string;
  status: JobStatus;
};
