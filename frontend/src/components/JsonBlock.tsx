type JsonBlockProps = {
  value: unknown;
};

export default function JsonBlock({ value }: JsonBlockProps) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return <pre className="json-block">{text}</pre>;
}

