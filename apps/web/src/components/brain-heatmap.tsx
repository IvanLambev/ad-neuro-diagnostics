import { Card } from "@/components/ui/card";

export function BrainHeatmap() {
  return (
    <Card className="relative overflow-hidden border border-border/50 bg-card/50 p-1 backdrop-blur-sm">
      <div className="aspect-video overflow-hidden rounded-lg bg-gradient-to-br from-muted to-background">
        <div className="relative flex h-full items-center justify-center p-8">
          <div className="relative h-full w-full max-w-2xl overflow-hidden rounded-lg border border-border bg-muted/50">
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-8 text-center">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-accent/30 to-accent/10" />
              <div className="h-4 w-48 rounded-full bg-foreground/10" />
              <div className="h-3 w-64 rounded-full bg-foreground/5" />
            </div>

            <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450">
              <defs>
                <radialGradient id="heatmap1" cx="50%" cy="40%">
                  <stop offset="0%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0.6 }} />
                  <stop offset="30%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0.3 }} />
                  <stop offset="60%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0.1 }} />
                  <stop offset="100%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0 }} />
                </radialGradient>
                <radialGradient id="heatmap2" cx="30%" cy="60%">
                  <stop offset="0%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0.4 }} />
                  <stop offset="40%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0.2 }} />
                  <stop offset="100%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0 }} />
                </radialGradient>
                <radialGradient id="heatmap3" cx="70%" cy="50%">
                  <stop offset="0%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0.3 }} />
                  <stop offset="50%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0.1 }} />
                  <stop offset="100%" style={{ stopColor: "rgb(59, 130, 246)", stopOpacity: 0 }} />
                </radialGradient>
              </defs>

              <circle cx="400" cy="180" r="150" fill="url(#heatmap1)" />
              <circle cx="240" cy="270" r="100" fill="url(#heatmap2)" />
              <circle cx="560" cy="225" r="80" fill="url(#heatmap3)" />
            </svg>

            <div className="absolute right-4 top-4 flex flex-col gap-2">
              <div className="flex items-center gap-2 rounded-lg border border-accent/30 bg-background/80 px-3 py-1.5 text-xs backdrop-blur-sm">
                <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
                <span className="font-mono text-accent">Analyzing...</span>
              </div>
            </div>

            <div className="absolute bottom-4 left-4 flex gap-2">
              {[
                ["Attention", "87%"],
                ["Emotion", "92%"],
                ["Clarity", "78%"],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg border border-border/50 bg-background/80 px-3 py-2 text-xs backdrop-blur-sm">
                  <div className="font-mono text-muted-foreground">{label}</div>
                  <div className="mt-1 font-mono text-lg font-semibold text-accent">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
