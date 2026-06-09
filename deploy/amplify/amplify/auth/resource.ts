import { defineAuth } from '@aws-amplify/backend';

/**
 * Cognito groups mirror AAIS operator_lanes:
 * - operator: final authority (Article I — humans decide; lane weight 1.0)
 * - observer: read-only evidence surfaces (Operator Console is read-only today)
 */
export const auth = defineAuth({
  loginWith: {
    email: true,
  },
  groups: ['operator', 'observer'],
});
