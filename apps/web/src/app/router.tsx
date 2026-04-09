import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { ProtectedRoute } from "@/lib/auth";

const AppShell = lazy(() => import("@/components/app-shell").then((module) => ({ default: module.AppShell })));
const DashboardPage = lazy(() => import("@/pages/dashboard-page").then((module) => ({ default: module.DashboardPage })));
const JobProgressPage = lazy(() => import("@/pages/job-progress-page").then((module) => ({ default: module.JobProgressPage })));
const LandingPage = lazy(() => import("@/pages/landing-page").then((module) => ({ default: module.LandingPage })));
const LibraryPage = lazy(() => import("@/pages/library-page").then((module) => ({ default: module.LibraryPage })));
const NewAnalysisPage = lazy(() => import("@/pages/new-analysis-page").then((module) => ({ default: module.NewAnalysisPage })));
const ReportPage = lazy(() => import("@/pages/report-page").then((module) => ({ default: module.ReportPage })));
const SignInPage = lazy(() => import("@/pages/sign-in-page").then((module) => ({ default: module.SignInPage })));

function withSuspense(node: ReactNode) {
  return <Suspense fallback={<div className="py-14 text-center text-muted-foreground">Loading...</div>}>{node}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: withSuspense(<LandingPage />),
  },
  {
    path: "/sign-in",
    element: withSuspense(<SignInPage />),
  },
  {
    path: "/app",
    element: (
      <ProtectedRoute>
        {withSuspense(<AppShell />)}
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: withSuspense(<DashboardPage />) },
      { path: "new", element: withSuspense(<NewAnalysisPage />) },
      { path: "jobs/:jobId", element: withSuspense(<JobProgressPage />) },
      { path: "jobs/:jobId/report", element: withSuspense(<ReportPage />) },
      { path: "library", element: withSuspense(<LibraryPage />) },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
