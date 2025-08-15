"use client";

import React from "react";

type OverlayLoadingProps = {
  visible: boolean;
  title?: string;
  description?: string;
};

export function OverlayLoading({
  visible,
  title = "연결중",
  description = "백엔드와 연결하고 있어요...",
}: OverlayLoadingProps) {
  if (!visible) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-[90%] max-w-sm rounded-2xl bg-white p-6 text-center shadow-2xl dark:bg-neutral-900">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-primary/30 border-t-primary" />
        <div className="text-lg font-semibold text-foreground">{title}</div>
        <div className="mt-1 text-sm text-muted-foreground">{description}</div>
      </div>
    </div>
  );
}


