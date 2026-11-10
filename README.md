# Disha: Student Risk Identification and Intervention Platform

Frontend for the **Student Risk Identification and Intervention Platform** (IITM BS, Software Engineering, Team 026): a **sign-in page**, the **student portal**, and a **staff portal** for support staff, course instructors and administrators.

Built with **Vue 3, Vite, Vue Router and Pinia** on the frontend and **FastAPI, SQLAlchemy, Alembic and PostgreSQL** in `backend/`. The backend checks passwords, enforces every role's permissions, stores all records (assignments, interventions, rules, imports, study plans, audit log) and answers the chatbot. Swagger UI for the API is at `http://localhost:8000/docs`.

## Run it

You need **Node.js 20 or later**, **Python 3.12 or later** and **PostgreSQL**.

**Backend** (first time):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # then set DATABASE_URL and JWT_SECRET
createdb disha                   # or create the database in pgAdmin
uvicorn app.main:app --reload    # http://localhost:8000, docs at /docs
```

On start-up the backend applies the Alembic migrations and, if the database is empty, seeds the demo accounts and the 60-student cohort (`AUTO_MIGRATE`, `AUTO_SEED`, `SEED_DEMO_DATA` in `backend/.env`).

**Frontend**, in a second terminal from the project folder:

```bash
npm install
npm run dev        # http://localhost:5173; /api is forwarded to http://localhost:8000
```

To build for production:

```bash
npm run build      # output goes to dist/
npm run preview    # serves dist/ on http://localhost:4173
```

The app uses hash routes (`/#/oppe`). If the frontend and API are on different hosts, set `VITE_API_URL` (for example `https://api.example.com/api`) and add the frontend's address to `CORS_ORIGINS` in the backend.

## Deploy on Vercel (with Neon)

One Vercel project serves both parts: the built frontend from `dist/`, and the FastAPI backend as a Python function (`api/index.py`) for every `/api/...` request. Python packages come from `requirements.txt` at the project root.

