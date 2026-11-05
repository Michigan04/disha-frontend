// What helped past students who failed a course once and then passed it.
// Sample, anonymised figures; in the platform these come from the predictive model
// and the outcome records (US-11), not from this file.

export const PAST_STUDENT_INSIGHTS = {
  stats2: {
    failedOnce: 186,
    passedNext: 132,
    whatHelped: [
      { text: 'Redid every weekly assignment from the failed term before Week 1', share: 78 },
      { text: 'Attended at least six live sessions during the term', share: 64 },
      { text: 'Solved two previous end-term papers under timed conditions', share: 59 },
      { text: 'Took no more than two other courses alongside the re-attempt', share: 55 },
    ],
    plan: [
      { when: 'Weeks 1 to 3', what: 'Revise probability and random variables using the failed term’s assignments.' },
      { when: 'Weeks 4 to 7', what: 'Keep the weekly assignment average above 60 and bring doubts to live sessions.' },
      { when: 'Weeks 8 to 10', what: 'Focus on hypothesis testing and estimation; attempt one past paper each week.' },
      { when: 'Weeks 11 and 12', what: 'Two timed full papers and a review of mistakes before the end-term.' },
    ],
  },
  python: {
    failedOnce: 240,
    passedNext: 168,
    whatHelped: [
      { text: 'Practised OPPE-style problems on the online IDE every week', share: 84 },
      { text: 'Took the mock OPPE twice before the real one', share: 71 },
      { text: 'Joined doubt-clearing sessions for help with debugging', share: 58 },
      { text: 'Wrote code by hand for ten minutes a day before using the IDE', share: 41 },
    ],
    plan: [
      { when: 'Weeks 1 to 4', what: 'One OPPE-style problem a day, timed, without looking at notes.' },
      { when: 'Weeks 5 to 7', what: 'Clear all weekly assignments early and attend one doubt session a week.' },
      { when: 'Weeks 8 and 9', what: 'Two mock OPPEs, then fix every error type that appeared.' },
      { when: 'Week 10 onwards', what: 'Revise file handling and dictionaries, the topics past students missed most.' },
    ],
  },
}
