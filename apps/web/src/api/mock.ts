import type {
  AnalysisReport,
  CreateJobInput,
  CreateJobResponse,
  Job,
  JobEvent,
  JobStatus,
} from "@/api/types";

const STORAGE_KEY = "and-demo-db";
const timeline = [
  { step: "queued", seconds: 3, label: "Queued for the next available processing slot" },
  { step: "validating", seconds: 4, label: "Checking the file, duration, and metadata" },
  { step: "normalizing", seconds: 5, label: "Preparing the clip for analysis" },
  { step: "running_tribe", seconds: 10, label: "Running the core signal pass" },
  { step: "extracting_features", seconds: 5, label: "Extracting temporal features" },
  { step: "benchmarking", seconds: 4, label: "Comparing against similar historical ads" },
  { step: "generating_report", seconds: 4, label: "Writing the plain-English report" },
] as const satisfies Array<{ step: Exclude<JobStatus, "completed" | "failed">; seconds: number; label: string }>;

type StoredJob = {
  job_id: string;
  title: string;
  brand: string;
  campaign: string;
  notes?: string;
  filename: string;
  duration_sec: number;
  created_at: string;
  started_at: string;
  updated_at: string;
  retries: number;
  should_fail: boolean;
};

type MockDb = {
  jobs: StoredJob[];
};

function readDb(): MockDb {
  const existing = localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return JSON.parse(existing) as MockDb;
  }

  const seeded = seedDb();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seeded));
  return seeded;
}

function writeDb(db: MockDb) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

function seedDb(): MockDb {
  const now = Date.now();
  return {
    jobs: [
      {
        job_id: "job_demo_completed",
        title: "Spring Launch Cutdown",
        brand: "Northline Spark",
        campaign: "Fresh Start",
        notes: "Launch spot for retail push.",
        filename: "spring-launch.mp4",
        duration_sec: 29.8,
        created_at: new Date(now - 1000 * 60 * 90).toISOString(),
        started_at: new Date(now - 1000 * 60 * 90).toISOString(),
        updated_at: new Date(now - 1000 * 60 * 83).toISOString(),
        retries: 0,
        should_fail: false,
      },
      {
        job_id: "job_demo_failed",
        title: "Summer Promo Teaser",
        brand: "Acorn Labs",
        campaign: "Bright Days",
        notes: "Demo failure case for retry.",
        filename: "summer-teaser.mov",
        duration_sec: 41.2,
        created_at: new Date(now - 1000 * 60 * 18).toISOString(),
        started_at: new Date(now - 1000 * 60 * 18).toISOString(),
        updated_at: new Date(now - 1000 * 60 * 15).toISOString(),
        retries: 0,
        should_fail: true,
      },
      {
        job_id: "job_demo_active",
        title: "Studio Reveal",
        brand: "Solstice Audio",
        campaign: "Better Sound",
        notes: "Current in-flight demo.",
        filename: "studio-reveal.webm",
        duration_sec: 24.5,
        created_at: new Date(now - 1000 * 12).toISOString(),
        started_at: new Date(now - 1000 * 12).toISOString(),
        updated_at: new Date(now - 1000 * 12).toISOString(),
        retries: 0,
        should_fail: false,
      },
    ],
  };
}

