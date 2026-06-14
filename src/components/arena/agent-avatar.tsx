import { cn } from "@/lib/utils";

interface AgentAvatarProps {
  avatar: string;
  name: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "h-8 w-8 text-lg",
  md: "h-12 w-12 text-2xl",
  lg: "h-16 w-16 text-3xl",
};

export function AgentAvatar({
  avatar,
  name,
  size = "md",
  className,
}: AgentAvatarProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-muted border",
        sizeClasses[size],
        className,
      )}
      title={name}
      aria-label={name}
    >
      <span role="img">{avatar}</span>
    </div>
  );
}
