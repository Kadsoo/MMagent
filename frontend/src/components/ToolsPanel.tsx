import type { ToolSpec } from "../types/api";
import JsonBlock from "./JsonBlock";

type ToolsPanelProps = {
  tools: ToolSpec[];
  loading: boolean;
  error: string | null;
};

export default function ToolsPanel({ tools, loading, error }: ToolsPanelProps) {
  return (
    <section className="panel tools-panel">
      <div className="panel-heading">
        <div>
          <h2>Registered Tools</h2>
          <p className="panel-subtitle">
            Tool registration is now separated from the chat homepage for a cleaner app layout.
          </p>
        </div>
        <span>{loading ? "loading" : `${tools.length} tools`}</span>
      </div>

      {error ? <p className="error-line">{error}</p> : null}

      <div className="tool-list">
        {tools.map((tool) => (
          <article className="tool-item" key={tool.name}>
            <div>
              <h3>{tool.name}</h3>
              <p>{tool.description}</p>
            </div>
            <details>
              <summary>Input schema</summary>
              <JsonBlock value={tool.input_schema} />
            </details>
          </article>
        ))}
      </div>
    </section>
  );
}
