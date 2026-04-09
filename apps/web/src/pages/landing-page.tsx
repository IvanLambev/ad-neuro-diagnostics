import { AlertCircle, ArrowRight, ChartNoAxesCombined, PlayCircle, ScanSearch, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { BrandMark } from "@/components/brand-mark";
import { BrainHeatmap } from "@/components/brain-heatmap";
import { DashboardPreview } from "@/components/dashboard-preview";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuthState } from "@/lib/auth";

const features = [
  {
    icon: ScanSearch,
    title: "Plain-English report",
    description: "Lead with Attention, Clarity, and Memorability instead of raw lab-side feature names.",
  },
  {
    icon: ChartNoAxesCombined,
    title: "Historical comparison",
    description: "See how a spot stacks up against similar ads in the historical library before launch.",
  },
  {
    icon: ShieldCheck,
    title: "Guidance, not false certainty",
    description: "Use the analysis as a decision-making aid, not a promise of business outcomes.",
  },
];

const problems = [
  {
    title: "You don't know why ads fail",
    description:
      "Traditional analytics tell you what happened, not why it happened. You're left guessing which creative elements work.",
  },
  {
    title: "A/B testing is slow and expensive",
    description:
      "Running tests costs thousands in ad spend and weeks of time. By the time you have data, your budget is gone.",
  },
  {
    title: "Analytics show results, not causes",
    description:
      "Click-through rates and conversions don't explain attention patterns, emotional triggers, or cognitive friction.",
  },
];

