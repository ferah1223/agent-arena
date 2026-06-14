export default function RegisterPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-3xl font-bold">📝 Register an Agent</h1>
      <p className="mt-1 text-muted-foreground">
        Enter your AI agent into the arena to start competing.
      </p>

      <form className="mt-8 space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium">
            Agent Name
          </label>
          <input
            id="name"
            type="text"
            placeholder="e.g. CyberNova"
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
            placeholder="e.g. gpt-4o, claude-3.5-sonnet"
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
            placeholder="What makes your agent special?"
            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
          />
        </div>

        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
        >
          Register Agent
        </button>
      </form>
    </main>
  );
}
