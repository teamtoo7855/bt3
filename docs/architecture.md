# Architecture - Bus Analysis and Live Location System BALLS

This document defines the system boundary, major components, architectural pattern, and key flows for BALLS.

---

## 1 Context Diagram

```mermaid
flowchart LR
  U[Users]
  T[TransLink GTFS Real Time API]
  R[User Reports]
  N[Notification Provider]

  SYS[Bus Analysis and Live Location System BALLS]

  U -->|Route selections and preferences| SYS
  SYS -->|ETA bus info and alerts| U

  T -->|Schedules routes stops vehicles delays| SYS
  SYS -->|Data requests| T

  R -->|Delay disruption reports| SYS
  SYS -->|Report confirmations| R

  SYS -->|Alert payloads| N
  N -->|Notifications| U
```

## 2 Component Diagram

```mermaid
flowchart TB
  subgraph ClientApps[Client Apps]
    WebUI[Web UI]
    MobileUI[Mobile UI]
  end

  subgraph Backend[Backend Server]
    APIGW[API Gateway]
    Aggregator[Data Aggregator]
    ETAEngine[ETA and Delay Engine]
    BusResolver[Bus Type Feature Resolver]
    ReportService[User Report Service]
    AlertService[Alert Orchestrator]
  end

  subgraph DataLayer[Data Layer]
    Cache[(Cache)]
    DB[(Database)]
  end

  subgraph ExternalSystems[External Systems]
    TransLink[TransLink Data API]
    Notif[Notification Provider]
  end

  WebUI -->|HTTPS| APIGW
  MobileUI -->|HTTPS| APIGW

  APIGW --> Aggregator
  APIGW --> ETAEngine
  APIGW --> BusResolver
  APIGW --> ReportService
  APIGW --> AlertService

  Aggregator -->|Fetch updates| TransLink
  Aggregator --> Cache
  Aggregator --> DB

  ETAEngine --> Cache
  ETAEngine --> DB

  BusResolver --> DB

  ReportService --> DB
  ReportService --> AlertService

  AlertService --> Notif
  AlertService --> DB

```

## 3 Sequence Diagram

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant API as Backend API
  participant Agg as Aggregator
  participant ETA as ETA Engine
  participant DB as Data Store
  participant TL as TransLink API
  participant N as Notification Provider

  U->>C: Select route and stop
  C->>API: GET route stop status
  API->>DB: Read cached data
  DB-->>API: Cache result

  alt Cache stale or missing
    API->>Agg: Refresh data
    Agg->>TL: GET real time updates
    TL-->>Agg: Vehicle positions and delays
    Agg->>DB: Store normalized updates
  end

  API->>ETA: Compute ETA and delay flags
  ETA->>DB: Read latest schedule and real time
  DB-->>ETA: Data returned
  ETA-->>API: ETA results and alert flags

  API-->>C: 200 OK ETA bus info alerts
  C-->>U: Show results

  opt Alerts enabled
    API->>N: Send notification
    N-->>U: Notification delivered
  end
```

## 4 Architectural Pattern Justification
Architectural Pattern: Client–Server with Layered Architecture

The Bus Analysis & Live Location System (BALLS) follows a Client–Server architecture combined with a layered design. This pattern cleanly separates concerns between the user interface, application logic, and data access, making the system easier to develop, maintain, and scale.

The client layer (web or mobile frontend) is responsible solely for presenting information to users, such as bus routes and live location updates. It communicates with the server layer via well-defined API endpoints, ensuring the frontend remains decoupled from backend implementation details. The backend layer contains the core business logic, including processing live transit data, caching frequently updated locations, and coordinating data from external APIs. A data layer persists route information and metadata while improving performance and reliability.

This architectural choice fits the project well because real-time bus tracking requires frequent data updates, controlled access to external APIs, and predictable response times. By isolating the data-fetching logic in the backend, the system can efficiently manage caching strategies and reduce unnecessary calls to the transit data provider.

The primary trade-off is increased complexity compared to a monolithic or single-tier application. Additional layers introduce more components to manage and deploy. However, this complexity is justified by the improved scalability, testability, and flexibility, which is especially important if future features such as user accounts, notifications, or analytics are added.
