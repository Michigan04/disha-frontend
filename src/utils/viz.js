// Chart status colours, shared by every chart. Each colour has one meaning and is never
// reused for anything else. Checked with the colour-blind separation validator
// (every pair is at least ΔE 10 apart for protan, deutan and tritan vision).
// Keep in sync with the --viz-* tokens in styles/main.css.
export const VIZ = {
  critical: '#a8362e', // High risk, escalated, not contacted, behind: needs action now
  warning: '#d4a03a', // Low risk, no response, at risk: watch closely
  good: '#389670', // On track, resolved, healthy capacity
  active: '#3e65a8', // In progress: work under way
  pred: '#7d5ca8', // Model estimate (predicted to fail), not a confirmed flag
  neutral: '#d5ccc0', // No intervention needed yet / remainder
}

// Usage against a limit: green while there is room, mustard when tight, red when full.
export const loadColor = (used, limit) => {
  const r = limit ? used / limit : 0
  return r > 0.9 ? VIZ.critical : r > 0.75 ? VIZ.warning : VIZ.good
}
