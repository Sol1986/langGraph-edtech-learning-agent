"use client";

import { useMemo } from "react";

import { HttpAgent } from "@ag-ui/client";
import { CopilotKit } from "@copilotkit/react-core";

// server.py's `/copilotkit` route (mounted via ag_ui_langgraph's
// add_langgraph_fastapi_endpoint) speaks raw AG-UI: POST a RunAgentInput,
// get back a stream of AG-UI events. @ag-ui/client's HttpAgent talks exactly
// that protocol, so we hand it to CopilotKit directly rather than pointing
// `runtimeUrl` at it -- `runtimeUrl` expects a Node-side CopilotKit Runtime
// (a different, JSON-RPC-style "/info" discovery protocol our FastAPI
// backend doesn't implement), which caused a 422 on every page load.
const AGENT_URL =
  process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL ?? "http://127.0.0.1:8000/copilotkit";

export function CopilotProvider({ children }: { children: React.ReactNode }) {
  const agents = useMemo(() => ({ quiz_agent: new HttpAgent({ url: AGENT_URL }) }), []);

  return (
    <CopilotKit agentId="quiz_agent" agents__unsafe_dev_only={agents}>
      {children}
    </CopilotKit>
  );
}
