"use client";

import {
  Building2,
  FileText,
  Mail,
  MoreVertical,
  Plus,
  Search,
  Shield,
  UserCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Department, Employee } from "@/lib/types";

export default function EmployeesPage() {
  const [employees, setEmployees] = React.useState<Employee[]>([]);
  const [departments, setDepartments] = React.useState<Department[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [selectedDept, setSelectedDept] = React.useState<string>("all");
  const [showCreateModal, setShowCreateModal] = React.useState(false);

  // New employee form state
  const [newFirstName, setNewFirstName] = React.useState("");
  const [newLastName, setNewLastName] = React.useState("");
  const [newEmail, setNewEmail] = React.useState("");
  const [newJobTitle, setNewJobTitle] = React.useState("");
  const [newDeptId, setNewDeptId] = React.useState("");
  const [newSalary, setNewSalary] = React.useState("95000");

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [empRes, deptRes] = await Promise.all([
        api.get<{ items: Employee[]; total: number }>("/api/employees"),
        api.get<Department[]>("/api/departments"),
      ]);
      setEmployees(empRes.items || []);
      setDepartments(deptRes || []);
    } catch (err) {
      console.error("Failed to load employees:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const code = `EMP-${Math.floor(100 + Math.random() * 900)}`;
      await api.post("/api/employees", {
        employeeCode: code,
        firstName: newFirstName,
        lastName: newLastName,
        email: newEmail,
        jobTitle: newJobTitle,
        departmentId: newDeptId || null,
        salary: Number(newSalary) || null,
        employmentStatus: "active",
        employmentType: "full_time",
      });
      setShowCreateModal(false);
      setNewFirstName("");
      setNewLastName("");
      setNewEmail("");
      setNewJobTitle("");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create employee");
    }
  };

  const filtered = employees.filter((emp) => {
    const matchesSearch =
      !search ||
      `${emp.firstName} ${emp.lastName}`.toLowerCase().includes(search.toLowerCase()) ||
      emp.email.toLowerCase().includes(search.toLowerCase()) ||
      emp.jobTitle.toLowerCase().includes(search.toLowerCase()) ||
      emp.employeeCode.toLowerCase().includes(search.toLowerCase());

    const matchesDept = selectedDept === "all" || emp.departmentId === selectedDept;
    return matchesSearch && matchesDept;
  });

  return (
    <AppShell
      actions={
        <Button onClick={() => setShowCreateModal(true)} className="gap-1.5 shadow-sm">
          <Plus size={15} /> Add Employee
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Header summary stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-line bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted">Total Employees</span>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-lavender text-brand">
                <Users size={16} />
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
              {employees.length}
            </div>
          </div>

          <div className="rounded-xl border border-line bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted">Departments</span>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                <Building2 size={16} />
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
              {departments.length}
            </div>
          </div>

          <div className="rounded-xl border border-line bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted">Active Onboarding</span>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
                <UserCheck size={16} />
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-ink">
              {employees.filter((e) => e.employmentStatus === "onboarding").length}
            </div>
          </div>
        </div>

        {/* Filters and search bar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-md">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-subtle pointer-events-none"
            />
            <input
              type="text"
              placeholder="Search by name, email, or role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-line bg-white pl-9 pr-3 text-sm text-ink placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="h-9 rounded-lg border border-line bg-white px-3 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand/20"
            >
              <option value="all">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Employee Directory Table */}
        <div className="overflow-hidden rounded-xl border border-line bg-white shadow-xs">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-canvas/50 text-xs font-semibold uppercase tracking-wider text-muted">
              <tr>
                <th className="px-6 py-3.5">Employee</th>
                <th className="px-6 py-3.5">Title & Dept</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Personnel Docs</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted">
                    Loading employee directory...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted">
                    No employees found. Add your first employee to get started.
                  </td>
                </tr>
              ) : (
                filtered.map((emp) => (
                  <tr key={emp.id} className="hover:bg-canvas/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-lavender font-display text-sm font-semibold text-brand">
                          {emp.firstName[0]}
                          {emp.lastName[0]}
                        </div>
                        <div>
                          <div className="font-medium text-ink">
                            {emp.firstName} {emp.lastName}
                          </div>
                          <div className="text-xs text-subtle flex items-center gap-1.5">
                            <span className="font-mono">{emp.employeeCode}</span>
                            <span>•</span>
                            <span>{emp.email}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-ink">{emp.jobTitle}</div>
                      <div className="text-xs text-muted">{emp.departmentName || "No Department"}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 capitalize border border-emerald-200">
                        {emp.employmentStatus}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/dashboard?employeeId=${emp.id}`}
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-brand hover:underline"
                      >
                        <FileText size={13} /> View Documents
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/templates?employeeId=${emp.id}`}
                        className="inline-flex items-center gap-1 rounded-md border border-line px-2.5 py-1 text-xs font-medium text-ink hover:bg-canvas"
                      >
                        Draft Contract
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Employee Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-line bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-ink">Add New Employee</h2>
            <p className="mt-1 text-sm text-muted">
              Create an employee profile to link contracts, agreements, and track employment.
            </p>

            <form onSubmit={handleCreate} className="mt-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-ink">First Name</label>
                  <input
                    required
                    value={newFirstName}
                    onChange={(e) => setNewFirstName(e.target.value)}
                    className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                    placeholder="Jane"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-ink">Last Name</label>
                  <input
                    required
                    value={newLastName}
                    onChange={(e) => setNewLastName(e.target.value)}
                    className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-ink">Work Email</label>
                <input
                  required
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="jane.doe@company.com"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-ink">Job Title</label>
                  <input
                    required
                    value={newJobTitle}
                    onChange={(e) => setNewJobTitle(e.target.value)}
                    className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                    placeholder="Product Manager"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-ink">Department</label>
                  <select
                    value={newDeptId}
                    onChange={(e) => setNewDeptId(e.target.value)}
                    className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  >
                    <option value="">Select Department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-ink">Annual Base Salary (USD)</label>
                <input
                  type="number"
                  value={newSalary}
                  onChange={(e) => setNewSalary(e.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-line px-3 text-sm focus:border-brand focus:outline-none"
                  placeholder="100000"
                />
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">Create Employee</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
