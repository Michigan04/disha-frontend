// Week-by-week study plans for a course the student has failed before.
// Built from what students who failed once and then passed actually did (sample data).

export const STUDY_PLANS = {
  stats2: {
    goal: 'Pass with a C or better',
    hoursPerWeek: 8,
    weeks: [
      { w: 1, focus: 'Multiple random variables', hours: 6, tasks: ['Redo the May-term Week 1 assignment', 'Make a joint PMF practice table (10 questions)', 'Watch the joint distributions recap'] },
      { w: 2, focus: 'Independence', hours: 6, tasks: ['Redo the May-term Week 2 assignment', 'Solve 8 conditional probability problems', 'Note 3 mistakes from your last attempt'] },
      { w: 3, focus: 'Expectation', hours: 7, tasks: ['Submit the Week 3 graded assignment', 'Practice set: expectation of functions', 'Join the live session'] },
      { w: 4, focus: 'Variance and covariance', hours: 7, tasks: ['Submit the Week 4 graded assignment', 'Solve 10 covariance problems', 'Add variance rules to your formula sheet'] },
      { w: 5, focus: 'Inequalities', hours: 7, tasks: ['Submit the Week 5 graded assignment', 'Markov and Chebyshev drill (6 questions)', 'Revise weeks 1 to 4'] },
      { w: 6, focus: 'Continuous random variables, Quiz 1', hours: 9, checkpoint: 'Quiz 1', tasks: ['Two past Quiz 1 papers, timed', '6 PDF and CDF problems', 'Go through every mistake'] },
      { w: 7, focus: 'Joint continuous distributions', hours: 8, tasks: ['Submit the Week 7 graded assignment', '8 joint density problems', 'Join the doubt session'] },
      { w: 8, focus: 'Sampling and the CLT', hours: 8, tasks: ['Submit the Week 8 graded assignment', '8 CLT problems', 'Watch the sampling distributions recap'] },
      { w: 9, focus: 'Estimation (MoM and MLE)', hours: 8, tasks: ['Submit the Week 9 graded assignment', '6 MLE problems', 'One table: MoM vs MLE'] },
      { w: 10, focus: 'Bayesian estimation, Quiz 2', hours: 9, checkpoint: 'Quiz 2', tasks: ['Two past Quiz 2 papers, timed', 'Revise weeks 5 to 9', 'Go through every mistake'] },
      { w: 11, focus: 'Hypothesis testing', hours: 8, tasks: ['Submit the Week 11 graded assignment', 'Draw a flowchart for choosing a test', '10 hypothesis test problems'] },
      { w: 12, focus: 'End-term preparation', hours: 10, checkpoint: 'End term', tasks: ['Two full past papers, timed', 'Finish your formula sheet', 'Read your mistake notes'] },
    ],
  },
  python: {
    goal: 'Clear both OPPEs and pass the course',
    hoursPerWeek: 9,
    weeks: [
      { w: 1, focus: 'Variables and expressions', hours: 6, tasks: ['One timed problem a day on the online IDE', 'Redo the Week 1 programming assignment', 'Type out, do not copy, every example'] },
      { w: 2, focus: 'Conditions', hours: 6, tasks: ['Submit the Week 2 graded assignment', '10 if/else problems with edge cases', 'Read your last OPPE attempt’s errors'] },
      { w: 3, focus: 'Loops', hours: 7, tasks: ['Submit the Week 3 graded assignment', '8 nested-loop problems', 'Join the doubt session'] },
      { w: 4, focus: 'Strings', hours: 7, tasks: ['Submit the Week 4 graded assignment', '10 string manipulation problems', 'Weekly check-in with your instructor'] },
      { w: 5, focus: 'Lists', hours: 8, tasks: ['Submit the Week 5 graded assignment', '8 list problems, timed', 'Weekly check-in with your instructor'] },
      { w: 6, focus: 'Functions', hours: 8, checkpoint: 'Quiz 1', tasks: ['Submit the Week 6 graded assignment', 'Rewrite 5 old solutions as functions', 'Quiz 1 revision'] },
      { w: 7, focus: 'Dictionaries and sets', hours: 9, tasks: ['Submit the Week 7 graded assignment', '10 dictionary problems', 'Weekly check-in with your instructor'] },
      { w: 8, focus: 'OPPE 1 practice', hours: 10, checkpoint: 'OPPE 1', tasks: ['Mock OPPE under exam conditions', 'Fix every error type from the mock', 'Practise on the exam IDE'] },
      { w: 9, focus: 'File handling', hours: 8, tasks: ['Submit the Week 9 graded assignment', '6 file read/write problems', 'Weekly check-in with your instructor'] },
      { w: 10, focus: 'Exceptions and modules', hours: 8, tasks: ['Submit the Week 10 graded assignment', 'Add error handling to 3 old solutions', 'Second mock OPPE'] },
      { w: 11, focus: 'OPPE 2 practice', hours: 10, checkpoint: 'OPPE 2', tasks: ['Two OPPE-style sets, timed', 'Review with the course TA', 'Rest the evening before'] },
      { w: 12, focus: 'End-term preparation', hours: 9, checkpoint: 'End term', tasks: ['Two past end-term papers', 'Revise dictionaries and files', 'Read your mistake notes'] },
    ],
  },
}
