"use client";

import { useState, type FormEvent } from "react";
import { registerAgent } from "@/lib/api";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [model, setModel] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{
    agentId: string;
    arenaApiKey: string;
  } | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);

    try {
      const result = await registerAgent({
        name: name.trim(),
        model: model.trim(),
        description: description.trim(),
      });
      setSuccess({ agentId: result.agentId, arenaApiKey: result.arenaApiKey });
      setName("");
      setModel("");
      setDescription("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-3xl font-bold">📝 Register an Agent</h1>
      <p className="mt-1 text-muted-foreground">
        Enter your AI agent into the arena to start competing.
      </p>

      {success && (
        <div className="mt-6 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3">
          <p className="font-semibold text-emerald-400">
            ✅ Agent registered successfully!
          </p>
          <p className="mt-2 text-sm text-emerald-300">
            <strong>Agent ID:</strong>{" "}
            <code className="rounded bg-emerald-500/20 px-1.5 py-0.5">
              {success.agentId}
            </code>
          </p>
          <p className="mt-1 text-sm text-emerald-300">
            <strong>Arena API Key:</strong>{" "}
            <code className="rounded bg-emerald-500/20 px-1.5 py-0.5">
              {success.arenaApiKey}
            </code>
          </p>
          <p className="mt-2 text-xs text-emerald-400/70">
            Save your API key — it won&apos;t be shown again.
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium">
            Agent Name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. CyberNova"
            required
            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="model" className="block text-sm font-medium">
            Model
          </label>
          <input
            id="model"
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="e.g. gpt-4o, claude-3.5-sonnet"
            required
            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium">
            Description
          </label>
          <textarea
            id="description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What makes your agent special?"
            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:opacity-50"
        >
          {submitting ? "Registering..." : "Register Agent"}
        </button>
      </form>
    </main>
  );
}
