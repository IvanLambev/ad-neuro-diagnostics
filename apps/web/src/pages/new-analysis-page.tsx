import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, LoaderCircle, Sparkles, UploadCloud } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { useCreateJobMutation } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { formatRelativeDuration } from "@/lib/utils";
import { ACCEPTED_VIDEO_EXTENSIONS, inspectVideoFile } from "@/lib/video";

const schema = z.object({
  title: z.string().min(2, "Give the ad a title."),
  brand: z.string().min(2, "Add the brand."),
  campaign: z.string().min(2, "Add the campaign."),
  notes: z.string().max(400, "Keep notes under 400 characters.").optional().or(z.literal("")),
});

type FormValues = z.infer<typeof schema>;

export function NewAnalysisPage() {
  const navigate = useNavigate();
  const mutation = useCreateJobMutation();
  const [file, setFile] = useState<File | null>(null);
  const [durationSeconds, setDurationSeconds] = useState<number | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      brand: "",
      campaign: "",
      notes: "",
    },
  });

  async function handleFileChange(nextFile: File | null) {
    setFile(nextFile);
    setFileError(null);
    setSubmitError(null);
    setDurationSeconds(null);

    if (!nextFile) {
      return;
    }

    try {
      const inspection = await inspectVideoFile(nextFile);
      setDurationSeconds(inspection.durationSeconds);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : "That video could not be validated.");
    }
  }

  const onSubmit = form.handleSubmit(async (values) => {
    setSubmitError(null);

    if (!file) {
      setFileError("Upload a video to continue.");
      return;
    }

    if (!durationSeconds) {
      setFileError("We still need a readable duration before submitting.");
      return;
    }

    try {
      const response = await mutation.mutateAsync({
        file,
        title: values.title,
        brand: values.brand,
        campaign: values.campaign,
        notes: values.notes || undefined,
        durationSeconds,
      });

      navigate(`/app/jobs/${response.job_id}`);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "The analysis could not be submitted.");
    }
  });

  return (
    <div className="grid gap-8 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
      <section className="space-y-7">
        <div className="max-w-3xl">
          <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">New analysis</div>
          <h1 className="mt-2 max-w-3xl text-balance text-4xl font-semibold tracking-tight">
            Upload the ad and hand it off to the queue.
          </h1>
          <p className="mt-3 text-base leading-7 text-muted-foreground">
            We validate file type and duration first, then send the ad to the backend, create a job, and move you into a proper progress view.
          </p>
        </div>

        <Card className="overflow-hidden rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="border-b border-border/60 px-6 py-6 sm:px-8">
            <CardTitle>Upload details</CardTitle>
            <CardDescription>Keep the submission short, clear, and ready for analysis.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 px-6 py-6 sm:px-8 sm:py-8">
            {submitError ? (
              <div className="flex items-start gap-3 rounded-[1.4rem] border border-destructive/30 bg-destructive/5 px-4 py-4 text-sm text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span className="leading-6">{submitError}</span>
              </div>
            ) : null}

            <form className="space-y-6" onSubmit={onSubmit}>
              <div className="rounded-[1.6rem] border border-dashed border-border/80 bg-secondary/20 p-4 sm:p-5">
                <div className="mb-3 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/12 text-accent">
                    <UploadCloud className="h-5 w-5" />
                  </div>
                  <div>
                    <Label htmlFor="file" className="text-base font-medium text-foreground">
                      Video upload
                    </Label>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      Accepted: {ACCEPTED_VIDEO_EXTENSIONS.join(", ")}. Max duration: 60 seconds.
                    </p>
                  </div>
                </div>
                <Input
                  id="file"
                  type="file"
                  accept={ACCEPTED_VIDEO_EXTENSIONS.join(",")}
                  onChange={(event) => void handleFileChange(event.target.files?.[0] ?? null)}
                  className="min-h-12 bg-background"
                />
                {fileError ? <p className="text-sm text-destructive">{fileError}</p> : null}
                {file && !fileError ? (
                  <div className="mt-4 rounded-[1.25rem] border border-border/70 bg-background/90 px-4 py-4">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-foreground">{file.name}</div>
                        <div className="mt-1 text-sm leading-6 text-muted-foreground">
                          {durationSeconds ? formatRelativeDuration(durationSeconds) : "Checking duration"} ·{" "}
                          {Math.max(1, Math.round(file.size / 1024 / 1024))} MB
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <Field label="Ad title" id="title" error={form.formState.errors.title?.message}>
                  <Input id="title" className="min-h-11" {...form.register("title")} />
                </Field>
                <Field label="Brand" id="brand" error={form.formState.errors.brand?.message}>
                  <Input id="brand" className="min-h-11" {...form.register("brand")} />
                </Field>
                <Field label="Campaign" id="campaign" error={form.formState.errors.campaign?.message}>
                  <Input id="campaign" className="min-h-11" {...form.register("campaign")} />
                </Field>
                <Field
                  label="Optional notes"
                  id="notes"
                  error={form.formState.errors.notes?.message}
                  className="md:col-span-2"
                >
                  <Textarea
                    id="notes"
                    rows={5}
                    className="min-h-32 resize-y bg-background"
                    placeholder="Any context for this cut, audience, or what you want to learn from the report."
                    {...form.register("notes")}
                  />
                </Field>
              </div>

              <div className="flex flex-col gap-3 border-t border-border/60 pt-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-sm leading-6 text-muted-foreground">
                  {mutation.isPending
                    ? "Creating your analysis job and sending you to progress tracking."
                    : "After submission, you should land on a progress page with queue and stage updates."}
                </div>
                <Button size="lg" type="submit" disabled={mutation.isPending || !file || !durationSeconds} className="min-w-52">
                  {mutation.isPending ? (
                    <>
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                      Creating job...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      Start analysis
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-5">
        <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
          <CardHeader className="px-6 py-6">
            <CardDescription>Estimated processing time</CardDescription>
            <CardTitle className="text-2xl">A few minutes in production</CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-6 text-sm leading-6 text-muted-foreground">
            Timing depends on upload speed, queue depth, and the GPU worker. The next screen tracks the job as it moves through validation, TRIBE, feature extraction, and report generation.
          </CardContent>
        </Card>
        <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
          <CardHeader className="px-6 py-6">
            <CardDescription>What the user gets</CardDescription>
            <CardTitle className="text-2xl">A plain-English readout, not a lab dump</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 px-6 pb-6 text-sm leading-6 text-muted-foreground">
            <p>Quick Read with Attention, Clarity, and Memorability.</p>
            <p>Strong moments and potential weak moments.</p>
            <p>Similar ads to compare against.</p>
            <p>Technical appendix behind an accordion instead of leading the page.</p>
          </CardContent>
        </Card>
        {file && durationSeconds ? (
          <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
            <CardHeader className="px-6 py-6">
              <CardDescription>Ready to submit</CardDescription>
              <CardTitle className="break-all text-xl leading-8">{file.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 px-6 pb-6 text-sm text-muted-foreground">
              <div>{formatRelativeDuration(durationSeconds)}</div>
              <div>{Math.max(1, Math.round(file.size / 1024 / 1024))} MB upload</div>
            </CardContent>
          </Card>
        ) : null}
      </section>
    </div>
  );
}

function Field({
  children,
  className,
  error,
  id,
  label,
}: {
  children: React.ReactNode;
  error?: string;
  id: string;
  label: string;
  className?: string;
}) {
  return (
    <div className={className ? `space-y-2 ${className}` : "space-y-2"}>
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