function computeStatus(job: StoredJob) {
  const startedAt = new Date(job.started_at).getTime();
  const elapsed = Math.max(0, (Date.now() - startedAt) / 1000);

  let accumulated = 0;
  for (let index = 0; index < timeline.length; index += 1) {
    const stage = timeline[index];
    const nextAccumulated = accumulated + stage.seconds;
    const progressBase = Math.round((index / timeline.length) * 100);
    const progressCap = Math.round(((index + 1) / timeline.length) * 100);

    if (job.should_fail && elapsed >= accumulated + stage.seconds && stage.step === "benchmarking") {
      return {
        status: "failed" as const,
        current_step: "benchmarking" as const,
        progress: 78,
        updated_at: new Date(startedAt + nextAccumulated * 1000).toISOString(),
      };
    }

    if (elapsed < nextAccumulated) {
      const ratio = (elapsed - accumulated) / stage.seconds;
      return {
        status: stage.step,
        current_step: stage.step,
        progress: Math.max(progressBase + Math.round((progressCap - progressBase) * ratio), 4),
        updated_at: new Date(Date.now()).toISOString(),
      };
    }

    accumulated = nextAccumulated;
  }

  return {
    status: "completed" as const,
    current_step: "completed" as const,
    progress: 100,
    updated_at: new Date(startedAt + accumulated * 1000).toISOString(),
  };
}

function toJob(job: StoredJob): Job {
  const runtime = computeStatus(job);
  return {
    id: job.job_id,
    title: job.title,
    brand: job.brand,
    campaign: job.campaign,
    notes: job.notes,
    status: runtime.status,
    progress: runtime.progress,
    current_step: runtime.current_step,
    created_at: job.created_at,
    updated_at: runtime.updated_at,
    started_at: job.started_at,
    completed_at: runtime.status === "completed" ? runtime.updated_at : null,
    error_message: runtime.status === "failed" ? "The benchmark comparison timed out. Retry to regenerate the report." : undefined,
  };
}

