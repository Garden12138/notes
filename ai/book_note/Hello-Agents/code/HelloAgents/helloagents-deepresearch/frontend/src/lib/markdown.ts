import DOMPurify from "dompurify";
import { marked } from "marked";

marked.setOptions({
  breaks: true,
  gfm: true,
});

export function renderMarkdown(markdown: string): string {
  if (!markdown.trim()) return "";
  const parsed = marked.parse(markdown, { async: false });
  const sanitized = DOMPurify.sanitize(parsed, {
    USE_PROFILES: { html: true },
  });

  const template = document.createElement("template");
  template.innerHTML = sanitized;
  for (const link of template.content.querySelectorAll("a")) {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
  return template.innerHTML;
}
