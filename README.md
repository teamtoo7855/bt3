# Bus Type Transit Tracker (bt3)

![Screenshot of bt3](https://github.com/teamtoo7855/bt3/blob/main/docs/screenshot.jpg?raw=true)

## Overview

bt3 is a web application that allows users to view bus routes and track live bus types and locations using real-time transit data. It integrates mapping, live vehicle feeds, and user preferences into a single interface.

## Quickstart

1. Install uv
   [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

2. Clone the repository

   ```bash
   git clone <repo-url>
   cd bt3
   ```

3. Set up environment variables

   ```bash
   cp .env.example .env
   ```

   Fill in your API keys.

4. Run the application

   ```bash
   uv run src/app.py
   ```

5. Open in browser

   ```
   http://localhost:8080
   ```


## Environment Variables

Create a `.env` file using the following template:

```env
MAPBOX_ACCESS_TOKEN=your_mapbox_key_here
TRANSLINK_API_KEY=your_translink_key_here
FIREBASE_APIKEY=your_secret_key_here
```


