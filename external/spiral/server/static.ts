import express, { type Express } from "express";
import fs from "fs";
import path from "path";

const ONE_HOUR_SECONDS = 60 * 60;
const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;
const IMMUTABLE_ASSET_PATTERN = /\.(?:css|js|mjs|svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|eot|map)$/i;

export function serveStatic(app: Express) {
  const distPath = path.resolve(__dirname, "public");
  if (!fs.existsSync(distPath)) {
    throw new Error(
      `Could not find the build directory: ${distPath}, make sure to build the client first`,
    );
  }

  app.use(
    express.static(distPath, {
      index: false,
      etag: true,
      maxAge: "1y",
      immutable: true,
      setHeaders: (res, filePath) => {
        if (path.basename(filePath).toLowerCase() === "index.html") {
          res.setHeader("Cache-Control", "no-cache");
          return;
        }

        if (IMMUTABLE_ASSET_PATTERN.test(filePath)) {
          res.setHeader("Cache-Control", `public, max-age=${ONE_YEAR_SECONDS}, immutable`);
          return;
        }

        res.setHeader("Cache-Control", `public, max-age=${ONE_HOUR_SECONDS}`);
      },
    }),
  );

  // fall through to index.html if the file doesn't exist
  app.use("/{*path}", (_req, res) => {
    res.setHeader("Cache-Control", "no-cache");
    res.sendFile(path.resolve(distPath, "index.html"));
  });
}
