# Sprint 3 Design

## Modularization Strategy: 
A brief explanation of how you are splitting up your code (e.g., routes, services, data access). Note: For groups that have already modularized their code, use this section to document your existing architecture and detail any further refinements or strict separation of concerns you plan to implement this sprint.


## SSR and CSR Breakdown: 
Our app will mainly use CSR:
- /login should post data to /api/login and return a JWT on successful login, which is handled by client-side JS and stored in localStorage.
- /profile should make a request to /api/profile for the logged in user's information, identified by their JWT
- Signup page should be at /signup and post data to /api/signup
- JS in the default map view should query from and send updates to /api/profile when favourites are read or changed
- Clearly define which parts of your application are rendered by the server (Flask or Jinja templates) and which parts are rendered or updated by the client (JavaScript and DOM manipulation).
- this is addressed in issue [#57](https://github.com/teamtoo7855/bt3/issues/57)

## Security measure (e.g., Input Validation & Query Limits): 
Explain your approach to security measures and how you are implementing them