function createReport(job: Job): AnalysisReport {
  const brandHash = job.brand.length % 3;
  const attentionScore = Number((2.4 + brandHash * 0.25).toFixed(2));
  const clarityScore = Number((2.1 + (job.title.length % 4) * 0.14).toFixed(2));
  const memorabilityScore = Number((2.0 + (job.campaign.length % 5) * 0.11).toFixed(2));

  return {
    job_id: job.id,
    status: "completed",
    ad: {
      ad_id: `${job.brand.toLowerCase().replace(/\s+/g, "-")}-${job.id}`,
      title: job.title,
      brand: job.brand,
      campaign: job.campaign,
      duration_sec: 0,
    },
    summary: {
      attention: {
        band: attentionScore > 2.6 ? "slightly_strong" : "average",
        score: attentionScore,
        dataset_mean: 2.31,
        peer_mean: 2.18,
        percentile: 58,
        confidence_label: "moderate",
        confidence_score: 0.66,
      },
      clarity: {
        band: clarityScore > 2.35 ? "strong" : "average",
        score: clarityScore,
        dataset_mean: 2.22,
        peer_mean: 2.11,
        percentile: 67,
        confidence_label: "moderate",
        confidence_score: 0.66,
      },
      memorability: {
        band: memorabilityScore > 2.35 ? "slightly_strong" : "average",
        score: memorabilityScore,
        dataset_mean: 2.15,
        peer_mean: 2.04,
        percentile: 63,
        confidence_label: "moderate",
        confidence_score: 0.66,
      },
    },
    confidence: {
      score: 0.66,
      label: "moderate",
    },
    creative_profile: {
      label: "Punchy opener",
      summary: "The ad appears to win attention early, but the closing payoff is not as settled as the opening beat.",
    },
    tracks: {
      hook_strength: {
        label: "Hook strength",
        score: 71,
        percentile: 68,
        band: "slightly_strong",
        short_description: "How strongly the first seconds pull people in.",
        long_description: "Fast early pull, opening energy, and whether the ad earns attention before the story settles.",
        why_it_matters: ["stronger early response", "richer color energy"],
      },
      clarity_stability: {
        label: "Clarity stability",
        score: 63,
        percentile: 59,
        band: "average",
        short_description: "How easy the message feels to stay with over time.",
        long_description: "Stability through pacing, intensity changes, and whether the ad stays readable instead of feeling noisy.",
        why_it_matters: ["more controlled intensity swings", "lighter speech load"],
      },
      value_lift: {
        label: "Value lift",
        score: 66,
        percentile: 62,
        band: "slightly_strong",
        short_description: "Whether the ad strengthens around the product, offer, or closing payoff.",
        long_description: "Late-stage lift matters because strong ads often build value instead of peaking too early and fading.",
        why_it_matters: ["stronger late-stage lift", "a stronger standout peak"],
      },
      trust_close: {
        label: "Trust close",
        score: 48,
        percentile: 41,
        band: "average",
        short_description: "How steady and reassuring the closing section feels.",
        long_description: "This track is a proxy for whether the final product, brand, or CTA lands with enough stability to reduce friction.",
        why_it_matters: ["faster cutting", "weaker late-stage lift"],
      },
    },
    strengths: [
      `${job.title} starts with a clean hook that should help viewers settle into the story quickly.`,
      "The pacing stays tight enough to keep attention from sagging in the middle third.",
    ],
    risks: [
      "The final brand handoff could land harder if the close repeated one earlier visual motif.",
      "There is a mild clarity dip around the transition into the offer section.",
    ],
    similar_ads: [
      {
        ad_id: "doritos-fvybcesuxmm",
        brand: "Doritos",
        distance: 6.37,
        why_similar: "Close pacing and a similar late-brand reveal rhythm.",
      },
      {
        ad_id: "sprite-axj7aeoe2ie",
        brand: "Sprite",
        distance: 7.18,
        why_similar: "Comparable early hook intensity with a lighter middle section.",
      },
    ],
    event_alignment: [
      {
        type: "scene_cut",
        label: "Scene-change burst",
        start_sec: 2,
        end_sec: 2.25,
        detail: "A sharper visual transition happens around this point.",
        source: "video pacing heuristic",
      },
      {
        type: "brand_mention",
        label: "Brand/logo cue",
        start_sec: 22,
        end_sec: 23,
        detail: "A brand cue appears here in the spoken or on-screen text. This is a language-based proxy, not direct logo detection.",
        text: "The brand lands clearly in the closing line.",
        source: "events.csv transcript heuristic",
      },
      {
        type: "cta_timing",
        label: "CTA timing",
        start_sec: 25,
        end_sec: 27,
        detail: "The transcript shifts into an action-oriented or offer-oriented phrase here.",
        text: "Get yours today.",
        source: "events.csv transcript heuristic",
      },
    ],
    moments: [
      {
        id: "strong-0",
        start_sec: 0,
        end_sec: 5,
        label: "Strong hook",
        summary: "The opening gets to the point quickly and is likely to help viewers settle into the ad.",
        impact: ["attention", "clarity"],
        frame_index: 0,
        timestamp_label: "0:00",
        kind: "strong",
        events: [],
      },
      {
        id: "weak-13",
        start_sec: 13,
        end_sec: 19,
        label: "Potential weak moment",
        summary: "The message becomes slightly harder to track in this middle section.",
        impact: ["clarity"],
        frame_index: 13,
        timestamp_label: "0:13",
        kind: "weak",
        events: [],
      },
      {
        id: "strong-22",
        start_sec: 22,
        end_sec: 28,
        label: "Brand lands clearly",
        summary: "The brand handoff is one of the strongest closing moments in the demo report.",
        impact: ["memorability"],
        frame_index: 22,
        timestamp_label: "0:22",
        kind: "strong",
        events: [
          {
            type: "brand_mention",
            label: "Brand/logo cue",
            start_sec: 22,
            end_sec: 23,
            detail: "A brand cue appears here in the spoken or on-screen text. This is a language-based proxy, not direct logo detection.",
            text: "The brand lands clearly in the closing line.",
            source: "events.csv transcript heuristic",
          },
          {
            type: "cta_timing",
            label: "CTA timing",
            start_sec: 25,
            end_sec: 27,
            detail: "The transcript shifts into an action-oriented or offer-oriented phrase here.",
            text: "Get yours today.",
            source: "events.csv transcript heuristic",
          },
        ],
      },
    ],
    why: {
      attention: ["Bigger shifts in scene intensity than the average ad in the library."],
      clarity: ["The offer reveal is fast, but the edit remains mostly readable."],
      memorability: ["The closing frame is distinct, but the brand mnemonic could repeat sooner."],
    },
    assets: {},
    playback: {
      frame_count: 0,
      seconds_per_frame: 1,
      brain_frame_url_template: undefined,
      chapters: [
        {
          title: "Strong hook",
          timestamp_label: "0:00",
          start_sec: 0,
          frame_index: 0,
        },
        {
          title: "Potential weak moment",
          timestamp_label: "0:13",
          start_sec: 13,
          frame_index: 13,
        },
        {
          title: "Brand lands clearly",
          timestamp_label: "0:22",
          start_sec: 22,
          frame_index: 22,
        },
      ],
    },
    technical: {
      top_rois: ["V8-rh", "V8-lh"],
      strongest_timestep: 11,
    },
  };
}

