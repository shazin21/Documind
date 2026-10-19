import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "success"
    | "warning"
    | "destructive"
    | "secondary"
    | "outline"
    | "indigo";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  children,
  ...props
}) => {
  const variants = {
    default: "bg-zinc-800 text-zinc-200 border-zinc-700",
    secondary: "bg-zinc-900/80 text-zinc-400 border-zinc-800",
    success: "bg-emerald-950/60 text-emerald-300 border-emerald-800/60",
    warning: "bg-amber-950/60 text-amber-300 border-amber-800/60",
    destructive: "bg-rose-950/60 text-rose-300 border-rose-800/60",
    indigo: "bg-indigo-950/60 text-indigo-300 border-indigo-800/60",
    outline: "bg-transparent text-zinc-300 border-zinc-700",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
