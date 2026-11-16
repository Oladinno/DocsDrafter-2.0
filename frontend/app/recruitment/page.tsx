"use client";

import {
  ArrowRight,
  Briefcase,
  CheckCircle2,
  FileCheck,
  FileText,
  Mail,
  Plus,
  Search,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Candidate, CandidateApplication, JobPosting } from "@/lib/types";

const STAGES = [
  { key: "applied", label: "Applied" },
  { key: "screening", label: "Screening" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer Extended" },
  { key: "hired", label: "Hired" },
];

export default function RecruitmentPage() {
  const router = useRouter();
  const [jobs, setJobs] = React.useState<JobPosting[]>([]);
  const [candidates, setCandidates] = React.useState<Candidate[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedJob, setSelectedJob] = React.useState<string>("all");

  // Create Job Modal state
  const [showJobModal, setShowJobModal] = React.useState(false);
  const [jobTitle, setJobTitle] = React.useState("");
  const [jobLocation, setJobLocation] = React.useState("Remote");
  const [jobSalaryRange, setJobSalaryRange] = React.useState("$100k - $130k");
  const [jobDescription, setJobDescription] = React.useState("");

  // Offer Letter Generation Modal State
  const [offerCandidate, setOfferCandidate] = React.useState<Candidate | null>(null);
  const [offerSalary, setOfferSalary] = React.useState("115000");
  const [offerStartDate, setOfferStartDate] = React.useState("2026-12-01");
  const [offerGenerating, setOfferGenerating] = React.useState(false);

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [jobsRes, candRes] = await Promise.all([
        api.get<JobPosting[]>("/api/recruitment/jobs"),
        api.get<Candidate[]>("/api/recruitment/candidates"),
      ]);
      setJobs(jobsRes || []);
      setCandidates(candRes || []);
    } catch (err) {
      console.error("Failed to load recruitment data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/api/recruitment/jobs", {
        title: jobTitle,
        location: jobLocation,
        salaryRange: jobSalaryRange,
        description: jobDescription,
        status: "open",
      });
      setShowJobModal(false);
      setJobTitle("");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create job posting");
    }
  };

  const handleMoveStage = async (appId: string, newStage: string) => {
    try {
      await api.patch(`/api/recruitment/applications/${appId}/stage`, {
        stage: newStage,
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to advance candidate stage");
    }
  };

  const handleGenerateOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offerCandidate) return;
    try {
      setOfferGenerating(true);
      const currentApp = offerCandidate.applications[0];
      const jobTitleToUse = currentApp?.jobTitle || "Engineer";

      const doc = await api.post<any>("/api/recruitment/generate-offer-letter", {
        candidateId: offerCandidate.id,
        jobPostingId: currentApp?.jobPostingId || null,
        salary: Number(offerSalary),
        currency: "USD",
        startDate: offerStartDate,
        jobTitle: jobTitleToUse,
      });

      setOfferCandidate(null);
      // Navigate straight to the document in DocsDrafter editor!
      router.push(`/documents/${doc.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to generate offer letter");
      setOfferGenerating(false);
    }
  };

  return (
    <AppShell
      actions={
        <Button onClick={() => setShowJobModal(true)} className="gap-1.5 shadow-sm">
          <Plus size={15} /> Create Requisition
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Header Summary */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-xl font-bold text-ink">Recruitment & ATS</h1>
            <p className="text-sm text-muted">
              Manage candidate pipelines and issue DocsDrafter offer letters seamlessly.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted">Filter Opening:</span>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="h-9 rounded-lg border border-line bg-white px-3 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand/20"
            >
              <option value="all">All Openings ({jobs.length})</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* ATS Pipeline Kanban Board */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          {STAGES.map((col) => {
            const matchingCandidates = candidates.filter((c) =>
              c.applications.some(
                (a) =>
                  a.stage === col.key &&
                  (selectedJob === "all" || a.jobPostingId === selectedJob)
              )
            );

            return (
              <div
                key={col.key}
                className="flex flex-col rounded-xl border border-line bg-white/70 p-3 shadow-2xs"
              >
                <div className="flex items-center justify-between border-b border-line pb-2.5 mb-3">
                  <span className="font-display text-xs font-semibold uppercase tracking-wider text-muted">
                    {col.label}
                  </span>
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-canvas text-xs font-semibold text-ink">
                    {matchingCandidates.length}
                  </span>
                </div>

                <div className="flex-1 space-y-3">
                  {matchingCandidates.map((c) => {
                    const currentApp = c.applications.find(
                      (a) =>
                        a.stage === col.key &&
                        (selectedJob === "all" || a.jobPostingId === selectedJob)
                    );
                    if (!currentApp) return null;

                    return (
                      <div
                        key={c.id}
                        className="rounded-lg border border-line bg-white p-3.5 shadow-xs transition-shadow hover:shadow-sm"
                      >
                        <div className="font-semibold text-sm text-ink">
                          {c.firstName} {c.lastName}
                        </div>
                        <div className="text-xs text-muted mt-0.5">{currentApp.jobTitle || "Open Role"}</div>
                        <div className="text-xs text-subtle mt-1">{c.email}</div>

                        {/* DocsDrafter Offer Letter Badge / Button */}
                        {currentApp.offerDocumentId ? (
                          <div className="mt-3">
                            <Link
                              href={`/documents/${currentApp.offerDocumentId}`}
                              className="inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-emerald-50 border border-emerald-200 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 transition-colors"
                            >
                              <FileCheck size={13} /> View Offer Letter
                            </Link>
                          </div>
                        ) : (
                          <div className="mt-3">
                            <button
                              type="button"
                              onClick={() => setOfferCandidate(c)}
                              className="inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-lavender border border-brand/20 px-2.5 py-1 text-xs font-medium text-brand hover:bg-lavender/80 transition-colors"
                            >
                              <Sparkles size={13} /> Draft Offer Letter
                            </button>
                          </div>
                        )}

                        {/* Stage Progression Action */}
                        <div className="mt-3 flex items-center justify-between border-t border-line/60 pt-2 text-[11px] text-muted">
                          <span>Stage:</span>
                          <select
                            value={currentApp.stage}
                            onChange={(e) => handleMoveStage(currentApp.id, e.target.value)}
                            className="rounded border border-line bg-canvas px-1.5 py-0.5 text-xs text-ink focus:outline-none"
                          >
                            {STAGES.map((s) => (
                              <option key={s.key} value={s.key}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Offer Letter Generation Modal */}
      {offerCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-2xl border border-line bg-white p-6 shadow-xl">
            <div className="flex items-center gap-2 text-brand">
              <Sparkles size={18} />
              <h2 className="text-lg font-semibold text-ink">Generate Offer Letter</h2>
            </div>
            <p className="mt-1 text-sm text-muted">
              Auto-generate an employment agreement for{" "}
              <strong className="text-ink">{offerCandidate.firstName} {offerCandidate.lastName}</strong>{" "}
              using the DocsDrafter engine.
            </p>

            <form onSubmit={handleGenerateOffer} className="mt-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-ink">Annual Base Salary (USD)</label>
                <input
                  required
                  type="number"
                  value={offerSalary}
                  onChange={(e) => setOfferSalary(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="120000"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-ink">Target Start Date</label>
                <input
                  required
                  type="date"
                  value={offerStartDate}
                  onChange={(e) => setOfferStartDate(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                />
              </div>

              <div className="rounded-lg bg-canvas p-3 text-xs text-muted">
                💡 This automatically populates the standard Offer Letter template and links it to this candidate's personnel file.
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setOfferCandidate(null)}
                  disabled={offerGenerating}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={offerGenerating} className="gap-1.5">
                  {offerGenerating ? "Drafting..." : "Generate & Open in Editor"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Requisition Modal */}
      {showJobModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-2xl border border-line bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-ink">New Job Requisition</h2>
            <form onSubmit={handleCreateJob} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-ink">Job Title</label>
                <input
                  required
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="Senior Product Designer"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink">Location</label>
                <input
                  required
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="Remote / New York, NY"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink">Salary Range</label>
                <input
                  value={jobSalaryRange}
                  onChange={(e) => setJobSalaryRange(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="$110,000 - $140,000"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink">Brief Description</label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-line p-2 text-sm focus:border-brand focus:outline-none"
                  placeholder="Key responsibilities and qualifications..."
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowJobModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">Publish Job</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
