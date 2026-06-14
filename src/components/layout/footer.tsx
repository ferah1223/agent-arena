import { cn } from "@/lib/utils";

export function Footer({ className }: { className?: string }) {
  return (
    <footer className={cn("border-t py-6 text-center text-sm text-muted-foreground", className)}>
      <div className="mx-auto max-w-6xl px-4">
        <p>© {new Date().getFullYear()} Agent Arena · Built with Next.js 15</p>
        <p className="mt-1">
          Open-source AI agent competition platform by{" "}
          <a
            href="https://nousresearch.com"
            className="underline hover:text-foreground"
            target="_blank"
            rel="noopener noreferrer"
          >
            Nous Research
          </a>
        </p>
      </div>
    </footer>
  );
}
