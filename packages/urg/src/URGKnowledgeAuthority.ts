export class URGKnowledgeAuthority {
  canRead(actor: string): boolean {
    return actor.length > 0;
  }

  canWrite(actor: string): boolean {
    return actor === 'governance' || actor === 'runtime';
  }
}
