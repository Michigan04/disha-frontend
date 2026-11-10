// Labels for the staff pages, and the suggested actions for each risk reason.
// The administrator maintains the suggested actions (US-05); they are loaded from the
// backend (see reference.js).

import { reactive } from 'vue'

export const CATEGORIES = {
  academic: { label: 'Academic support', cls: 'route' },
  planning: { label: 'Planning advice', cls: 'ok' },
  admin: { label: 'Administrative follow-up', cls: '' },
}

// SUGGESTED_ACTIONS[reasonKey] [{ key, text, cat }]
export const SUGGESTED_ACTIONS = reactive({})

export const INTERVENTION_TYPES = {
  call: { label: 'Call', icon: 'phone' },
  email: { label: 'Email', icon: 'mail' },
  meeting: { label: 'Meeting', icon: 'video' },
  referral: { label: 'Referral', icon: 'refer' },
}

export const OUTCOMES = {
  not_contacted: { label: 'Not contacted yet', cls: 'high' },
  in_progress: { label: 'In progress', cls: 'route' },
  no_response: { label: 'No response', cls: 'low' },
  escalated: { label: 'Escalated', cls: 'high' },
  resolved: { label: 'Resolved', cls: 'ok' },
}
