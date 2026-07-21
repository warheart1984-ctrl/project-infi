import { gridStyle, Metric, sectionStyle } from './shared.js';

type OrganizationRegistry = {
  organizations: {
    id: string;
    name: string;
    ownerCustomerId: string;
    billingContactEmail: string;
    domain?: string;
    members: { customerId: string; role: string; joinedAt: string }[];
    createdAt: string;
    updatedAt: string;
  }[];
  organizationCount: number;
  roleCounts: Record<string, number>;
};

export interface OrganizationRegistryRbacPanelProps {
  organizations: OrganizationRegistry;
}

export function OrganizationRegistryRbacPanel({ organizations }: OrganizationRegistryRbacPanelProps) {
  return (
    <section style={sectionStyle}>
      <h2>Organization Registry and RBAC</h2>
      <p>Organizations carry owner, billing contact, and per-member roles so customer workspaces and operator surfaces stay aligned.</p>
      <div style={gridStyle}>
        <Metric label="Organizations" value={String(organizations.organizationCount)} />
        <Metric label="Owners" value={String(organizations.roleCounts.owner ?? 0)} />
        <Metric label="Admins" value={String(organizations.roleCounts.admin ?? 0)} />
        <Metric label="Auditors" value={String(organizations.roleCounts.auditor ?? 0)} />
      </div>
      <table>
        <thead>
          <tr>
            <th>Organization</th>
            <th>Owner</th>
            <th>Billing</th>
            <th>Domain</th>
            <th>Members</th>
            <th>Roles</th>
          </tr>
        </thead>
        <tbody>
          {organizations.organizations.map((organization) => (
            <tr key={organization.id}>
              <td>{organization.name}</td>
              <td>{organization.ownerCustomerId}</td>
              <td>{organization.billingContactEmail}</td>
              <td>{organization.domain ?? 'none'}</td>
              <td>{organization.members.length}</td>
              <td>{organization.members.map((member) => member.role).join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
