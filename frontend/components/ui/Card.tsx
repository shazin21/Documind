import React from "react";
import { cn } from "@/lib/utils";

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-zinc-800 bg-zinc-900/60 backdrop-blur-sm p-6 text-zinc-100 shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div className={cn("flex flex-col space-y-1.5 pb-4", className)} {...props}>
      {children}
    </div>
  );
};

export const CardTitle: React.FC<
  React.HTMLAttributes<HTMLHeadingElement>
> = ({ className, children, ...props }) => {
  return (
    <h3
      className={cn(
        "text-lg font-semibold leading-none tracking-tight text-zinc-100",
        className
      )}
      {...props}
    >
      {children}
    </h3>
  );
};

export const CardDescription: React.FC<
  React.HTMLAttributes<HTMLParagraphElement>
> = ({ className, children, ...props }) => {
  return (
    <p className={cn("text-sm text-zinc-400 leading-relaxed", className)} {...props}>
      {children}
    </p>
  );
};

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => {
  return <div className={cn("pt-0", className)} {...props}>{children}</div>;
};
