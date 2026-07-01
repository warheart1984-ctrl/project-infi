const fs = require("node:fs");
const path = require("node:path");

function createProject({ rootDir, type, name }) {
  const safeName = sanitizeProjectName(name);
  const projectRoot = path.join(rootDir, safeName);
  fs.mkdirSync(projectRoot, { recursive: false });

  if (type === "python") {
    writePython(projectRoot, safeName);
  } else if (type === "node") {
    writeNode(projectRoot, safeName);
  } else if (type === "rust") {
    writeRust(projectRoot, safeName);
  } else {
    throw new Error(`Unknown template type: ${type}`);
  }
  return projectRoot;
}

function sanitizeProjectName(name) {
  const safe = String(name || "").trim().replace(/[^a-zA-Z0-9_-]/g, "-");
  if (!safe) {
    throw new Error("Project name is required");
  }
  return safe;
}

function writePython(root, name) {
  fs.writeFileSync(path.join(root, "app.py"), [
    "from fastapi import FastAPI",
    "",
    "app = FastAPI()",
    "",
    '@app.get("/v1/health")',
    "def health():",
    '    return {"status": "ok"}',
    "",
  ].join("\n"), "utf8");
  fs.writeFileSync(path.join(root, "requirements.txt"), "fastapi\nuvicorn\n", "utf8");
  fs.writeFileSync(path.join(root, "README.md"), `# ${name}\n\nNova Python health-service template.\n`, "utf8");
}

function writeNode(root, name) {
  fs.writeFileSync(path.join(root, "index.js"), [
    "const express = require('express');",
    "const app = express();",
    "",
    "app.get('/v1/health', (req, res) => {",
    "  res.json({ status: 'ok' });",
    "});",
    "",
    "app.listen(3000);",
    "",
  ].join("\n"), "utf8");
  fs.writeFileSync(path.join(root, "package.json"), JSON.stringify({
    name,
    version: "0.1.0",
    dependencies: { express: "^4.18.2" },
  }, null, 2) + "\n", "utf8");
  fs.writeFileSync(path.join(root, "README.md"), `# ${name}\n\nNova Node.js health-service template.\n`, "utf8");
}

function writeRust(root, name) {
  fs.mkdirSync(path.join(root, "src"));
  fs.writeFileSync(path.join(root, "src", "main.rs"), [
    "use actix_web::{get, App, HttpServer, Responder};",
    "",
    '#[get("/v1/health")]',
    "async fn health() -> impl Responder {",
    '    "{\\"status\\":\\"ok\\"}"',
    "}",
    "",
    "#[actix_web::main]",
    "async fn main() -> std::io::Result<()> {",
    "    HttpServer::new(|| App::new().service(health))",
    '        .bind("127.0.0.1:8080")?',
    "        .run()",
    "        .await",
    "}",
    "",
  ].join("\n"), "utf8");
  fs.writeFileSync(path.join(root, "Cargo.toml"), [
    "[package]",
    `name = "${name.replace(/-/g, "_")}"`,
    'version = "0.1.0"',
    'edition = "2021"',
    "",
    "[dependencies]",
    'actix-web = "4"',
    "",
  ].join("\n"), "utf8");
  fs.writeFileSync(path.join(root, "README.md"), `# ${name}\n\nNova Rust health-service template.\n`, "utf8");
}

module.exports = {
  createProject,
  sanitizeProjectName,
};
