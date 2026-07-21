import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { extname } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(scriptDir, "..");
const distRoot = path.join(siteRoot, "dist");

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico": "image/x-icon",
  ".json": "application/json; charset=utf-8"
};

function getArg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

const host = getArg("--host", "127.0.0.1");
const port = Number(getArg("--port", "3000"));

async function resolveFilePath(requestPathname) {
  const candidates = [];
  if (requestPathname === "/") {
    candidates.push(path.join(distRoot, "index.html"));
  } else {
    candidates.push(path.join(distRoot, requestPathname));
    candidates.push(path.join(distRoot, `${requestPathname}.html`));
    candidates.push(path.join(distRoot, requestPathname, "index.html"));
  }

  for (const candidate of candidates) {
    try {
      await readFile(candidate);
      return candidate;
    } catch {
      // try next fallback
    }
  }

  throw new Error(`No file found for ${requestPathname}`);
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://${host}:${port}`);
    let pathname = decodeURIComponent(url.pathname);
    const filePath = await resolveFilePath(pathname);
    const content = await readFile(filePath);
    res.setHeader("Content-Type", mimeTypes[extname(filePath)] ?? "application/octet-stream");
    res.end(content);
  } catch {
    res.statusCode = 404;
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.end("Not found");
  }
});

server.listen(port, host, () => {
  console.log(`Docs site running at http://${host}:${port}`);
});
