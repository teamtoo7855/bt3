# Sprint 3 Design

## Modularization Strategy: 
The code is being modularized into blueprints (api, auth, dashboard, data_geojson, and profile) with init and routes files. The code that pulls static data is stored in a utils directory where it can be imported into the proper blueprints. A validation file is used to check that proper user info is implemented and imported to respective, relevant blueprints. All is merged in an app file. Config and firebase files are also complementary for access and verification. Blueprints improve organization/maintainability and scalability, utils centralizes shared logic, and validation creates consistency across endpoints.

## SSR and CSR Breakdown: 
Our app will mainly use CSR:
- /login should post data to /api/login and return a JWT on successful login, which is handled by client-side JS and stored in localStorage.
- /profile should make a request to /api/profile for the logged in user's information, identified by their JWT
- Signup page should be at /signup and post data to /api/signup
- JS in the default map view should query from and send updates to /api/profile when favourites are read or changed
- Clearly define which parts of your application are rendered by the server (Flask or Jinja templates) and which parts are rendered or updated by the client (JavaScript and DOM manipulation).
- this is addressed in issue [#57](https://github.com/teamtoo7855/bt3/issues/57)
SSR is mainly for base templates.

## Security measure: 
So far only input validation is being implemented for security checks. This would be for things such as preventing malformed data and injection and password hashing. JWT verification for api is also used for protection.

