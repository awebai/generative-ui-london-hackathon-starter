import { CopyCommand } from "./CopyCommand";

const GENUI_ORIGIN = "https://genui.ai";

export default function Home() {
  return (
    <main>
      <h1 className="page-title">genui — agent-first generative UI</h1>
      <p className="lede">
        Humans bring their own agents. Agents use BYOT certificates to co-author
        shared text, turn a document into A2UI, and hand the human one safe
        presentation link. No app account. No chat box pretending to be the
        product.
      </p>

      <section className="terminal" aria-label="Getting started">
        <div className="terminal-frame">
          <div className="terminal-bar">
            <span>getting started</span>
            <span>copy one command at a time</span>
          </div>
          <pre>
            <code>
              <span className="comment">
                # two team agents write the source text. the certificate is the login.
              </span>
              <CopyCommand
                label="set genui origin"
                command={`export GENUI_ORIGIN=${GENUI_ORIGIN}`}
              >
                <span className="cmd-line">export GENUI_ORIGIN={GENUI_ORIGIN}</span>
              </CopyCommand>
              <CopyCommand
                label="agent a creates a document"
                command={`aw id request POST "$GENUI_ORIGIN/v1/documents" --team-auth --raw \
  --body '{"slug":"agentic-research-memo","title":"Agentic UI research memo","body":"Agent A draft: live web research plus declarative A2UI should produce cited, shareable surfaces."}'`}
              >
                <span className="cmd-line">aw id request POST "$GENUI_ORIGIN/v1/documents" --team-auth --raw \</span>
                <span className="cmd-line">  --body '{'{"slug":"agentic-research-memo","title":"Agentic UI research memo","body":"Agent A draft: live web research plus declarative A2UI should produce cited, shareable surfaces."}'}</span>
              </CopyCommand>
              <CopyCommand
                label="agent b appends a version"
                command={`aw id request POST "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw \
  --body 'Agent B revision: add source-backed validation and mint a no-login /present link for the human.'`}
              >
                <span className="cmd-line">aw id request POST "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw \</span>
                <span className="cmd-line">  --body 'Agent B revision: add source-backed validation and mint a no-login /present link for the human.'</span>
              </CopyCommand>
              <CopyCommand
                label="show version attribution"
                command={`aw id request GET "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw`}
              >
                <span className="cmd-line">aw id request GET "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw</span>
              </CopyCommand>

              <span className="comment">
                # an agent formats the doc as A2UI and stores it as an artifact.
              </span>
              <CopyCommand
                label="create a2ui artifact"
                command={`aw id request POST "$GENUI_ORIGIN/v1/artifacts" --team-auth --raw \
  --body '{"slug":"agentic-research-surface","a2ui":{"a2ui_operations":[{"version":"v0.9","createSurface":{"surfaceId":"doc","catalogId":"https://cpk-a2ui.local/catalogs/copilotkit/v1"}},{"version":"v0.9","updateComponents":{"surfaceId":"doc","components":[{"id":"root","component":"Stack","children":["card"],"gap":"lg"},{"id":"card","component":"Card","tone":"lilac","child":"brief"},{"id":"brief","component":"Markdown","text":"# Agentic UI research memo\\n\\n**Agent A** drafted the memo. **Agent B** appended a sourced validation request. The human gets this renderer-safe A2UI document by link."}]}},{"version":"v0.9","updateDataModel":{"surfaceId":"doc","path":"/","value":{"slug":"agentic-research-memo"}}}]}}'`}
              >
                <span className="cmd-line">aw id request POST "$GENUI_ORIGIN/v1/artifacts" --team-auth --raw \</span>
                <span className="cmd-line">  --body '{'{"slug":"agentic-research-surface","a2ui":{"a2ui_operations":[...]}}'}</span>
              </CopyCommand>
              <CopyCommand
                label="mint present link"
                command={`aw id request POST "$GENUI_ORIGIN/v1/present" --team-auth --raw \
  --body '{"artifact_id":"<artifact_id from previous response>","version":1}'`}
              >
                <span className="cmd-line">aw id request POST "$GENUI_ORIGIN/v1/present" --team-auth --raw \</span>
                <span className="cmd-line">  --body '{'{"artifact_id":"<artifact_id from previous response>","version":1}'}</span>
              </CopyCommand>

              <span className="comment">
                # now the only human web UI: open the token. possession is access.
              </span>
              <CopyCommand
                label="open present url"
                command="open http://127.0.0.1:3000/present/<token>"
              >
                <span className="cmd-line">open http://127.0.0.1:3000/present/&lt;token&gt;</span>
              </CopyCommand>
            </code>
          </pre>
        </div>
      </section>

      <p className="footnote">
        Quirk, not gimmick: the browser is the last mile, not the workspace.
        GenUI stores server-readable text and A2UI artifacts scoped to the
        verified team; the human only sees the document-shaped presentation the
        agents chose to mint.
      </p>
    </main>
  );
}
