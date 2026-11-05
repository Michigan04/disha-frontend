// Course catalogue (sample). Course names follow the BS programme; codes are omitted.

export const COURSES = {
  math1: { id: 'math1', name: 'Mathematics for Data Science I', level: 'foundation', type: 'course', credits: 4 },
  stats1: { id: 'stats1', name: 'Statistics for Data Science I', level: 'foundation', type: 'course', credits: 4 },
  ct: { id: 'ct', name: 'Computational Thinking', level: 'foundation', type: 'course', credits: 4 },
  eng1: { id: 'eng1', name: 'English I', level: 'foundation', type: 'course', credits: 4 },
  math2: { id: 'math2', name: 'Mathematics for Data Science II', level: 'foundation', type: 'course', credits: 4 },
  stats2: { id: 'stats2', name: 'Statistics for Data Science II', level: 'foundation', type: 'course', credits: 4 },
  python: { id: 'python', name: 'Programming in Python', level: 'foundation', type: 'course', credits: 4, oppe: true },
  eng2: { id: 'eng2', name: 'English II', level: 'foundation', type: 'course', credits: 4 },

  dbms: { id: 'dbms', name: 'Database Management Systems', level: 'diploma', type: 'course', credits: 4 },
  pdsa: { id: 'pdsa', name: 'Programming, Data Structures and Algorithms using Python', level: 'diploma', type: 'course', credits: 4, oppe: true },
  mad1: { id: 'mad1', name: 'Modern Application Development I', level: 'diploma', type: 'course', credits: 4 },
  mad1p: { id: 'mad1p', name: 'Modern Application Development I Project', level: 'diploma', type: 'project', credits: 2 },
  sc: { id: 'sc', name: 'System Commands', level: 'diploma', type: 'course', credits: 3, oppe: true },
  java: { id: 'java', name: 'Programming Concepts using Java', level: 'diploma', type: 'course', credits: 4, oppe: true },
  mad2: { id: 'mad2', name: 'Modern Application Development II', level: 'diploma', type: 'course', credits: 4 },
  mad2p: { id: 'mad2p', name: 'Modern Application Development II Project', level: 'diploma', type: 'project', credits: 2 },
}

export const LEVEL_COURSES = {
  foundation: ['math1', 'stats1', 'ct', 'eng1', 'math2', 'stats2', 'python', 'eng2'],
  diploma: ['dbms', 'pdsa', 'mad1', 'mad1p', 'sc', 'java', 'mad2', 'mad2p'],
}
