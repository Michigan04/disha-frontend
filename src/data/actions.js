// Suggested actions for each risk reason. In the full platform the administrator
// maintains this list (US-06); these are sample entries.

export const CATEGORIES = {
  academic: { label: 'Academic support', cls: 'route' },
  planning: { label: 'Planning advice', cls: 'ok' },
  admin: { label: 'Administrative follow-up', cls: '' },
}

export const SUGGESTED_ACTIONS = {
  failed_twice: [
    { key: 'refer', text: 'Refer to the course instructor for weekly check-ins until the next OPPE or exam', cat: 'academic' },
    { key: 'load', text: 'Agree a lighter course load for the next term', cat: 'planning' },
  ],
  failed_once: [
    { key: 'plan', text: 'Share the 12-week study plan and check that it has been opened', cat: 'academic' },
    { key: 'reg', text: 'Confirm the student is registered for the re-attempt', cat: 'admin' },
  ],
  oppe_not_eligible: [
    { key: 'oppe', text: 'Share OPPE practice sets and the next OPPE date', cat: 'academic' },
    { key: 'count', text: 'Explain which weekly assignments still count towards OPPE 2', cat: 'planning' },
  ],
  low_prediction: [
    { key: 'doubt', text: 'Suggest this week’s doubt-clearing sessions for the course', cat: 'academic' },
  ],
  plan_inactive: [
    { key: 'nudge', text: 'Send a reminder: the study plan has not been opened for a week', cat: 'admin' },
  ],
  behind_milestone: [
    { key: 'milestone', text: 'Plan the courses needed to meet the next milestone', cat: 'planning' },
  ],
  data_issue: [
    { key: 'verify', text: 'Ask the program office to confirm the record before contacting the student', cat: 'admin' },
  ],
}

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
