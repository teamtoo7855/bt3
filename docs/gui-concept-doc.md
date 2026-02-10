# GUI Concept – Bus Transit Tracking Application

## Overview

The frontend GUI for this project was designed with a **map-first, commuter-focused approach**. The primary goal of the interface is to allow users to quickly and intuitively understand the current state of bus transit, including **bus locations, routes, ETAs, and vehicle information**, with minimal interaction and no unnecessary complexity.

The interface prioritizes clarity, speed, and ease of use, ensuring that commuters can access essential information at a glance without navigating multiple pages or menus.

## Design Philosophy

The GUI follows three core principles:

1. **Map-centric interaction** – The map is the main interface element, as geographic context is essential for transit planning.
2. **Minimal controls** – Only essential controls are exposed to avoid clutter and cognitive overload.
3. **Details on demand** – Advanced or detailed information is revealed only when the user interacts with a bus marker.

This ensures the UI remains approachable for first-time users while still supporting more detailed exploration.

## Main Interface Layout

![Main map interface with live bus markers](docs/basic-gui.md)

- The map occupies the majority of the screen and loads immediately on startup.
- Live bus locations are displayed as high-contrast markers, making them visible at both high and low zoom levels.
- Users can pan and zoom freely to explore nearby routes and bus activity.

**User requirement satisfied:**  
*As a commuter, I want to know the bus locations, so that I can plan my commute.*

## Route Filtering

- A single dropdown allows users to filter buses by route or view all routes simultaneously.
- Selecting a route reduces visual noise and helps users focus only on buses relevant to their commute.

**User requirement satisfied:**  
*As a commuter, I want to get information on buses and their routes, so that I can know what features the buses have.*

## Bus Information Popup

When a user clicks or taps on a bus marker, a popup appears displaying:

- Vehicle make and model
- Route number
- Direction of travel
- Current speed
- Time since last update

This transforms raw GTFS data into readable, user-friendly information.

**User requirements satisfied:**
- *As a commuter, I want to know the bus type, features, and size so that I can travel comfortably.*
- *As a commuter, I want to get all relevant bus data so that I can have accurate bus information.*

## ETA Lookup Interface, Stop and ETA Input

- Users can enter a stop ID and bus number to retrieve an estimated arrival time.
- The ETA is displayed in a concise and readable format (e.g., minutes until arrival).

This supports both casual users and commuters who prefer precise, stop-based planning.

**User requirement satisfied:**  
*As a commuter, I want to know the ETA for buses, so that I can plan my route accordingly.*

## Accessibility and Ease of Use

- The interface avoids complex navigation, logins, or multi-page flows.
- Controls are placed directly on the map for immediate access.
- Information is presented using plain language instead of technical identifiers.

This ensures the UI remains intuitive, even for users unfamiliar with transit APIs or data structures.

## Summary

The frontend GUI successfully fulfills the requirement to **conceptualize a basic frontend UI that is easy to use** by:

- Centering the experience around an interactive map
- Minimizing user interactions required to access key data
- Presenting transit information in a clear and readable format
- Supporting both visual exploration and direct ETA queries

Overall, the GUI serves as a clean and effective MVP frontend that aligns with commuter needs and project user stories while remaining simple, scalable, and easy to extend in future iterations.
