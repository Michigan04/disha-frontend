// CSV upload categories for the administrator (US-09). The server checks every row
// (POST /api/imports/validate) and serves the templates; this file only lists the
// categories and their columns for the upload page, plus a sample file to try.

export const CATEGORIES = {
  results: {
    label: 'Term results',
    columns: ['roll_no', 'course_code', 'term', 'grade'],
    example: ['25f1000101', 'BSMA1004', 'May 2026', 'U'],
  },
  registrations: {
    label: 'Course registrations',
    columns: ['roll_no', 'course_code', 'term'],
    example: ['25f1000101', 'BSMA1004', 'Sep 2026'],
  },
  scores: {
    label: 'Weekly assignment scores',
    columns: ['roll_no', 'course_code', 'term', 'week', 'score'],
    example: ['25f1000101', 'BSMA1004', 'Sep 2026', '7', '64'],
  },
}

export const SAMPLE_FILES = {
  scores: [
    'roll_no,course_code,term,week,score',
    '25f1000101,BSMA1004,Sep 2026,8,71',
    '25f1000101,BSCS1002,Sep 2026,8,78',
    '25f1000214,BSCS1002,Sep 2026,8,46',
    '25f1000214,BSMA1004,Sep 2026,8,60',
    '24f2000377,BSCS2005,Sep 2026,8,84',
    '24f2000377,BSCS2006,Sep 2026,8,80',
    '25f1101833,BSCS1002,Sep 2026,8,',
    '25f1103566,BSMA1004,Sep 2026,8,58',
    '25f1103566,BSMA1004,Sep 2026,8,58',
    '25f1105299,BSCS9999,Sep 2026,8,66',
    '25f1107032,BSCS1002,Sep 2026,14,72',
    '25f1108765,BSMA1003,Sep 2026,8,91',
    'abc123,BSMA1001,Sep 2026,8,55',
    '25f1110498,BSHS1002,Sep 2026,8,74',
  ].join('\n'),
}
