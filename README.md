# bt3
Bus Type Transit Tracker
## Project Overview
The Bus Analysis & Live Location System (BALLS) allows users to view bus routes and track live bus locations using real-time transit data.
## Architecture Summary
The system follows a Client–Server architecture with layered components. The frontend communicates with a backend API that processes live bus data from external transit services. Caching and persistent storage are used to improve performance and reliability. Detailed architectural diagrams and justifications can be found in `docs/architecture.md`.
## Requirements
uv is needed to run this project. Get it from [here](https://docs.astral.sh/uv/getting-started/installation/).
## Usage
### Windows
Run `bootstrap.ps1`. The webserver is accessible at `localhost:8080`.
### Linux
Run `bootstrap.sh`. The webserver is accessible at `localhost:8080`.
