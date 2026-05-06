const inlinePatterns = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;

function renderInline(text) {
  return text.split(inlinePatterns).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }

    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }

    return <span key={index}>{part}</span>;
  });
}

function flushList(blocks, listItems, ordered) {
  if (listItems.length === 0) return;

  const Tag = ordered ? "ol" : "ul";
  blocks.push(
    <Tag key={`list-${blocks.length}`}>
      {listItems.map((item, index) => (
        <li key={index}>{renderInline(item)}</li>
      ))}
    </Tag>,
  );
}

function isTableSeparator(line) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());
}

function parseTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

export default function MarkdownMessage({ text }) {
  const blocks = [];
  const lines = text.split(/\r?\n/);
  let listItems = [];
  let orderedList = false;
  let codeLines = [];
  let inCodeBlock = false;
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        blocks.push(
          <pre key={`code-${blocks.length}`}>
            <code>{codeLines.join("\n")}</code>
          </pre>,
        );
        codeLines = [];
        inCodeBlock = false;
      } else {
        flushList(blocks, listItems, orderedList);
        listItems = [];
        inCodeBlock = true;
      }
      index += 1;
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      index += 1;
      continue;
    }

    if (!trimmed) {
      flushList(blocks, listItems, orderedList);
      listItems = [];
      index += 1;
      continue;
    }

    if (trimmed.includes("|") && lines[index + 1] && isTableSeparator(lines[index + 1])) {
      flushList(blocks, listItems, orderedList);
      listItems = [];

      const headers = parseTableRow(trimmed);
      const rows = [];
      index += 2;

      while (index < lines.length && lines[index].trim().includes("|") && lines[index].trim()) {
        rows.push(parseTableRow(lines[index]));
        index += 1;
      }

      blocks.push(
        <div className="markdown-table-wrap" key={`table-${blocks.length}`}>
          <table>
            <thead>
              <tr>
                {headers.map((header, headerIndex) => (
                  <th key={headerIndex}>{renderInline(header)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {headers.map((_, cellIndex) => (
                    <td key={cellIndex}>{renderInline(row[cellIndex] || "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      flushList(blocks, listItems, orderedList);
      listItems = [];
      const HeadingTag = `h${headingMatch[1].length + 2}`;
      blocks.push(<HeadingTag key={`heading-${index}`}>{renderInline(headingMatch[2])}</HeadingTag>);
      index += 1;
      continue;
    }

    const unorderedMatch = trimmed.match(/^[-*]\s+(.+)$/);
    const orderedMatch = trimmed.match(/^\d+\.\s+(.+)$/);

    if (unorderedMatch || orderedMatch) {
      const nextOrdered = Boolean(orderedMatch);
      if (listItems.length > 0 && orderedList !== nextOrdered) {
        flushList(blocks, listItems, orderedList);
        listItems = [];
      }

      orderedList = nextOrdered;
      listItems.push((orderedMatch || unorderedMatch)[1]);
      index += 1;
      continue;
    }

    flushList(blocks, listItems, orderedList);
    listItems = [];
    blocks.push(<p key={`paragraph-${index}`}>{renderInline(trimmed)}</p>);
    index += 1;
  }

  if (inCodeBlock && codeLines.length > 0) {
    blocks.push(
      <pre key={`code-${blocks.length}`}>
        <code>{codeLines.join("\n")}</code>
      </pre>,
    );
  }

  flushList(blocks, listItems, orderedList);

  return <div className="markdown-content">{blocks}</div>;
}
