import type { TraceStep } from "../types/api";
import JsonBlock from "./JsonBlock";

type TracePanelProps = {
  trace: TraceStep[];
  title?: string;
};

export default function TracePanel({ trace, title }: TracePanelProps) {
  return (
    <section className="panel trace-panel">
      <div className="panel-heading">
        <div>
          <h2>Execution Trace</h2>
          {title ? <p className="panel-subtitle">{title}</p> : null}
        </div>
        <span>{trace.length} steps</span>
      </div>

      {trace.length === 0 ? (
        <p className="muted">Trace will appear after the first request.</p>
      ) : (
        <div className="timeline">
          {trace.map((step) => (
            <article className="trace-step" key={step.step}>
              <div className="step-title">
                <span>Step {step.step}</span>
                <strong>{labelForStep(step)}</strong>
              </div>

              {step.model_output ? (
                <details open>
                  <summary>Model output</summary>
                  <JsonBlock value={tryParseJson(step.model_output)} />
                </details>
              ) : null}

              {step.tool_call ? (
                <details open>
                  <summary>JSON tool call</summary>
                  <JsonBlock value={step.tool_call} />
                </details>
              ) : null}

              {step.tool_result ? (
                <details open>
                  <summary>Tool result</summary>
                  <JsonBlock value={step.tool_result} />
                </details>
              ) : null}

              {step.final_answer ? (
                <div className="final-answer">
                  <span>Final answer</span>
                  <p>{step.final_answer.answer}</p>
                </div>
              ) : null}

              {step.error ? <p className="error-line">{step.error}</p> : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function labelForStep(step: TraceStep) {
  if (step.final_answer) {
    return "final";
  }
  if (step.tool_call) {
    return step.tool_call.tool_name;
  }
  if (step.error) {
    return "error";
  }
  return "reasoning";
}

function tryParseJson(value: string) {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}
