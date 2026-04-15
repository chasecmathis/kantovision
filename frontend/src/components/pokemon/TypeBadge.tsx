import { cn } from "@/src/lib/utils";
import { TYPE_COLORS } from "@/src/lib/typeColors";

interface TypeBadgeProps {
  type: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function TypeBadge({ type, size = "md", className }: TypeBadgeProps) {
  const color = TYPE_COLORS[type] ?? "#9CA3AF";

  return (
    <span
      className={cn(
        "type-badge",
        size === "sm" && "px-2 py-0.5 text-[9px]",
        size === "md" && "px-3 py-1 text-[10px]",
        size === "lg" && "px-4 py-1.5 text-xs",
        className
      )}
      style={{
        color,
        borderColor: `${color}40`,
        backgroundColor: `${color}15`,
        fontFamily: "var(--font-unbounded)",
      }}
    >
      {type.toUpperCase()}
    </span>
  );
}
