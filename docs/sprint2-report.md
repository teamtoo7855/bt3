# Sprint 2 Report

**Format:** Add the markdown (`docs/sprint2-report.md`) to your repo and submit the PDF to Learning Hub  
**Purpose:** This report is a **written companion** to your live demo. It summarizes **what you planned**, **what you delivered**, and **what you learned**.

---

## 1. Sprint Overview

- **Your Team Name:** Team 2
- **Sprint 2 Dates:** Feb 10, 2026 -> March 3, 2026
- **Sprint Goal:** Implement feature X with **Firestore persistence** and **basic validation**.*

---

## 2. Sprint Board

**Sprint Board Link:** https://github.com/teamtoo7855/bt3.git  
**GitHub Repository Link:** https://github.com/teamtoo7855/bt3.git

---

### 2.1 Sprint Board Screenshot (Filtered by Team Member)

**Please provide a screenshot of your Sprint 2 board** (e.g., Trello, GitHub Projects) **filtered by each team member**. This makes the review concrete and shows shared ownership.

- **fyemane Board Screenshot:**
  ![Screenshot of fyemane Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint2-board-filter-fyemane.png?raw=true)
  
- **hi-im-vika Board Screenshot:**  
  `images/sprint2-board-filter-[member-name-2].png`

- **itsMegga Board Screenshot:**  
  ![Screenshot of fyemane Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint2-board-filter-itsMegga.png?raw=true)
  
- **JCslam14 Board Screenshot:**  
  ![Screenshot of fyemane Board](https://github.com/teamtoo7855/bt3/blob/main/docs/images/sprint2-board-filter-JCslam14.png?raw=true)

### 2.2 Completed vs. Not Completed (Feature-Focused)

Based on what you **plan** vs. what you **demoed**, summarize the state of your feature.

**Completed in Sprint 2 (Feature)**

- [ ] **Client** can trigger the feature and send input (e.g., POST `/feature`)
- [ ] **Server** exposes the endpoint with basic validation
- [ ] **Firestore** integration: data is written to the database
- [ ] **Server** can retrieve the stored data (GET from Firestore)
- [ ] **Basic Testing**: at least one test covering an error-free path (or a validation test)
- [ ] **Security/Secrets**: credentials are not committed; `.gitignore` excludes sensitive files (`keys.py`, `serviceAccountKey.json`, `.env`)
- [ ] **UI page**: app purpose influenced UI webpage designed

**Not Completed / Partially Completed**

- [ ] **Full UI web overlay**: massively underestimated complexity

---

## 3. Technical Summary: What Was Implemented
This is a **short technical summary** of the **end-to-end feature** you built.

1. **Feature:** profile storage 
    - **Collection:** profile
    - **What it does:** stores login information and preferrences related to the bus tracking application. These preferences are to be saved and grabbed from in the future when more UI functionality is implemented.
  
2. **Feature:** local storage for static data
    - **Collection:** N/A (data not stored on Firestore)
    - **What it does:** on app start, retrieves latest GTFS static data archive from TransLink and stores it in an SQLite database for quick retrieval. Additionally, tests have been written in Postman to ensure that retrieving, for example, bus stop information is faster than before.
### Data Model (Firestore)

- **Document shape (Collection: profile):**  
  Example JSON that represents **one document** in the collection (or the schema you structured):

  ```json
  {
    "created": 1772574201.8982875,
            "email": "secondnew@example.com",
            "prefs": {
                "favorite_bus_types": "Electric",
                "favorite_routes": "555,130,25,152",
                "favorite_stops": "51542,58438",
                "theme": "Dark",
                "alerts": true
            }
  }
  ```

  **Why this structure?**
  We wanted to establish an account for login purposes and preference based, the login purpose keys/values are those not within preferences. All data within preferences is prospective info that we think could be used for UI improvment. 

- **Input (Client → Server):**  
  Example JSON the client sends:

  ```json
  {
    "name": "New Feature",
    "status": "pending"
  }
  ```

- **Output (Server → Client):**  
  Example response the client receives after a successful create or read:

  ```json
  {
    "id": "generated-id",
    "userId": "firebase-uid",
    "name": "New Feature",
    "status": "pending",
    "createdAt": "2026-01-01T12:00:00.000Z"
  }
  ```

---

## 4. End-to-End Flow (What Was Demoed)

Give a **high-level, end-to-end description** of the feature flow you demonstrated. This is the same flow you walked through in the demo, in written form.

1. **Client** sends a request to the server (e.g., POST `/feature`) with a valid **payload** (JSON).
2. **Server** validates the input and **requires authentication** (JWT verification via Firebase Admin).
3. **Server** creates or updates a document in **Firestore**, storing it under a collection (e.g., `/features`).
4. **Client** receives a response (e.g., 201 or 200) with the stored data.
5. **Client** requests the data (e.g., GET `/feature/:id`) and the server reads the document **specifically** from Firestore.
6. **Server** returns the data to the client.

**Bounded Read:** In Sprint 2, you were required to demonstrate a **bounded read** (e.g., `.limit()`, `.where()`, or pagination). Describe what you implemented:

- **What you did:** [e.g., “We used Firestore `.limit(10)` to fetch a maximum of 10 items per request.”]
- **Why this matters:** [e.g., “This prevents unbounded scans, protects cost, and improves performance as data grows.”]

---

## 5. Sprint Retrospective: What We Learned

### 5.1 What Went Well

- Item 1: We got API endpoints working faster than expected
- Item 2: We got security checking working well
- Item 3: We got Firestore framework up and working quickly

### 5.2 What Didn’t Go Well

- Item 1: We didn't organize tasks well
- Item 2: We didn't organize our time well
- Item 3: We didn't coordinate with each other well

### 5.3 Key Takeaways & Sprint 3 Actions

| Issue / Challenge | What We Learned | Action for Sprint 3 |
|---|---|---|
| Task organization | Tasks should be discussed at the start of the sprint (in person preferrably) | Establish upcoming tasks before sprints so that there is no confusion amongst individuals |
| Time organization | Timelines should have a general start and due date to ensure no significant lagging | Address what tasks may be dependent on others |
| Team coordination | Communication should be more clear when involving the possible overlap of tasks | Address possible conflicts of tasks when coming across or noticing ahead of time (some research for tasks might lead to someone overstepping their bounds in tasks) |

---

## 6. Sprint 3 Preview

Based on what we accomplished (and what we didn’t), here are the **next Sprint 3 priorities**:

- **Priority 1**: Add user authentication and authorization so users can only access/modify their own feature data.
- **Priority 2**: Implement bus route visualization with conjunction with stop favoriting
- **Priority 3**: Add 3D models of bus to allow easy identification of bus type and size
