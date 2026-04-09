import { zodResolver } from "@hookform/resolvers/zod";
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
    if (!file) {
      setFileError("Upload a video to continue.");
      return;
    }

    if (!durationSeconds) {
      setFileError("We still need a readable duration before submitting.");
      return;
    }

    const response = await mutation.mutateAsync({
      file,
      title: values.title,
      brand: values.brand,
      campaign: values.campaign,
      notes: values.notes || undefined,
      durationSeconds,
    });

    navigate(`/app/jobs/${response.job_id}`);
  });

  return (
    <div className="grid gap-8 lg:grid-cols-[1.12fr_0.88fr]">
      <section className="space-y-6">
        <div className="max-w-3xl">
          <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">New analysis</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Upload the ad and hand it off to the queue.</h1>
          <p className="mt-3 text-base leading-7 text-muted-foreground">
            The frontend validates format and duration first, then sends the ad to `/v1/jobs`, receives a `job_id`, and routes straight into tracked progress.
          </p>
        </div>

        <Card className="rounded-[2rem] border-border/70 bg-card/96 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
          <CardHeader className="px-8 pt-8">
            <CardTitle>Upload details</CardTitle>
            <CardDescription>Keep the submission short, clear, and ready for analysis.</CardDescription>
          </CardHeader>
          <CardContent className="px-8 pb-8">
            <form className="space-y-6" onSubmit={onSubmit}>
              <div className="space-y-2">
                <Label htmlFor="file">Video upload</Label>
                <Input
                  id="file"
                  type="file"
                  accept={ACCEPTED_VIDEO_EXTENSIONS.join(",")}
                  onChange={(event) => void handleFileChange(event.target.files?.[0] ?? null)}
                />
                <p className="text-sm text-muted-foreground">Accepted: {ACCEPTED_VIDEO_EXTENSIONS.join(", ")}. Max duration: 60 seconds.</p>
                {fileError ? <p className="text-sm text-destructive">{fileError}</p> : null}
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <Field label="Ad title" id="title" error={form.formState.errors.title?.message}>
                  <Input id="title" {...form.register("title")} />
                </Field>
                <Field label="Brand" id="brand" error={form.formState.errors.brand?.message}>
                  <Input id="brand" {...form.register("brand")} />
                </Field>
                <Field label="Campaign" id="campaign" error={form.formState.errors.campaign?.message}>
                  <Input id="campaign" {...form.register("campaign")} />
                </Field>
                <Field label="Optional notes" id="notes" error={form.formState.errors.notes?.message}>
                  <Textarea id="notes" rows={5} className="min-h-28" {...form.register("notes")} />
                </Field>
              </div>

              <Button size="lg" type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Submitting..." : "Submit for analysis"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-5">
        <Card className="rounded-[1.75rem] border-border/70 bg-card/96 shadow-[0_14px_40px_rgba(15,23,42,0.05)]">
          <CardHeader className="px-6 py-6">
            <CardDescription>Estimated processing time</CardDescription>
            <CardTitle className="text-2xl">About 35 to 45 seconds in demo mode</CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-6 text-sm leading-6 text-muted-foreground">
            Production timing will depend on upload speed, queue depth, and the backend worker, but the UI is already set up to poll for active jobs every five seconds.
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
              <CardTitle className="text-2xl">{file.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 px-6 pb-6 text-sm text-muted-foreground">
              <div>{formatRelativeDuration(durationSeconds)}</div>
              <div>{Math.round(file.size / 1024 / 1024)} MB upload</div>
            </CardContent>
          </Card>
        ) : null}
      </section>
    </div>
  );
}

function Field({
  children,
  error,
  id,
  label,
}: {
  children: React.ReactNode;
  error?: string;
  id: string;
  label: string;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
