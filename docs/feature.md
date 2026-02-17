# Feature Description
A user of this application will have certain preferences based on their transit frequency and their general visual and practical app habits. Due to this problem, users need a way of making and managing personal profiles for the purposes of maintaining relevant data and avoiding refilling the same info everytime they use the bt3 application. That's what this feature aims to do.

# Inputs
1. **HTTP Methods (POST, GET, etc.)**
2. **Endpoint path**
3. **Request format (JSON), could consist of the following info:**
- Username (required)
- Password (required)
- Most often used bus route
- Preferred bus type
- Most frequented locations

# Outputs
1. **Success and Error Responses**
2. **HTTP Status codes**

# Data Stored in Firestore
1. **Collection name**
2. **Document**
3. **Fields**
- Data stored in Firestore will be a user's preferences, these would consist of favourite bus types, best routes, light/dark mode, and any other relevant info that might better the user experience with the goal of improving a transit users experience.

# Short End-to-End Flow Description
1. **Client sends HTTP method**
2. **Flask validates**
3. **Data written to Firestore**
4. **Firestore returns confirmed reception(?)**
5. **Send back JSON reponse to client(?)**
