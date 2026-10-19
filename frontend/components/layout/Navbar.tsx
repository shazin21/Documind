"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  MessageSquare,
  Layers,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { HealthResponse } from "@/types";
import { cn } from "@/lib/utils";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await api.getHealth();
        if (mounted) setHealth(res);
      } catch {
        if (mounted) setHealth(null);
      } finally {
        if (mounted) setIsChecking(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const navLinks = [
    { href: "/", label: "Dashboard", icon: Layers },
    { href: "/documents", label: "Documents", icon: FileText },
    { href: "/chat", label: "Chat & Q&A", icon: MessageSquare },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
              DocuMind AI
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] font-semibold uppercase tracking-wider text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded-full border border-indigo-800/60">
              RAG Engine
            </span>
          </div>
        </Link>

        {/* Navigation links */}
        <nav className="flex items-center gap-1 sm:gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-zinc-800/90 text-white shadow-sm border border-zinc-700/60"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-indigo-400" : "text-zinc-400")} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* System Health Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-zinc-900 border-zinc-800">
            {isChecking ? (
              <>
                <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-zinc-400 hidden sm:inline">Connecting</span>
              </>
            ) : health ? (
              <>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-400 font-medium">Backend Ready</span>
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-rose-400" />
                <span className="text-rose-400 font-medium">Offline</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
