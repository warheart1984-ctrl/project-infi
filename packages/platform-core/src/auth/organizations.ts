import { randomBytes } from 'node:crypto';

import type {
  OrganizationMemberRecord,
  OrganizationRecord,
  OrganizationRole,
} from '../types.js';

export interface OrganizationCreateInput {
  name: string;
  billingContactEmail: string;
  planId: string;
  domain?: string;
  ownerCustomerId: string;
  ownerRole?: OrganizationRole;
}

export interface OrganizationMemberInput {
  customerId: string;
  role: OrganizationRole;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function normalizeName(value: string): string {
  return value.trim();
}

function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

function createOrganizationId(name: string): string {
  return `org_${normalizeName(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || randomBytes(4).toString('hex')}`;
}

export class OrganizationStore {
  private readonly organizations = new Map<string, OrganizationRecord>();

  create(input: OrganizationCreateInput): OrganizationRecord {
    if (!isNonEmptyString(input.name)) {
      throw new Error('ORGANIZATION: name is required');
    }
    if (!isNonEmptyString(input.billingContactEmail)) {
      throw new Error('ORGANIZATION: billing contact email is required');
    }

    const now = new Date().toISOString();
    const id = createOrganizationId(input.name);
    const ownerRole = input.ownerRole ?? 'owner';
    const organization: OrganizationRecord = {
      id,
      name: normalizeName(input.name),
      ownerCustomerId: input.ownerCustomerId,
      planId: input.planId,
      billingContactEmail: normalizeEmail(input.billingContactEmail),
      domain: input.domain?.trim() || undefined,
      members: [
        {
          customerId: input.ownerCustomerId,
          role: ownerRole,
          joinedAt: now,
        },
      ],
      createdAt: now,
      updatedAt: now,
    };

    this.organizations.set(id, organization);
    return this.clone(organization);
  }

  upsert(input: OrganizationCreateInput & { id?: string }): OrganizationRecord {
    if (input.id) {
      const existing = this.organizations.get(input.id);
      if (existing) {
        return this.addMember(existing.id, {
          customerId: input.ownerCustomerId,
          role: input.ownerRole ?? 'owner',
        });
      }
      const created = this.create({ ...input, name: input.name || input.id });
      if (created.id !== input.id) {
        this.organizations.delete(created.id);
        const rewritten: OrganizationRecord = {
          ...created,
          id: input.id,
          name: normalizeName(input.name || input.id),
          planId: input.planId,
        };
        this.organizations.set(rewritten.id, rewritten);
        return this.clone(rewritten);
      }
      return created;
    }
    return this.create(input);
  }

  addMember(organizationId: string, input: OrganizationMemberInput): OrganizationRecord {
    const organization = this.organizations.get(organizationId);
    if (!organization) {
      throw new Error('ORGANIZATION: organization not found');
    }

    const now = new Date().toISOString();
    const members = organization.members.filter((member) => member.customerId !== input.customerId);
    members.push({
      customerId: input.customerId,
      role: input.role,
      joinedAt: now,
    });

    const updated: OrganizationRecord = {
      ...organization,
      members,
      updatedAt: now,
    };
    this.organizations.set(organizationId, updated);
    return this.clone(updated);
  }

  setMemberRole(organizationId: string, customerId: string, role: OrganizationRole): OrganizationRecord {
    return this.addMember(organizationId, { customerId, role });
  }

  get(organizationId: string): OrganizationRecord | undefined {
    const organization = this.organizations.get(organizationId);
    return organization ? this.clone(organization) : undefined;
  }

  findByMember(customerId: string): OrganizationRecord | undefined {
    for (const organization of this.organizations.values()) {
      if (organization.members.some((member) => member.customerId === customerId)) {
        return this.clone(organization);
      }
    }
    return undefined;
  }

  list(): OrganizationRecord[] {
    return [...this.organizations.values()].map((organization) => this.clone(organization));
  }

  listMembers(organizationId: string): OrganizationMemberRecord[] {
    const organization = this.organizations.get(organizationId);
    return organization ? organization.members.map((member) => ({ ...member })) : [];
  }

  private clone(organization: OrganizationRecord): OrganizationRecord {
    return {
      ...organization,
      members: organization.members.map((member) => ({ ...member })),
    };
  }
}
