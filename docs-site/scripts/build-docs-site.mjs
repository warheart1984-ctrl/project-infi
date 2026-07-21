import { mkdir, readdir, readFile, rm, stat, writeFile, copyFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(scriptDir, "..");
const contentRoots = [
  path.join(siteRoot, "src", "pages"),
  path.join(siteRoot, "docs")
];
const staticRoot = path.join(siteRoot, "static");
const distRoot = path.join(siteRoot, "dist");

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${href.replace(/\.mdx?$/i, ".html")}">${label}</a>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function stripFrontMatter(markdown) {
  if (!markdown.startsWith("---")) {
    return markdown;
  }
  const end = markdown.indexOf("\n---", 3);
  if (end === -1) {
    return markdown;
  }
  return markdown.slice(end + 4).replace(/^\s+/, "");
}

function extractTitle(markdown, fallback) {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : fallback;
}

function renderMarkdown(markdown) {
  const lines = stripFrontMatter(markdown).split(/\r?\n/);
  const output = [];
  let inList = false;
  let inCode = false;
  let codeBuffer = [];

  const flushList = () => {
    if (inList) {
      output.push("</ul>");
      inList = false;
    }
  };

  const flushCode = () => {
    if (inCode) {
      output.push(`<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
      codeBuffer = [];
      inCode = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.replace(/\s+$/, "");
    if (line.startsWith("```")) {
      if (inCode) {
        flushCode();
      } else {
        flushList();
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuffer.push(line);
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushList();
      const level = heading[1].length;
      output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }
    const bullet = line.match(/^- (.+)$/);
    if (bullet) {
      if (!inList) {
        output.push("<ul>");
        inList = true;
      }
      output.push(`<li>${inlineMarkdown(bullet[1])}</li>`);
      continue;
    }
    if (!line.trim()) {
      flushList();
      output.push("");
      continue;
    }
    flushList();
    output.push(`<p>${inlineMarkdown(line)}</p>`);
  }
  flushCode();
  flushList();
  return output.join("\n");
}

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await walk(full));
    } else if (entry.isFile() && (entry.name.endsWith(".md") || entry.name.endsWith(".mdx"))) {
      files.push(full);
    }
  }
  return files;
}

async function ensureDir(filePath) {
  await mkdir(path.dirname(filePath), { recursive: true });
}

async function copyStatic(sourceDir, targetDir) {
  try {
    const entries = await readdir(sourceDir, { withFileTypes: true });
    for (const entry of entries) {
      const src = path.join(sourceDir, entry.name);
      const dst = path.join(targetDir, entry.name);
      if (entry.isDirectory()) {
        await copyStatic(src, dst);
      } else if (entry.isFile()) {
        await ensureDir(dst);
        await copyFile(src, dst);
      }
    }
  } catch {
    // static assets are optional
  }
}

function toRoute(filePath) {
  const relativeFromPages = path.relative(path.join(siteRoot, "src", "pages"), filePath);
  if (!relativeFromPages.startsWith("..")) {
    return relativeFromPages.replace(/\.mdx?$/i, ".html");
  }
  const relativeFromDocs = path.relative(path.join(siteRoot, "docs"), filePath);
  return path.join("docs", relativeFromDocs).replace(/\.mdx?$/i, ".html");
}

function navItems(pages) {
  return pages
    .map((page) => `<a href="/${page.route.replace(/\\/g, "/")}">${escapeHtml(page.title)}</a>`)
    .join("");
}

function pageTemplate({ title, nav, content }) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    <style>
      :root { color-scheme: dark; --bg: #0d1117; --panel: #161b22; --text: #e6edf3; --muted: #8b949e; --accent: #79c0ff; }
      body { margin: 0; font-family: Inter, system-ui, sans-serif; background: linear-gradient(180deg, #09111f 0%, #0d1117 100%); color: var(--text); }
      .layout { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
      aside { padding: 24px; border-right: 1px solid rgba(255,255,255,.08); background: rgba(22,27,34,.9); position: sticky; top: 0; height: 100vh; overflow:auto; }
      main { padding: 32px; max-width: 980px; }
      h1,h2,h3 { line-height: 1.2; }
      nav { display: grid; gap: 10px; margin-top: 20px; }
      nav a { color: var(--text); text-decoration: none; padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,.03); }
      nav a:hover { background: rgba(121,192,255,.12); color: var(--accent); }
      p, li { color: var(--text); line-height: 1.7; }
      p { max-width: 75ch; }
      pre { background: var(--panel); padding: 16px; border-radius: 12px; overflow:auto; }
      code { background: rgba(255,255,255,.06); padding: 2px 5px; border-radius: 6px; }
      table { border-collapse: collapse; width: 100%; margin: 18px 0; }
      th, td { border: 1px solid rgba(255,255,255,.12); padding: 8px 10px; text-align:left; vertical-align: top; }
      th { background: rgba(255,255,255,.04); }
      a { color: var(--accent); }
      .eyebrow { color: var(--muted); font-size: .88rem; text-transform: uppercase; letter-spacing: .08em; }
    </style>
  </head>
  <body>
    <div class="layout">
      <aside>
        <div class="eyebrow">AAES-OS Docs</div>
        <h1>Governed Runtime Docs</h1>
        <p>Evidence-first documentation for constitutional governance, runtime behavior, agents, and ULX.</p>
        <nav>${nav}</nav>
      </aside>
      <main>
        ${content}
      </main>
    </div>
  </body>
</html>`;
}

async function build() {
  await rm(distRoot, { recursive: true, force: true });
  await mkdir(distRoot, { recursive: true });
  await copyStatic(staticRoot, distRoot);

  const markdownFiles = [];
  for (const root of contentRoots) {
    markdownFiles.push(...await walk(root));
  }

  const pages = [];
  for (const filePath of markdownFiles) {
    const raw = await readFile(filePath, "utf8");
    const route = toRoute(filePath);
    const title = extractTitle(stripFrontMatter(raw), path.basename(filePath, ".md"));
    pages.push({ filePath, route, title, raw });
  }

  pages.sort((a, b) => a.route.localeCompare(b.route));
  const nav = navItems(pages);

  for (const page of pages) {
    const html = pageTemplate({
      title: `${page.title} | AAES-OS Documentation`,
      nav,
      content: renderMarkdown(page.raw)
    });
    const outPath = path.join(distRoot, page.route);
    await ensureDir(outPath);
    await writeFile(outPath, html, "utf8");
  }

  const homepageSource = path.join(siteRoot, "src", "pages", "index.mdx");
  const homepage = pageTemplate({
    title: "AAES-OS Documentation",
    nav,
    content: renderMarkdown(await readFile(homepageSource, "utf8"))
  });
  await writeFile(path.join(distRoot, "index.html"), homepage, "utf8");

  console.log(`Built ${pages.length} docs pages into ${distRoot}`);
}

build().catch((error) => {
  console.error(error);
  process.exit(1);
});
