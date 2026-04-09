import { ArrowRight, LockKeyhole, PlayCircle } from "lucide-react";
import { Navigate } from "react-router-dom";
import { BrandMark } from "@/components/brand-mark";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthSignInCard, useAuthState } from "@/lib/auth";

export function SignInPage() {
  const auth = useAuthState();

  if (auth.isSignedIn) {
    return <Navigate to="/app" replace />;
  }

  return (
    <div className="min-h-screen px-6 py-8 lg:px-10">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-8 lg:grid-cols-[1fr_1fr]">
        <div className="flex flex-col justify-between rounded-[2.25rem] border border-border/10 bg-foreground p-8 text-background shadow-[0_28px_100px_rgba(15,23,42,0.22)] lg:p-10">
          <BrandMark className="[&_div:last-child]:text-background [&_.font-mono]:text-background/60" />
          <div className="space-y-6">
            <div className="inline-flex rounded-full bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.2em] text-background/70">
              Sign in to start a new analysis
            </div>
            <div className="space-y-4">
              <h1 className="text-4xl font-semibold tracking-tight">Keep the workflow simple: sign in, upload, track, review.</h1>
              <p className="max-w-xl text-base leading-7 text-background/75">
                We are using Clerk-ready auth plumbing here, but the screen also supports a local demo mode so we can keep building and testing before the production auth keys are wired in.
              </p>
            </div>
          </div>
          <div className="grid gap-4">
            {[
              { icon: LockKeyhole, label: "Clerk-managed sign-in when keys are configured" },
              { icon: PlayCircle, label: "One-click demo mode when we just need to test the product flow" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3 rounded-[1.25rem] border border-white/10 bg-white/5 px-4 py-4">
                <item.icon className="h-5 w-5 text-accent" />
                <span className="text-sm text-background/80">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center">
          {auth.clerkEnabled ? (
            <div className="w-full">
              <AuthSignInCard />
            </div>
          ) : (
            <Card className="w-full rounded-[2rem] border-border/70 bg-card/96 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
              <CardHeader className="px-8 pt-8 lg:px-10 lg:pt-10">
                <div className="inline-flex w-fit rounded-full border border-border/70 bg-secondary px-4 py-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                  Demo sign-in
                </div>
                <CardTitle className="text-3xl">Use the local app flow</CardTitle>
                <CardDescription className="max-w-xl text-base leading-7">
                  This signs you into a mock account so we can exercise uploads, progress polling, report rendering, and retry flows before backend auth is live.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 px-8 pb-8 lg:px-10 lg:pb-10">
                <div className="rounded-[1.5rem] border border-border/70 bg-secondary/35 p-5 text-sm leading-6 text-muted-foreground">
                  Best for local product iteration while the backend and Clerk production keys are still being wired up.
                </div>
                <Button className="w-full" size="lg" onClick={auth.signIn}>
                  Continue as demo user
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
