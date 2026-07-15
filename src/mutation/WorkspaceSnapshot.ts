export class WorkspaceSnapshot {
  constructor(private files: Record<string, string> = {}) {}

  getFile(path: string) {
    return this.files[path] ?? null
  }

  setFile(path: string, content: string) {
    this.files[path] = content
  }

  deleteFile(path: string) {
    delete this.files[path]
  }

  clone() {
    return new WorkspaceSnapshot({ ...this.files })
  }
}
