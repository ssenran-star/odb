export type LocalChunk = {
  id: string;
  document: string;
  metadata: {
    source: string;
    title: string;
    chunkIndex: number;
  };
};

const MAX_CHARS = 420;

export function titleFromName(name: string): string {
  return name
    .replace(/\.[^.]+$/, "")
    .replace(/^\d+-/, "")
    .replace(/[-_]/g, " ");
}

export function chunkDocument(input: {
  source: string;
  title: string;
  text: string;
}): LocalChunk[] {
  const normalized = input.text.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];
  const paragraphs = normalized
    .split(/\n\s*\n/)
    .map((part) => part.replace(/\s+/g, " ").trim())
    .filter(Boolean);

  const pieces: string[] = [];
  for (const paragraph of paragraphs) {
    if (paragraph.length <= MAX_CHARS) {
      pieces.push(paragraph);
      continue;
    }
    const sentences = paragraph.split(/(?<=[。！？.!?])\s*/);
    let buffer = "";
    for (const sentence of sentences) {
      if ((buffer + sentence).length > MAX_CHARS && buffer) {
        pieces.push(buffer.trim());
        buffer = sentence;
      } else {
        buffer += sentence;
      }
    }
    if (buffer.trim()) pieces.push(buffer.trim());
  }

  return pieces.map((document, chunkIndex) => ({
    id: `${input.source}::${chunkIndex}`,
    document,
    metadata: {
      source: input.source,
      title: input.title,
      chunkIndex,
    },
  }));
}
