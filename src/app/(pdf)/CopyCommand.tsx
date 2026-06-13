"use client";

import { useState } from "react";

export function CopyCommand({
  command,
  children,
  label = "copy",
}: {
  command: string;
  children: React.ReactNode;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <span className="cmd-block" data-cmd>
      <span className="cmd-lines">{children}</span>
      <button
        className={`copy ${copied ? "copied" : ""}`}
        type="button"
        onClick={copy}
        aria-label={`Copy: ${label}`}
      >
        {copied ? "copied" : "copy"}
      </button>
    </span>
  );
}
