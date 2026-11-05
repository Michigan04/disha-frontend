import { defineStore } from 'pinia'
import { buildStudents } from '../data/students'
import {
  cgpa, completed, courseList, currentCourses, currentTermLabel, currentTermNumber,
  milestones, nextMilestone, risk, termSummaries,
} from '../utils/progress'
import { LEVEL_RULES } from '../data/rules'

const KEY = 'disha.demoStudent'

function readSaved() {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export const useStudentStore = defineStore('student', {
  state: () => ({
    students: buildStudents(),
    currentId: readSaved() || 'ananya',
  }),
  getters: {
    student: (s) => s.students.find((x) => x.id === s.currentId) || s.students[0],
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
    setStudent(id) {
      this.currentId = id
      try {
        localStorage.setItem(KEY, id)
      } catch {
        /* storage unavailable: the choice lasts for this visit only */
      }
    },
  },
})