export function LandingPage() {
  const auth = useAuthState();

  return (
    <main className="min-h-screen bg-background">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6 lg:px-10">
          <BrandMark />

          <nav className="hidden items-center gap-6 md:flex">
            <a href="#features" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#preview" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Preview
            </a>
            <a href="#workflow" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Workflow
            </a>
            <a href="#guidance" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Guidance
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {!auth.isSignedIn ? (
              <Button asChild variant="ghost" size="sm" className="hidden md:inline-flex">
                <Link to="/sign-in">Sign in</Link>
              </Button>
            ) : null}
            <Button asChild size="sm">
              <Link to={auth.isSignedIn ? "/app" : "/sign-in"}>{auth.isSignedIn ? "Open app" : "Get started"}</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden border-b border-border/40 pt-32 pb-20">
        <div className="absolute inset-0 bg-gradient-to-b from-accent/5 to-transparent" />

        <div className="relative mx-auto w-full max-w-7xl px-6 lg:px-10">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs">
              <div className="h-1.5 w-1.5 rounded-full bg-accent" />
              <span className="text-muted-foreground">Customer-facing ad analysis</span>
            </div>

            <h1 className="mb-6 text-balance text-5xl font-bold leading-tight tracking-tight md:text-6xl lg:text-7xl">
              Know how an ad may land <span className="text-accent">before you launch</span>
            </h1>

            <p className="mx-auto mb-8 max-w-3xl text-balance text-lg leading-relaxed text-muted-foreground md:text-xl">
              Upload a spot, track the analysis job, and get a clear read on Attention, Clarity, Memorability, and similar historical ads without making the interface feel like a neuroscience lab.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button asChild size="lg" className="w-full gap-2 sm:w-auto">
                <Link to={auth.isSignedIn ? "/app/new" : "/sign-in"}>
                  Analyze your ad
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="w-full gap-2 sm:w-auto">
                <Link to={auth.isSignedIn ? "/app/library" : "/sign-in"}>
                  <PlayCircle className="h-4 w-4" />
                  See the preview
                </Link>
              </Button>
            </div>
          </div>

          <div id="preview" className="mx-auto mt-16 max-w-6xl">
            <BrainHeatmap />
          </div>
        </div>
      </section>

      <section id="problem" className="border-b border-border/40 py-24">
        <div className="mx-auto w-full max-w-7xl px-6 lg:px-10">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-balance text-3xl font-bold tracking-tight md:text-4xl">
              Stop wasting budget on guesswork
            </h2>
            <p className="text-balance text-lg leading-relaxed text-muted-foreground">
              Most ad campaigns fail because marketers can't see what viewers actually notice, feel, or understand.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl gap-6 md:grid-cols-3">
            {problems.map((problem) => (
              <Card key={problem.title} className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-destructive/20 bg-destructive/10">
                    <AlertCircle className="h-5 w-5 text-destructive" />
                  </div>
                  <h3 className="mb-2 text-balance text-lg font-semibold">{problem.title}</h3>
                  <p className="text-balance text-sm leading-relaxed text-muted-foreground">{problem.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="border-b border-border/40 py-24">
        <div className="mx-auto w-full max-w-7xl px-6 lg:px-10">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-balance text-3xl font-bold tracking-tight md:text-4xl">
              Everything you need to review ad performance before launch
            </h2>
            <p className="text-balance text-lg leading-relaxed text-muted-foreground">
              Built for creative teams and marketers who want guidance that feels strategic, not technical for its own sake.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-6xl gap-6 md:grid-cols-3">
            {features.map((feature) => (
              <Card key={feature.title} className="group border-border/50 bg-card/50 transition-colors hover:border-accent/50">
                <CardContent className="p-6">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg border border-accent/20 bg-accent/10 text-accent transition-colors group-hover:bg-accent group-hover:text-accent-foreground">
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mb-2 text-balance text-lg font-semibold">{feature.title}</h3>
                  <p className="text-balance text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="border-b border-border/40 py-24">
        <div className="mx-auto w-full max-w-7xl px-6 lg:px-10">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-balance text-3xl font-bold tracking-tight md:text-4xl">Simple workflow, no waiting on one request</h2>
            <p className="text-balance text-lg leading-relaxed text-muted-foreground">
              Upload the ad, get a job ID back immediately, watch the progress state, and open the structured report when it&apos;s ready.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-6xl gap-6 md:grid-cols-4">
            {[
              "Upload a video ad up to 60 seconds",
              "Receive a job and route to progress",
              "Poll or subscribe to updates",
              "Open the final report when complete",
            ].map((step, index) => (
              <Card key={step} className="border-border/50 bg-card/50">
                <CardContent className="p-6">
                  <div className="mb-4 text-xs font-medium uppercase tracking-[0.2em] text-accent">Step {index + 1}</div>
                  <p className="text-sm leading-7 text-foreground">{step}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="guidance" className="border-b border-border/40 py-24">
        <div className="mx-auto grid w-full max-w-7xl gap-12 px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-10">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs">
              <div className="h-1.5 w-1.5 rounded-full bg-accent" />
              <span className="text-muted-foreground">What teams actually get</span>
            </div>
            <h2 className="text-balance text-3xl font-bold tracking-tight md:text-4xl">
              Built for creative review, not for throwing technical jargon at a client.
            </h2>
            <p className="mt-4 text-base leading-8 text-muted-foreground">
              The frontend keeps the story customer-facing. It starts with a quick read, shows strong moments and potential weak moments, points to similar ads, and keeps the technical appendix tucked away until someone genuinely needs it.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              {
                title: "Quick Read first",
                copy: "The report leads with plain-English strategy language instead of raw feature outputs.",
              },
              {
                title: "Historical context",
                copy: "Every result is framed against prior ads so the guidance feels anchored, not arbitrary.",
              },
              {
                title: "Progress tracking",
                copy: "Users can watch a job move through stages instead of sitting on a loading spinner.",
              },
              {
                title: "Retry when needed",
                copy: "If something fails, the UI supports a retry path instead of leaving the job stranded.",
              },
            ].map((item) => (
              <Card key={item.title} className="border-border/50 bg-card/50">
                <CardContent className="p-6">
                  <h3 className="mb-2 text-lg font-semibold">{item.title}</h3>
                  <p className="text-sm leading-7 text-muted-foreground">{item.copy}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-border/40 py-24">
        <div className="mx-auto w-full max-w-7xl px-6 lg:px-10">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-balance text-3xl font-bold tracking-tight md:text-4xl">See the product view, not just the promise</h2>
            <p className="text-balance text-lg leading-relaxed text-muted-foreground">
              The homepage now includes the actual dashboard-style preview from the reference so the product story feels grounded in a concrete interface.
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-7xl">
            <DashboardPreview />
          </div>
        </div>
      </section>

      <section className="py-24">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-center px-6 text-center lg:px-10">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs">
            <div className="h-1.5 w-1.5 rounded-full bg-accent" />
            <span className="text-muted-foreground">Ready to try it</span>
          </div>
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight md:text-4xl">
            Upload the next cut, follow the job, and review the report in one flow.
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
            The product is built to feel lightweight for marketers while still leaving room for a technical appendix and backend integration when we wire the full stack together.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row">
            <Button asChild size="lg">
              <Link to={auth.isSignedIn ? "/app/new" : "/sign-in"}>Start a new analysis</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to={auth.isSignedIn ? "/app/library" : "/sign-in"}>Browse the historical library</Link>
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
