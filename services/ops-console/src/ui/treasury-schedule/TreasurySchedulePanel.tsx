import { formatCurrency, gridStyle, Metric, Panel, sectionStyle } from './shared.js';

type TreasuryScheduleResponse = {
  schedule: {
    scheduledAt: string;
    source: 'ledger';
    customerId: string;
    ownerId: string;
    governanceProfile: string;
    instructions: {
      openAI: { destination: string; channel: string; amountUsd: number; notes: string };
      tax: { destination: string; channel: string; amountUsd: number; notes: string };
      ownerProfit: { destination: string; channel: string; amountUsd: number; notes: string };
    };
    sourcePlan: {
      grossInvoiceUsd: number;
      openAiUsageCostUsd: number;
      taxReserveUsd: number;
      platformReserveUsd: number;
      ownerProfitUsd: number;
      totalReserveUsd: number;
      netAfterReservesUsd: number;
      providerNotes: {
        customerCollection: string;
        openAI: string;
        tax: string;
        profit: string;
      };
      adapters: {
        paypalCheckout: {
          enabled: boolean;
          environment: string;
          apiBaseUrl: string;
          createOrderPath: string;
          captureOrderPath: string;
          orderRequest: {
            intent: string;
            application_context: {
              brand_name: string;
              landing_page: string;
              user_action: string;
              return_url: string;
              cancel_url: string;
            };
            purchase_units: Array<{
              reference_id: string;
              description: string;
              custom_id: string;
              amount: { currency_code: string; value: string };
            }>;
          };
        };
        paypalPayout: {
          enabled: boolean;
          environment: string;
          apiBaseUrl: string;
          createBatchPath: string;
          batchRequest: {
            sender_batch_header: {
              sender_batch_id: string;
              email_subject: string;
              email_message: string;
            };
            items: Array<{
              recipient_type: string;
              amount: { currency: string; value: string };
              receiver: string;
              note: string;
              sender_item_id: string;
            }>;
          };
        };
      };
    };
  } | null;
};

export interface TreasurySchedulePanelProps {
  treasurySchedule: TreasuryScheduleResponse;
}

export function TreasurySchedulePanel({ treasurySchedule }: TreasurySchedulePanelProps) {
  return (
    <section id="treasury" style={sectionStyle}>
      <h2>Treasury Schedule</h2>
      <p>The treasury planner now exposes a schedule endpoint with concrete PayPal checkout and payout adapter payloads behind the ledger plan.</p>
      <div style={gridStyle}>
        <Metric label="Source" value={treasurySchedule.schedule?.source ?? 'loading'} />
        <Metric label="Scheduled" value={treasurySchedule.schedule?.scheduledAt ?? 'loading'} />
        <Metric label="OpenAI Reserve" value={formatCurrency(treasurySchedule.schedule?.sourcePlan.openAiUsageCostUsd ?? 0)} />
        <Metric label="Owner Profit" value={formatCurrency(treasurySchedule.schedule?.sourcePlan.ownerProfitUsd ?? 0)} />
      </div>
      <div style={gridStyle}>
        <Panel title="Checkout Adapter">
          <p>Enabled {treasurySchedule.schedule?.sourcePlan.adapters.paypalCheckout.enabled ? 'yes' : 'no'}</p>
          <p>Environment {treasurySchedule.schedule?.sourcePlan.adapters.paypalCheckout.environment ?? 'loading'}</p>
          <p>API base {treasurySchedule.schedule?.sourcePlan.adapters.paypalCheckout.apiBaseUrl ?? 'loading'}</p>
          <p>Order path {treasurySchedule.schedule?.sourcePlan.adapters.paypalCheckout.createOrderPath ?? 'loading'}</p>
        </Panel>
        <Panel title="Payout Adapter">
          <p>Enabled {treasurySchedule.schedule?.sourcePlan.adapters.paypalPayout.enabled ? 'yes' : 'no'}</p>
          <p>Environment {treasurySchedule.schedule?.sourcePlan.adapters.paypalPayout.environment ?? 'loading'}</p>
          <p>API base {treasurySchedule.schedule?.sourcePlan.adapters.paypalPayout.apiBaseUrl ?? 'loading'}</p>
          <p>Batch path {treasurySchedule.schedule?.sourcePlan.adapters.paypalPayout.createBatchPath ?? 'loading'}</p>
        </Panel>
        <Panel title="IRS Instruction">
          <p>Channel {treasurySchedule.schedule?.instructions.tax.channel ?? 'loading'}</p>
          <p>Amount {formatCurrency(treasurySchedule.schedule?.instructions.tax.amountUsd ?? 0)}</p>
          <p>{treasurySchedule.schedule?.instructions.tax.notes ?? 'loading'}</p>
        </Panel>
        <Panel title="Reserve Summary">
          <p>Gross {formatCurrency(treasurySchedule.schedule?.sourcePlan.grossInvoiceUsd ?? 0)}</p>
          <p>Total reserve {formatCurrency(treasurySchedule.schedule?.sourcePlan.totalReserveUsd ?? 0)}</p>
          <p>Net after reserves {formatCurrency(treasurySchedule.schedule?.sourcePlan.netAfterReservesUsd ?? 0)}</p>
        </Panel>
      </div>
      <table>
        <thead>
          <tr>
            <th>Instruction</th>
            <th>Destination</th>
            <th>Channel</th>
            <th>Amount</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {treasurySchedule.schedule ? (
            <>
              <tr>
                <td>OpenAI</td>
                <td>{treasurySchedule.schedule.instructions.openAI.destination}</td>
                <td>{treasurySchedule.schedule.instructions.openAI.channel}</td>
                <td>{formatCurrency(treasurySchedule.schedule.instructions.openAI.amountUsd)}</td>
                <td>{treasurySchedule.schedule.instructions.openAI.notes}</td>
              </tr>
              <tr>
                <td>Tax</td>
                <td>{treasurySchedule.schedule.instructions.tax.destination}</td>
                <td>{treasurySchedule.schedule.instructions.tax.channel}</td>
                <td>{formatCurrency(treasurySchedule.schedule.instructions.tax.amountUsd)}</td>
                <td>{treasurySchedule.schedule.instructions.tax.notes}</td>
              </tr>
              <tr>
                <td>Owner Profit</td>
                <td>{treasurySchedule.schedule.instructions.ownerProfit.destination}</td>
                <td>{treasurySchedule.schedule.instructions.ownerProfit.channel}</td>
                <td>{formatCurrency(treasurySchedule.schedule.instructions.ownerProfit.amountUsd)}</td>
                <td>{treasurySchedule.schedule.instructions.ownerProfit.notes}</td>
              </tr>
            </>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}
