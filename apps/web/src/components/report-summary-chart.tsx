import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AnalysisReport } from "@/api/types";

export function ReportSummaryChart({ report }: { report: AnalysisReport }) {
  const data = [
    {
      name: "Attention",
      score: report.summary.attention.score,
      dataset: report.summary.attention.dataset_mean,
      peer: report.summary.attention.peer_mean,
    },
    {
      name: "Clarity",
      score: report.summary.clarity.score,
      dataset: report.summary.clarity.dataset_mean,
      peer: report.summary.clarity.peer_mean,
    },
    {
      name: "Memorability",
      score: report.summary.memorability.score,
      dataset: report.summary.memorability.dataset_mean,
      peer: report.summary.memorability.peer_mean,
    },
  ];

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <BarChart data={data} barGap={10}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(112, 98, 79, 0.16)" />
          <XAxis dataKey="name" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} domain={[0, 3]} />
          <Tooltip cursor={{ fill: "rgba(112, 98, 79, 0.08)" }} />
          <Legend />
          <Bar dataKey="score" fill="var(--chart-2)" radius={[8, 8, 0, 0]} />
          <Bar dataKey="dataset" fill="var(--chart-1)" radius={[8, 8, 0, 0]} />
          <Bar dataKey="peer" fill="var(--chart-3)" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
