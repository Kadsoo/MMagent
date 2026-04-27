import { Fragment, ReactNode } from "react";

type MarkdownMessageProps = {
  text: string;
};

export default function MarkdownMessage({ text }: MarkdownMessageProps) {
  const normalized = text.replace(/\\n/g, "\n");
  const blocks = normalized.split(/\n{2,}/).map((block) => block.trim()).filter(Boolean);

  return (
    <div className="markdown-message">
      {blocks.map((block, index) => (
        <Fragment key={`${index}-${block.slice(0, 18)}`}>
          {renderBlock(block, index)}
        </Fragment>
      ))}
    </div>
  );
}

function renderBlock(block: string, index: number) {
  if (block.startsWith("### ")) {
    return <h4>{renderInline(block.slice(4))}</h4>;
  }
  if (block.startsWith("## ")) {
    return <h3>{renderInline(block.slice(3))}</h3>;
  }
  if (block.startsWith("# ")) {
    return <h3>{renderInline(block.slice(2))}</h3>;
  }

  const lines = block.split("\n");
  if (lines.every((line) => /^[-*]\s+/.test(line.trim()))) {
    return (
      <ul>
        {lines.map((line, lineIndex) => (
          <li key={`${index}-${lineIndex}`}>{renderInline(line.trim().replace(/^[-*]\s+/, ""))}</li>
        ))}
      </ul>
    );
  }

  if (lines.every((line) => /^\d+\.\s+/.test(line.trim()))) {
    return (
      <ol>
        {lines.map((line, lineIndex) => (
          <li key={`${index}-${lineIndex}`}>{renderInline(line.trim().replace(/^\d+\.\s+/, ""))}</li>
        ))}
      </ol>
    );
  }

  return (
    <p>
      {lines.map((line, lineIndex) => (
        <Fragment key={`${index}-${lineIndex}`}>
          {lineIndex > 0 ? <br /> : null}
          {renderInline(line)}
        </Fragment>
      ))}
    </p>
  );
}

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}
