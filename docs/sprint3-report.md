# Sprint 3 Report

- **Team Name:** Team 2
- **Sprint Dates:** March 3, 2026 - March 31, 2026
- **Sprint Board Link:** https://github.com/orgs/teamtoo7855/projects/1
- **GitHub Repository Link:** https://github.com/teamtoo7855/bt3.git

## 1. Sprint Board Screenshots
*Provide screenshots of your Sprint 3 board filtered by each team member.*
- **hi-im-vika:** ![Screenshot of hi-im-vika Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint3-board-filter-hi-im-vika.png?raw=true)
- **JCslam14:** ![Screenshot of JCslam14 Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint3-board-filter-JCslam14.png?raw=true)
- **fyemane:** ![Screenshot of fyemane Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint3-board-filter-fyemane.png?raw=true)
- **itsMegga:** ![Screenshot of itsMegga Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint3-board-filter-itsMegga.png?raw=true)

## 2. Sprint Review (Planned vs. Delivered)
*Review what you planned to accomplish this sprint versus what was actually completed. Focus on your architecture, testing, and UI goals.*

**Successfully Delivered:**
- Modularize code: Separate code based on labs and what made sense for the infrastructure developed already.
- Secure appropriate API endpoints with Flask decorators: used require_jwt to secure API endpoints
- Gracefully handle errors in UI: Replace debug error screens, 404 screens, etc. with nice UI notifications
- Implement rate limits on API: Limit maximum API requests to avoid overwhelming system/sending excess requests to Mapbox
- Implement input validation: Email field only accepts input that looks like user@example.tld, Password must be at least eight characters long, Don't allow invalid stop numbers to be added to a profile's favourite stop list
- Display information from Chart.js: Display pie chart with current bus types on a certain route
- Create structured testing suite: Built a pytest test suite in src/tests with organized files for authentication, API validation, auth route behavior, and reusable validation logic.
- Generate automated tests: Added automated tests for protected API behavior, bad request validation, auth page flows, stop list CRUD behavior, and validation helpers, and ran them locally with coverage reporting.


**Not Completed / Partially Completed:**
*Explain why these were not finished. (e.g., Underestimated complexity, spent more time writing quality tests for a single endpoint rather than rushing multiple endpoints, blockers with Mocking, etc.)*
- Optimize static data lookup: Scheduling conflict, apparently done but busy.
- Fix data types storedd per user profile: Scheduling conflict, apparently done but busy.
- Create Structured Testing Suite: [Reason]
- Generate Automated Tests: [Reason]


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
- **Current Code Coverage:** `71%`  
- **Mocked Components:** `firebase_admin.auth.verify_id_token`, Firestore (`db.collection`, `document`, `get`, `set`, `update` via in-memory mocks)

### Automated Testing & Coverage

We implemented a structured `pytest` test suite inside `src/tests` to verify authentication, API validation, and core route behavior. The test suite currently executes 41 tests in under a second, demonstrating that it is fast, automated, and suitable for continuous development.

A key goal of this sprint was to transition from manual testing (e.g., Postman) to automated testing. Our tests now cover:
- Protected API routes requiring authentication
- Invalid request handling (400 responses)
- Authentication flows (login, signup, token validation)
- Profile stop management endpoints (add, update, delete)
- Reusable validation utilities (email, password, input formats)

This ensures consistent behavior across both valid and invalid inputs.

### Mocking Strategy

To prevent reliance on external services, we mocked both Firebase authentication and Firestore:

- **Firebase Auth Mocking:**  
  We used `unittest.mock.patch` to mock `firebase_admin.auth.verify_id_token`. This allows us to simulate valid and invalid JWT tokens without making real network requests.

- **Firestore Mocking:**  
  We created fake Firestore classes in `conftest.py` that simulate:
  - `db.collection(...)`
  - `document(...)`
  - `get()`, `set()`, `update()`

  These mocks use in-memory Python dictionaries to mimic database behavior, ensuring that tests:
  - run without internet access  
  - do not modify real database data  
  - execute quickly and consistently  

### Coverage Analysis

We used `pytest --cov=src --cov-report=term-missing` to evaluate test coverage. Our current coverage is **71%**, with strong coverage in:
- Authentication decorators and token validation
- Auth route flows (login, signup, error handling)
- API validation logic (400 and 401 responses)
- Core backend logic for user profile operations

The coverage report highlights untested lines, allowing us to focus on meaningful logic such as edge cases and error handling instead of artificially increasing test count.

### Test Highlight (AAA + Parametrization)

```python
import pytest
from utils.validation import validate_email


@pytest.mark.parametrize(
    "email, expected",
    [
        ("test@example.com", True),
        ("student@bcit.ca", True),
        ("bademail", False),
        ("missingatsign.com", False),
        ("", False),
    ],
)
def test_validate_email(email, expected):
    result = validate_email(email)

    assert result == expected
```

**Explanation:**

**AAA Pattern:**
- **Arrange:** Define inputs and expected outputs using `@pytest.mark.parametrize`
- **Act:** Call `validate_email(email)`
- **Assert:** Verify the result matches the expected output

**Equivalence Partitioning:**
Instead of testing all possible inputs, we test representative groups:
- Valid emails  
- Invalid formats  
- Missing components  
- Empty input  

This ensures efficient and meaningful test coverage.
