import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json(
    {
      error: "agent_sidecar_retired",
      message:
        "GenUI no longer runs a LangGraph concierge/chat sidecar. Team agents call the cert-auth server directly: POST /v1/search, POST /v1/artifacts, POST /v1/present.",
    },
    { status: 410 },
  );
}