export const mockApi = {
  async getJobs() {
    const db = readDb();
    return db.jobs
      .map(toJob)
      .sort((left, right) => right.created_at.localeCompare(left.created_at));
  },
  async getJob(jobId: string) {
    const db = readDb();
    const job = db.jobs.find((entry) => entry.job_id === jobId);
    if (!job) {
      throw new Error("Job not found.");
    }
    return toJob(job);
  },
  async getJobEvents(jobId: string) {
    const db = readDb();
    const stored = db.jobs.find((entry) => entry.job_id === jobId);
    if (!stored) {
      throw new Error("Job not found.");
    }

    const job = toJob(stored);
    const startedAt = new Date(stored.started_at).getTime();
    let accumulated = 0;

    const events = timeline.map<JobEvent>((stage) => {
      accumulated += stage.seconds;
      const stageAt = new Date(startedAt + accumulated * 1000).toISOString();
      let status: JobEvent["status"] = "pending";
      if (job.status === "failed" && stage.step === "benchmarking") {
        status = "failed";
      } else if (job.status === "completed" || accumulated * 1000 < Date.now() - startedAt) {
        status = "done";
      } else if (job.current_step === stage.step) {
        status = "current";
      }

      return {
        step: stage.step,
        at: stageAt,
        label: stage.label,
        status,
      };
    });

    if (job.status === "completed") {
      events.push({
        step: "completed",
        at: job.updated_at,
        label: "Report ready to review",
        status: "done",
      });
    }

    return events;
  },
  async createJob(input: CreateJobInput): Promise<CreateJobResponse> {
    const db = readDb();
    const now = new Date().toISOString();
    const title = input.title.trim();
    const shouldFail = /fail|retry/i.test(`${input.title} ${input.notes ?? ""}`);

    const job: StoredJob = {
      job_id: `job_${Math.random().toString(36).slice(2, 10)}`,
      title,
      brand: input.brand.trim(),
      campaign: input.campaign.trim(),
      notes: input.notes?.trim(),
      filename: input.file.name,
      duration_sec: Number(input.durationSeconds.toFixed(1)),
      created_at: now,
      started_at: now,
      updated_at: now,
      retries: 0,
      should_fail: shouldFail,
    };

    db.jobs.unshift(job);
    writeDb(db);

    return {
      job_id: job.job_id,
      status: "queued",
    };
  },
  async getReport(jobId: string) {
    const job = await this.getJob(jobId);
    if (job.status !== "completed") {
      throw new Error("Report is not ready yet.");
    }
    return createReport(job);
  },
  async retryJob(jobId: string) {
    const db = readDb();
    const job = db.jobs.find((entry) => entry.job_id === jobId);
    if (!job) {
      throw new Error("Job not found.");
    }
    job.started_at = new Date().toISOString();
    job.updated_at = job.started_at;
    job.retries += 1;
    job.should_fail = false;
    writeDb(db);
    return toJob(job);
  },
};
