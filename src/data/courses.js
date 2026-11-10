// Course catalogue, loaded from the backend (see reference.js).
//   COURSES[id]          { id, code, name, level, type: 'course' | 'project', credits, oppe? }
//   LEVEL_COURSES[level] course ids in the order they are usually taken

import { reactive } from 'vue'

export const COURSES = reactive({})
export const LEVEL_COURSES = reactive({})
// TERM_OUTCOMES[id]   { term, parts: [{ label, pct }] }: last term's results by component
export const TERM_OUTCOMES = reactive({})
