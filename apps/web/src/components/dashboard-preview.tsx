import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function DashboardPreview() {
  return (
    <Card className="overflow-hidden border border-border/50 bg-card/50 backdrop-blur-sm">
      <div className="border-b border-border/40 bg-muted/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10" />
            <div>
              <div className="text-sm font-semibold">Product Launch Ad - V3</div>
              <div className="text-xs text-muted-foreground">Analyzed 2 minutes ago</div>
            </div>
          </div>
          <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-medium text-accent">Ready to deploy</div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <div className="border-b border-border/40 px-4">
          <TabsList className="h-12 w-full justify-start rounded-none border-0 bg-transparent p-0">
            <TabsTrigger value="overview" className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none">
              Overview
            </TabsTrigger>
            <TabsTrigger value="heatmap" className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none">
              Heatmap
            </TabsTrigger>
            <TabsTrigger value="emotions" className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none">
              Emotions
            </TabsTrigger>
            <TabsTrigger value="insights" className="rounded-none border-b-2 border-transparent data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none">
              Insights
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="m-0 p-6">
          <div className="grid gap-6 md:grid-cols-3">
            {[
              ["Overall Score", "8.7", "+12% vs previous"],
              ["Attention Peak", "94%", "At 3.2s (logo reveal)"],
              ["Emotional Engagement", "89%", "Positive sentiment"],
            ].map(([label, value, note]) => (
              <Card key={label} className="border-border/40 bg-background/50 p-4">
                <div className="mb-2 text-xs font-medium text-muted-foreground">{label}</div>
                <div className="mb-1 flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-accent">{value}</span>
                  {label === "Overall Score" ? <span className="text-sm text-muted-foreground">/10</span> : null}
                </div>
                <div className="text-xs text-muted-foreground">{note}</div>
              </Card>
            ))}
          </div>

          <div className="mt-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Attention Over Time</h3>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-accent" />
                  <span className="text-muted-foreground">Attention</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-chart-2" />
                  <span className="text-muted-foreground">Engagement</span>
                </div>
              </div>
            </div>

            <div className="relative h-48 rounded-lg border border-border/40 bg-muted/20 p-4">
              <svg className="h-full w-full" viewBox="0 0 800 160" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="attentionGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0.3 }} />
                    <stop offset="100%" style={{ stopColor: "rgb(139, 92, 246)", stopOpacity: 0 }} />
                  </linearGradient>
                </defs>

                <path d="M 0 120 Q 100 100, 200 80 T 400 40 T 600 60 T 800 50" fill="none" stroke="rgb(139, 92, 246)" strokeWidth="3" />
                <path d="M 0 120 Q 100 100, 200 80 T 400 40 T 600 60 T 800 50 L 800 160 L 0 160 Z" fill="url(#attentionGradient)" />
                <path d="M 0 130 Q 100 115, 200 95 T 400 70 T 600 80 T 800 65" fill="none" stroke="rgb(59, 130, 246)" strokeWidth="2" opacity="0.6" />
              </svg>

              <div className="absolute bottom-2 left-4 right-4 flex justify-between text-xs text-muted-foreground">
                <span>0s</span>
                <span>5s</span>
                <span>10s</span>
                <span>15s</span>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="heatmap" className="m-0 p-6">
          <div className="flex h-64 items-center justify-center text-muted-foreground">Heatmap visualization would appear here</div>
        </TabsContent>

        <TabsContent value="emotions" className="m-0 p-6">
          <div className="flex h-64 items-center justify-center text-muted-foreground">Emotional analysis would appear here</div>
        </TabsContent>

        <TabsContent value="insights" className="m-0 p-6">
          <div className="space-y-4">
            {[
              ["Strong opening hook", "The first 3 seconds capture 94% attention. Viewers are immediately engaged with the visual."],
              ["Clear value proposition", "The message is understood quickly with minimal cognitive load. Clarity score: 89%."],
              ["Optimize mid-section pacing", "Attention drops slightly at 8-10s. Consider adding motion or text emphasis here."],
            ].map(([title, body], index) => (
              <div
                key={title}
                className={index === 2 ? "flex gap-3 rounded-lg border border-yellow-500/40 bg-yellow-500/5 p-4" : "flex gap-3 rounded-lg border border-border/40 bg-muted/20 p-4"}
              >
                <div className={index === 2 ? "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-yellow-500/10" : "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10"}>
                  <div className={index === 2 ? "h-3 w-3 rounded-full bg-yellow-500" : "h-3 w-3 rounded-full bg-accent"} />
                </div>
                <div className="flex-1">
                  <div className="mb-1 text-sm font-semibold">{title}</div>
                  <div className="text-sm text-muted-foreground">{body}</div>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
