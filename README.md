# bt3
Bus Type Transit Tracker (bt3)
## Project Overview
bt3 is an app that allows users to view bus routes and track live bus locations using real-time transit data.
## Architecture Summary
The system follows a Client–Server architecture with layered components. The frontend communicates with a backend API that processes live bus data from external transit services. Caching and persistent storage are used to improve performance and reliability. Detailed architectural diagrams and justifications can be found in `docs/architecture.md`.
## Requirements
uv is needed to run this project. Get it from [here](https://docs.astral.sh/uv/getting-started/installation/).
### API Keys
You will also need to obtain your own Mapbox and Translink API keys.
- [Mapbox Registration](https://account.mapbox.com/auth/signup/)
- [Translink Open API Registration](https://www.translink.ca/about-us/doing-business-with-translink/app-developer-resources/register)

Once you have your API keys, make copy `keys.sample.py` to `keys.py` and fill in the blanks with your keys.
#### Warning
Do not expose this server to the internet. As of now, the API keys imported are exposed in the rendered webpage source and will be addressed later.
## Usage
### Windows
Run `bootstrap.ps1`. The webserver is accessible at `localhost:8080`.
### Linux
Run `bootstrap.sh`. The webserver is accessible at `localhost:8080`.
