<script lang="ts">

  import { DEFAULT_SETTINGS, type OperatorSettings } from "../lib/settings";



  let {

    open = false,

    settings,

    onClose,

    onSave,

  }: {

    open?: boolean;

    settings: OperatorSettings;

    onClose?: () => void;

    onSave?: (s: OperatorSettings) => void;

  } = $props();



  let draft = $state<OperatorSettings>({ ...settings });



  $effect(() => {

    if (open) {

      draft = { ...settings };

    }

  });



  function save() {

    const next: OperatorSettings = {

      ...DEFAULT_SETTINGS,

      ...draft,

      kernelUrl: draft.kernelUrl.trim() || DEFAULT_SETTINGS.kernelUrl,

      lawfulBrainUrl: draft.lawfulBrainUrl.trim() || DEFAULT_SETTINGS.lawfulBrainUrl,

      maxSteps: Math.max(1, Math.min(50, Number(draft.maxSteps) || DEFAULT_SETTINGS.maxSteps)),

    };

    onSave?.(next);

    onClose?.();

  }

</script>



{#if open}

  <div class="backdrop">
    <button type="button" class="backdrop-hit" aria-label="Close settings" onclick={() => onClose?.()}></button>

    <div

      class="modal"

      role="dialog"

      aria-labelledby="settings-title"

    >

      <h2 id="settings-title">Settings</h2>



      <label>

        Kernel URL

        <input type="url" bind:value={draft.kernelUrl} placeholder="http://127.0.0.1:8790" />

      </label>



      <label>

        Lawful brain URL

        <input type="url" bind:value={draft.lawfulBrainUrl} placeholder="http://127.0.0.1:8791" />

      </label>



      <label>

        Default agent

        <select bind:value={draft.defaultAgentId}>

          <option value="explorer">Explorer (read-only)</option>

          <option value="builder">Builder (edits + shell)</option>

          <option value="reviewer">Reviewer (read-only, no shell)</option>

        </select>

      </label>



      <label>

        Max steps per run

        <input type="number" min="1" max="50" bind:value={draft.maxSteps} />

      </label>



      <fieldset class="toggles">

        <legend>Task constraints</legend>

        <label class="check">

          <input type="checkbox" bind:checked={draft.readOnly} />

          Read-only (no file patches)

        </label>

        <label class="check">

          <input type="checkbox" bind:checked={draft.allowShell} />

          Allow shell commands

        </label>

        <label class="check">

          <input type="checkbox" bind:checked={draft.allowGitCommit} />

          Allow git commits

        </label>

        <label class="check">

          <input type="checkbox" bind:checked={draft.allowNetwork} />

          Allow network

        </label>

      </fieldset>



      <p class="hint">

        The desktop host starts the operator kernel on port 8790. Override URLs only for remote

        kernels or development.

      </p>



      <div class="actions">

        <button type="button" onclick={() => onClose?.()}>Cancel</button>

        <button type="button" class="primary" onclick={save}>Save</button>

      </div>

    </div>

  </div>

{/if}



<style>

  .backdrop {

    position: fixed;

    inset: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    z-index: 100;

  }

  .backdrop-hit {
    position: absolute;
    inset: 0;
    border: none;
    padding: 0;
    margin: 0;
    background: rgba(0, 0, 0, 0.55);
    cursor: default;
  }

  .modal {

    position: relative;
    z-index: 1;
    background: #1a1f2b;

    border: 1px solid #3d4659;

    border-radius: 8px;

    padding: 1.25rem;

    width: min(440px, 92vw);

    display: flex;

    flex-direction: column;

    gap: 0.75rem;

    max-height: 90vh;

    overflow-y: auto;

  }

  h2 {

    margin: 0;

    font-size: 1rem;

  }

  label {

    display: flex;

    flex-direction: column;

    gap: 0.35rem;

    font-size: 0.85rem;

    color: #9aa3b8;

  }

  .toggles {

    border: 1px solid #3d4659;

    border-radius: 6px;

    padding: 0.75rem;

    margin: 0;

  }

  .toggles legend {

    font-size: 0.75rem;

    color: #9aa3b8;

    padding: 0 0.25rem;

  }

  .check {

    flex-direction: row;

    align-items: center;

    gap: 0.5rem;

    color: #e2e8f0;

    font-size: 0.85rem;

    margin-top: 0.35rem;

  }

  .hint {

    margin: 0;

    font-size: 0.75rem;

    color: #6b7280;

    line-height: 1.4;

  }

  .actions {

    display: flex;

    justify-content: flex-end;

    gap: 0.5rem;

    margin-top: 0.25rem;

  }

  .primary {

    background: #3b82f6;

    color: #fff;

    border: none;

    padding: 0.4rem 0.85rem;

    border-radius: 4px;

    cursor: pointer;

  }

</style>

