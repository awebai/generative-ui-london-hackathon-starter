"use client";

import { useEffect, useMemo, useState } from "react";
import {
  A2UIProvider,
  A2UIRenderer,
  useA2UIActions,
} from "@copilotkit/a2ui-renderer";
import { catalog } from "@/a2ui/catalog";
import { extractSurfaceId, type A2UIEnvelope } from "@/types/a2ui";

type A2UIOp = Record<string, unknown>;

export function PresentSurface({ operations }: { operations: A2UIOp[] }) {
  return (
    <A2UIProvider catalog={catalog}>
      <PresentSurfaceInner operations={operations} />
    </A2UIProvider>
  );
}

function PresentSurfaceInner({ operations }: { operations: A2UIOp[] }) {
  const actions = useA2UIActions();
  const [error, setError] = useState<string | null>(null);
  const surfaceId = useMemo(() => findSurfaceId(operations), [operations]);

  useEffect(() => {
    setError(null);
    try {
      actions.processMessages(operations);
    } catch (err) {
      console.warn("[present] failed to process A2UI operations", err);
      setError("This presentation could not be rendered.");
    }
  }, [actions, operations]);

  if (!surfaceId) {
    return <EmptyPresentSurface message="This presentation is empty." />;
  }
  if (error) {
    return <EmptyPresentSurface message={error} />;
  }

  return <A2UIRenderer surfaceId={surfaceId} />;
}

function EmptyPresentSurface({ message }: { message: string }) {
  return (
    <div className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center text-[var(--muted)]">
      {message}
    </div>
  );
}

function findSurfaceId(operations: A2UIOp[]): string | null {
  for (const op of operations) {
    const surfaceId = extractSurfaceId(op as A2UIEnvelope);
    if (surfaceId) return surfaceId;
  }
  return null;
}
