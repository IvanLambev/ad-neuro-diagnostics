import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { createApiClient } from "@/api/client";
import type { CreateJobInput, JobStatus } from "@/api/types";
import { appConfig } from "@/lib/config";
import { useAuthState } from "@/lib/auth";

const ACTIVE_STATUSES: JobStatus[] = [
  "queued",
  "validating",
  "normalizing",
  "running_tribe",
  "extracting_features",
  "benchmarking",
  "generating_report",
];

export function useApi() {
  const auth = useAuthState();

  return useMemo(
    () =>
      createApiClient({
        apiBaseUrl: appConfig.apiBaseUrl,
        getToken: auth.getToken,
      }),
    [auth.getToken],
  );
}

export function useJobsQuery() {
  const api = useApi();
  return useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.getJobs(),
    refetchInterval: (query) =>
      query.state.data?.some((job) => ACTIVE_STATUSES.includes(job.status)) ? 5000 : 15000,
  });
}

export function useJobQuery(jobId: string) {
  const api = useApi();
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => api.getJob(jobId),
    refetchInterval: (query) =>
      query.state.data && ACTIVE_STATUSES.includes(query.state.data.status) ? 5000 : false,
  });
}

export function useJobEventsQuery(jobId: string) {
  const api = useApi();
  return useQuery({
    queryKey: ["jobs", jobId, "events"],
    queryFn: () => api.getJobEvents(jobId),
    refetchInterval: 5000,
  });
}

export function useReportQuery(jobId: string, enabled = true) {
  const api = useApi();
  return useQuery({
    queryKey: ["jobs", jobId, "report"],
    queryFn: () => api.getReport(jobId),
    enabled,
  });
}

export function useCreateJobMutation() {
  const api = useApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateJobInput) => api.createJob(payload),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["jobs", data.job_id] });
    },
  });
}

export function useRetryJobMutation(jobId: string) {
  const api = useApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.retryJob(jobId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      await queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
      await queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "events"] });
      await queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "report"] });
    },
  });
}
