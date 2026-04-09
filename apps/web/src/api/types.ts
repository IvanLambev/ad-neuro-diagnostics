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
  strengths: string[];
  risks: string[];
  similar_ads: Array<{
    ad_id: string;
    brand: string;
    distance: number;
    why_similar: string;
  }>;
  moments: Array<{
    start_sec: number;
    end_sec: number;
    label: string;
    impact: string[];
  }>;
  why: Record<string, string[]>;
  assets: {
    activation_curve_url?: string;
    brain_strongest_url?: string;
    brain_animation_url?: string;
  };
  technical: {
    top_rois: string[];
    strongest_timestep: number;
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
