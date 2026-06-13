"use client";

import { useState } from "react";

function useCopied() {
  const [copied, setCopied] = useState(false);

  function flash() {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return { copied, flash };
}

export function CopyCommand({
  command,
  children,
  label = "copy",
}: {
  command: string;
  children?: React.ReactNode;
  label?: string;
}) {
  const { copied, flash } = useCopied();

  async function copy() {
    await navigator.clipboard.writeText(command);
    flash();
  }

  return (
    <span className="cmd-block" data-cmd>
      <span className="cmd-lines">
        {children ??
          command.split("\n").map((line, index) => (
            <span className="cmd-line" key={`${index}-${line}`}>
              {line}
            </span>
          ))}
      </span>
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

export function CopyTextButton({
  text,
  children,
  label = "copy",
}: {
  text: string;
  children: React.ReactNode;
  label?: string;
}) {
  const { copied, flash } = useCopied();

  async function copy() {
    await navigator.clipboard.writeText(text);
    flash();
  }

  return (
    <button
      className={`copy-inline ${copied ? "copied" : ""}`}
      type="button"
      onClick={copy}
      aria-label={`Copy: ${label}`}
    >
      {copied ? "copied" : children}
    </button>
  );
}

export function CopyFileButton({
  path,
  children,
  label = "copy file",
}: {
  path: string;
  children: React.ReactNode;
  label?: string;
}) {
  const { copied, flash } = useCopied();

  async function copy() {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Could not fetch ${path}`);
    }
    await navigator.clipboard.writeText(await response.text());
    flash();
  }

  return (
    <button
      className={`copy-inline ${copied ? "copied" : ""}`}
      type="button"
      onClick={copy}
      aria-label={`Copy: ${label}`}
    >
      {copied ? "copied" : children}
    </button>
  );
}
