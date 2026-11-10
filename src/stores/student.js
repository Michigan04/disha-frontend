import { defineStore } from 'pinia'
import { api } from '../services/api'
import {
  cgpa, completed, courseList, currentCourses, currentTermLabel, currentTermNumber,
  milestones, nextMilestone, risk, termSummaries,
} from '../utils/progress'
import { LEVEL_RULES } from '../data/rules'

// The signed-in student's record (GET /api/me/student, loaded by services/loader.js)
// and everything worked out from it.
export const useStudentStore = defineStore('student', {
  state: () => ({ student: null }),
  getters: {
    rule() { return LEVEL_RULES[this.student.level] },
    termNumber() { return currentTermNumber(this.student) },
    termLabel() { return currentTermLabel(this.student) },
    cgpa() { return cgpa(this.student) },
    done() { return completed(this.student) },
    courses() { return courseList(this.student) },
    current() { return currentCourses(this.student) },
    terms() { return termSummaries(this.student) },
    milestones() { return milestones(this.student) },
    nextMilestone() { return nextMilestone(this.student) },
    risk() { return risk(this.student) },
  },
  actions: {
    async load() {
      this.apply((await api.fresh('/me/student')).data)
    },
    apply(student) {
      this.student = student
    },
    clear() {
      this.student = null
    },
  },
})
