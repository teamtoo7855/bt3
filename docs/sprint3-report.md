# Sprint 3 Report

- **Team Name:** Team 2
- **Sprint Dates:** March 3, 2026 - March 24, 2026
- **Sprint Board Link:** [[Link]  ](https://github.com/teamtoo7855/bt3.git)
- **GitHub Repository Link:** https://github.com/teamtoo7855/bt3.git

## 1. Sprint Board Screenshots
*Provide screenshots of your Sprint 3 board filtered by each team member.*
- **hi-im-vika:** `images/sprint3-board-[member1].png`
- **JCslam14:** `images/sprint3-board-[member2].png`
- **fyemane:** `images/sprint3-board-[member1].png`
- **itsMegga:** `images/sprint3-board-[member2].png`

## 2. Sprint Review (Planned vs. Delivered)
*Review what you planned to accomplish this sprint versus what was actually completed. Focus on your architecture, testing, and UI goals.*

**Successfully Delivered:**
- Modularize code: Separate code based on labs and what made sense for the infrastructure developed already.
- Secure appropriate API endpoints with Flask decorators: used require_jwt to secure API endpoints
- Gracefully handle errors in UI: Replace debug error screens, 404 screens, etc. with nice UI notifications
- Implement rate limits on API: Limit maximum API requests to avoid overwhelming system/sending excess requests to Mapbox
- Implement input validation: Email field only accepts input that looks like user@example.tld, Password must be at least eight characters long, Don't allow invalid stop numbers to be added to a profile's favourite stop list
- Display information from Chart.js: Display pie chart with current bus types on a certain route


**Not Completed / Partially Completed:**
*Explain why these were not finished. (e.g., Underestimated complexity, spent more time writing quality tests for a single endpoint rather than rushing multiple endpoints, blockers with Mocking, etc.)*
- Optimize static data lookup: [Reason]
- Fix data types storedd per user profile: [Reason]
- Create Structured Testing Suite: [Reason]
- Generate Automatedd Tests: [Reason]
- Properly implement CSR: [Reason]

## 3. Architecture & UI Strategy
**Code Modularization:**  
The code is being modularized into blueprints (api, auth, dashboard, data_geojson, and profile) with init and routes files.
The code that pulls static data is stored in a utils directory where it can be imported into the proper blueprints. 
A validation file is used to check that proper user info is implemented and imported to respective, relevant blueprints. 
All is merged in an app file. Config and firebase files are also complementary for access and verification. 
Blueprints improve organization/maintainability and scalability, utils centralizes shared logic, and validation creates consistency across endpoints.

**SSR + CSR Breakdown:**  
- **Server-Side (Flask):** Flask renders base templates, firebase infrastructure, and validation [What does Flask render? e.g., Base templates, initial layout]
- **Client-Side (JS):** JS handles fetching and generating mapbox data, generating customized .html screens, and (updating Chart.js?) [What does JS handle? e.g., Fetching sensor data, updating Chart.js]

## 4. Automated Testing & Coverage
- **Testing Framework:** `pytest`
- **Current Code Coverage:** [%]
- **Mocked Components:** [List what was mocked, e.g., `verify_id_token`, Firestore]

**Test Highlight:**
```python
# Paste ONE test here that demonstrates the AAA pattern and Mocking/Parametrization