1. **Create the database.** In [Neon](https://neon.tech) create a project and copy the **pooled** connection string (Dashboard → Connect, "Connection pooling" on; the host contains `-pooler`).
2. **Set up the tables and demo data once**, from your machine:

   ```bash
   cd backend
   # PowerShell:  $env:DATABASE_URL="postgresql://...-pooler...neon.tech/neondb?sslmode=require"
   DATABASE_URL="postgresql://...-pooler...neon.tech/neondb?sslmode=require" python -m app.bootstrap
   ```

   It applies the migrations and seeds the demo accounts and cohort. Running it again is safe. Do the same after adding a new migration.
3. **Import the repository in Vercel** (Add New… → Project). Leave the detected settings; `vercel.json` sets the Vite build, the `dist` folder and the Python function.
4. **Give the project the database URL**: either connect Neon under the project's **Storage** tab (Vercel then adds `POSTGRES_URL`, which the backend uses), or add `DATABASE_URL` (the pooled URL) under Settings → Environment Variables. Recommended: a `JWT_SECRET`. On Vercel the backend already defaults `USE_NULL_POOL=true`, `AUTO_MIGRATE=false` and `AUTO_SEED=false`; `.env.vercel` lists the rest. Optionally `VITE_GOOGLE_CLIENT_ID`.
5. **Deploy.** Every push to `main` redeploys. Check `https://<your-project>.vercel.app/api/health`: it answers `{"status":"ok", ...}` when the function can reach Neon, and names the problem otherwise (for example `"host": "localhost"` means no database URL is set).

If you use Google Calendar, add the Vercel URL to the OAuth client's **Authorised JavaScript origins**.

## Sign in

The app opens on the sign-in page. Pick a role, click a demo account to fill in the form, and press **Sign in**. Every demo account uses the password **`disha123`** (`DEMO_PASSWORD`). The sign-in page lists the accounts from `GET /api/auth/demo-accounts`; set `SHOW_DEMO_ACCOUNTS=false` to hide them. **Sign out** is at the bottom of the side menu (top right on a phone).

| Role | Email | Lands on | What you will see |
|---|---|---|---|
| Student | `ananya@disha.demo` | Student home | Low risk: study plan for Statistics II |
| Student | `rahul@disha.demo` | Student home | High risk: instructor support |
| Student | `karthik@disha.demo` | Student home | On track, Diploma |
| Support staff | `neha@disha.demo` | Staff overview | Her own caseload, follow-ups, interventions |
| Course instructor | `kavya@disha.demo` | My course | Students referred to Programming in Python, course totals |
| Administrator | `admin@disha.demo` | Staff overview | Everything: at-risk list, assigning, interventions, reports, data upload, rules, users, audit log |

Each role can open only its own pages. A student who types a staff address, or support staff who open the rules page, are sent back to their own home page, and the API refuses the request (403) whatever the browser does.

### The three demo students

| Student | Level | Situation | What you will see |
|---|---|---|---|
| Ananya Rao | Foundation, term 4 | Failed Statistics II once | **Low risk**: 12-week study plan for Statistics II, built from past students |
| Rahul Verma | Foundation, term 4 | Failed Programming in Python twice | **High risk**: instructor support with a weekly check-in; predicted score below the pass mark |
| Karthik Iyer | Diploma, term 3 | No failures | **On track**: course guides and predicted grades only |

## Features

| # | Feature | Where |
|---|---|---|
| 1 | CGPA and terms tracking: CGPA, term-by-term GPA chart, terms used out of the limit, milestones | **CGPA and terms** page; CGPA card and the route on **Home** |
| 2 | Chatbot that knows the student's data and the program rules | **Ask Disha** page; suggested questions on **Home** |
| 3 | Progress tracking for every student, with guidance after a failed course | **Courses** and each course page |
| 4 | Two risk levels: **High** (same course failed twice, instructor support) and **Low** (one course failed once, guidance from past students) | Status band on **Home**; course page |
| 5 | OPPE eligibility, with each condition and the student's own values | **OPPE eligibility** card on **Home**; **OPPE eligibility** page |
| 6 | Google Calendar integration: upcoming meetings on the dashboard | **Upcoming meetings** on **Home**; **Meetings** page |
| 7 | Chatbot replies in a fixed JSON format, checked before display | **View JSON** under every answer |
| 8 | **Today panel**: today's meetings at the top right of Home, with a live countdown and Join button | **Home**, top right |
| 9 | **Course guide** for every course this term: pass rate, hours a week that paid off, week-by-week workload, common slip-ups, what passing students did, resources | Course page, **Course guide** tab; "How others passed it" on **Home** |
| 10 | **Study plan** for a course failed once: 12 weeks of tick-off tasks, exam checkpoints, progress ring | Course page, **Study plan** tab; "Your study plan" on **Home** |
| 11 | **Predicted score**: expected final score and grade from graded assignments and quizzes so far, what is pulling it up or down, and a "what if" slider | Course page, **Overview** tab; predicted grade beside each course on **Home**; ask Disha "Will I pass my courses this term?" |
| 12 | **Sign-in with roles**: student, support staff, course instructor, administrator; each role sees only its own pages | `/#/login` |

### Staff portal

Staff see a demo cohort of **60 students**: the three demo students plus 57 generated ones. Every number comes from the same rules the student pages use (CGPA, milestones, risk, OPPE, prediction), so Rahul looks the same to staff as he does to himself.

| Feature | User story | Who | Where |
|---|---|---|---|
| Overview: KPI tiles with weekly trends, risk mix chart (with a split by level), where cases stand, caseload against capacity, students newly moved to High risk, at-risk students by week, courses with the most risk flags, follow-ups due, caseload by staff member, data and system health, today's meetings | US-04, US-07, US-13 | Admin, support | **Overview** |
| At-risk list sorted by urgency, with filters for risk, level, term and owner, the main reason, the model's predicted score, owner and case status | US-04 | Admin, support | **At-risk students** |
| Assign one or many students to a staff member, with a reason; capacity shown | US-07 | Admin | **At-risk students** (tick rows) and each profile (**Reassign**) |
| Student profile: risk reasons with the rule behind each, suggested actions labelled academic support, planning advice or administrative follow-up ("Mark shared"), route through the degree, this term's courses with predictions, course attempts, owner history | US-05 | Admin, support | Click any student |
| Log an intervention: call, email, meeting or referral, linked reason, notes, outcome and follow-up date, with checks before saving | US-06 | Admin, support | Student profile |
| Interventions board: follow-ups due and overdue (oldest first), every case by outcome, change an outcome from the card | US-06 | Admin, support | **Interventions** |
| Course view for instructors: only students referred to their course, record support offered, course totals by component | US-12 | Instructor | **My course** |
| Reports: time to first contact and to resolution, risk by term, outcomes by intervention type, top risk reasons, progress by level and admission cohort; totals only | US-11, US-13 | Admin | **Reports** |
| CSV upload with a template, row-by-row checks (row number and reason for each rejected row), confirm, then risk recalculation; import history and data freshness | US-09 | Admin | **Data and system** |
| System status and AI: imports, recalculations, alert batches, model version and accuracy, switch the language model off, flag sample messages | US-15 | Admin | **Data and system** |
| Risk and milestone rules: edit thresholds and milestones, check the effect (who would change level) before applying, version history with reasons | US-08 | Admin | **Rules and access** |
| Users and access: what each role can do, change a staff member's role, deactivate an account | US-14 | Admin | **Rules and access**, second tab |
| Audit log: every assignment, intervention, outcome, rule change, import, recalculation and setting, searchable by text, action, person and date; read only | US-10 | Admin | **Audit log** |

Try this as the administrator: assign Vikram Singh and Yash Jain (filter **Owner: No owner**), open Vikram and log a call, change the High-risk rule to 3 failed attempts and check the effect, import the sample file on **Data and system**, then see all of it in the **Audit log**.

### Pages

| Route | Page |
|---|---|
| `/#/` | Home: route through the degree, risk status, meetings, CGPA, OPPE eligibility, this term's courses |
| `/#/progress` | CGPA and terms |
| `/#/courses` | All courses, with filters |
| `/#/courses/:id` | One course, in tabs: **Overview** (instructor check-in, this term so far, predicted score, OPPE), **Course guide**, **Study plan** (failed once), **Attempts**. Open a tab directly with `?tab=guide` or `?tab=plan` |
| `/#/oppe` | OPPE eligibility in detail |
| `/#/meetings` | Google Calendar connection and upcoming meetings |
| `/#/ask` | Ask Disha chatbot |
| `/#/login` | Sign in |
| `/#/staff` | Staff overview (admin, support) |
| `/#/staff/students` | At-risk students; `?risk=high`, `?owner=none` and similar open it filtered |
| `/#/staff/students/:id` | Student profile for staff |
| `/#/staff/interventions` | Follow-ups and the interventions board |
| `/#/staff/course` | Course instructor's view |
| `/#/staff/reports` | Reports (admin) |
| `/#/staff/data` | Data upload and system status (admin) |
| `/#/staff/rules` | Rules, users and access (admin) |
| `/#/staff/audit` | Audit log (admin) |

### Risk rules

The rules live in `src/utils/progress.js` (`risk()`) and `src/data/rules.js`. They only consider courses the student has **not yet cleared**:

- **High risk**: the same course failed twice. The course page shows the instructor working with the student and the next check-in.
- **Low risk**: a course failed once. The course page shows how past students who failed it once went on to pass it, and a week-by-week plan.
- **On track**: no uncleared failed course.

## Connecting the real services

Copy `.env.example` to `.env` to set the frontend values, and `backend/.env.example` to `backend/.env` for the backend. Restart the servers afterwards.

```bash
# .env (frontend)
VITE_API_URL=                    # leave empty when the API is served at /api
VITE_GOOGLE_CLIENT_ID=1234567890-abc.apps.googleusercontent.com

# backend/.env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b         # empty = built-in replies
```

### Chatbot (feature 2 and 7)

The Ask Disha page first asks `GET /api/chat/status` whether a live model will answer. If so, it sends a POST request to `/api/chat`, and the backend passes it to Ollama with `format` set to the schema, so the model replies in it:

```json
{
  "system": "You are Disha, an assistant for students of the IITM BS degree...",
  "messages": [{ "role": "user", "content": "Am I eligible for my next OPPE?" }],
  "context": { "student": { "...": "..." }, "program_rules": { "...": "..." } },
  "response_schema": { "type": "object", "required": ["answer", "intent", "..."] }
}
```

The backend returns `{ "response": ... }` holding one JSON object in this shape:

```json
{
  "answer": "You are not eligible for OPPE 1 yet.",
  "intent": "oppe",
  "key_points": ["Assignment average 31, needs 40"],
  "actions": [{ "label": "Open OPPE eligibility", "route": "/oppe" }],
  "follow_up_questions": ["When is my next OPPE?"],
  "sources": [{ "title": "OPPE eligibility rules for your courses" }],
  "confidence": "high",
  "escalate_to_human": false
}
```

`RESPONSE_SCHEMA` in `src/services/chat.js` is the full JSON Schema. `validateResponse()` rejects replies that do not match it, and only allows in-app routes in action buttons.

When `OLLAMA_MODEL` is empty, or the administrator switches the language model off on **Data and system**, the backend answers 503 and a built-in responder answers common questions (CGPA, a target CGPA, OPPE eligibility, failed courses, terms and milestones, meetings, registration, weekly focus) from the demo student's data, in the same JSON format.

### Google Calendar (feature 6)

1. In Google Cloud Console, create a project and enable the **Google Calendar API**.
2. Create an **OAuth client ID** of type **Web application**. Add `http://localhost:5173` (and your deployed URL) under **Authorised JavaScript origins**.
3. Set up the OAuth consent screen, and add your team's Google accounts as test users.
4. Put the client ID in `VITE_GOOGLE_CLIENT_ID`.

The app signs in with Google Identity Services and asks for the read-only scope `calendar.readonly`. It then reads the next 30 days of events from the student's primary calendar, including the Meet link. It never writes to the calendar. Without a client ID, **Connect Google Calendar** simulates a connection with the sample meetings.

## Project structure

```
src/
  App.vue               shows the current layout
  main.js               app setup, fonts
  router/index.js       routes, and which roles may open each one
  layouts/
    StudentLayout.vue   student side menu (desktop), top bar and tab bar (phone)
    StaffLayout.vue     staff side menu, filtered by role
  stores/
    auth.js             demo sign-in and the signed-in user
    student.js          the signed-in student and everything worked out from it
    staff.js            staff data and actions: assign, log, outcomes, rules, imports, audit
  data/
    students.js         three sample students (grades, OPPEs, meetings, instructor support)
    courses.js          course catalogue
    rules.js            milestones, grade points, risk levels
    insights.js         what helped past students who failed once (sample figures)
    guides.js           course guides: how last term's students passed each course
    plans.js            12-week study plans for courses failed once
    schemes.js          grading weights per course and grade bands
    accounts.js         demo accounts and roles
    staff.js            staff members, permissions, staff meetings
    cohort.js           the 60-student demo cohort and its intervention history
    actions.js          suggested actions, intervention types and outcomes
  utils/
    progress.js         CGPA, course status, milestones, risk, OPPE eligibility
    predict.js          predicted final score, likely range and what moves it
    staff.js            risk with the admin's thresholds, reasons, staff summary per student
    csv.js              CSV parsing and row checks for uploads
    dates.js            date formatting and term arithmetic
  services/
    chat.js             chatbot: JSON schema, context, validation, built-in responder
    calendar.js         Google Calendar connection and events
  components/           RouteTrack, RiskPanel, TodayCard, PredictionCard, CourseGuide, StudyPlan, ...
    staff/              Kpi, KpiChart, Donut, Gauge, RiskChip, StackBar, TrendChart, Timeline, InterventionForm, Person
  views/                one file per student page, LoginView.vue
    staff/              one file per staff page
  styles/main.css       colours, type and shared styles
```

## Notes

- All names, grades, statistics and meetings are sample data.
- **How the prediction works (sample model):** parts already marked (weekly assignments, Quiz 1) count at the student's real score; a missed OPPE counts as 0; each part still to come is estimated from the assignment average and Quiz 1, adjusted by how last term's students with similar scores did. The likely range narrows as more results come in. In the full platform this comes from the backend's model; the grading weights in `schemes.js` are sample values.
- Study plan ticks are saved per student on the server (`/api/me/study-plan/:courseId`).
- **Sign-in:** the backend checks the email and password and issues a JWT (`JWT_SECRET`, `JWT_EXPIRE_MINUTES`); every endpoint checks the role again. Passwords are stored as plain text while `HASH_PASSWORDS=false`; set it to `true` before real use (existing passwords are upgraded to PBKDF2 at the next sign-in).
- Staff changes (assignments, interventions, outcomes, rules, imports, settings) are saved by the backend and written to the audit log.
- The interface is responsive from 360 px phones to wide screens, works with the keyboard, has visible focus outlines, and turns off motion for people who prefer reduced motion.
- The milestone and risk rules are stored in the database as versioned settings; the administrator edits them on **Rules and access**.
