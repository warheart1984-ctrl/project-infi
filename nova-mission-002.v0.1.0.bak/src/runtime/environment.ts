export function getEnvironment(): { node: string; platform: string; cwd: string } {
  return {
    node: process.version,
    platform: process.platform,
    cwd: process.cwd(),
  };
}
