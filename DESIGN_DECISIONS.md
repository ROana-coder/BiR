# Key Design Decisions

Throughout the development process of the Literature Explorer, I made several strategic choices to balance academic accuracy with a modern user experience. This document outlines the rationale behind those decisions.

## 1. Genre Simplification
*   **The Challenge**: Wikidata contains thousands of granular genres (e.g., "Historical Novel", "Epistolary Novel", "Roman à clef") which can overwhelm users.
*   **Decision**: I implemented a strategy to **group details under broad categories**. For the quick filters and main search logic, I often rely on high-level entities (e.g., "Novel" - Q8261) or remove genre constraints entirely for broader searches (like "French Classics").
*   **Rationale**: This prevents the filter interface from becoming unmanageable and ensures that users find relevant works without needing to know specific Wikidata sub-classifications.

## 2. Performance: Manual vs. Auto-Search
*   **The Challenge**: SPARQL queries to Wikidata are computationally expensive and can take 1-2 seconds to return.
*   **Decision**: I switched from a "search-as-you-type" model to a **Manual Search Trigger** (user must click "SEARCH").
*   **Rationale**: This prevents the application from firing multiple expensive, lag-inducing requests while a user is still adjusting parameters (e.g., sliding a year range). It makes the UI feel more responsive and stable.

## 3. Graph Visualization: Visual Noise Reduction
*   **The Challenge**: Symmetric relationships (e.g., "Shared Movement") theoretically have arrows pointing in both directions (A -> B and B -> A), which doubled the number of edges and cluttered the graph.
*   **Decision**: I **removed bidirectional arrows** for these relationships.
*   **Rationale**: visually, a single line connecting two authors is sufficient to show they share a movement. Removing the duplicate reverse edge significantly cleans up the visualization without losing information.

## 4. Layout Stability
*   **The Challenge**: As lists of books or authors grew, they often caused the main browser window to scroll, which broke the "sticky" positioning of the sidebar and revealed unsightly background gaps ("black area bug").
*   **Decision**: I enforced a **Fixed 100vh Layout**.
*   **Rationale**: The entire app is pinned to the viewport height. The Sidebar and Main Content areas have their own independent internal scrolling (`overflow-y: auto`). This provides a polished, app-like feel that never breaks layout, regardless of list length.

## 5. Quick Filter Robustness
*   **The Challenge**: Specific combinations of filters (e.g., "Russian Realism" + "Novel" genre) sometimes returned zero results due to missing data tags on Wikidata.
*   **Decision**: For presets like **French Classics** and **Russian Realism**, I removed strict genre constraints or broadened year ranges.
*   **Rationale**: It is better to return a slightly broader set of accurate results (e.g., all Russian works 1850-1920) than to return nothing because a specific book wasn't tagged explicitly as a "Novel".

## 6. Cloud Deployment & Data Reliability
*   **The Challenge**: The application worked perfectly on `localhost` but failed silently (0 results or crashes) when deployed to AWS.
    1.  **Backend Blocking**: Wikidata blocked requests from the AWS IP because the default Python User-Agent is flagged as a bot.
    2.  **Frontend Crashes**: The frontend blindly expected arrays, but the blocked backend returned error objects (JSON), causing `map is not a function` crashes.
    3.  **Proxy Routing**: Caddy's `try_files` directive (for SPA support) was inadvertently hijacking API requests, serving HTML instead of JSON.
    4.  **"Poisoned" Cache**: Browsers cached the initial failed responses (304), making it appear as if fixes weren't working even after the server was repaired.
*   **Decisions**:
    *   **Polite Identity**: I implemented a custom `User-Agent` header (`RepublicOfLetters/1.0...`) to identify the app as a legitimate research tool, bypassing the block.
    *   **Defensive Coding**: I wrapped all frontend data processing in strict `Array.isArray()` checks to prevent crashes regardless of API status.
    *   **Strict Routing**: I re-architected the `Caddyfile` to use mutually exclusive `handle` blocks, ensuring API traffic and Frontend traffic never overlap.
    *   **Custom Domain**: I migrated from a raw IP deployment to a custom domain (`literature-explorer.xyz`) to enable purely automatic HTTPS via Caddy/Let's Encrypt. This eliminated browser security warnings and "Mixed Content" blocking that plagued the raw IP version.
*   **Rationale**: Reliability in production requires assuming the "happy path" will fail. By strictly separating routing concerns, identifying myself politely to external APIs, and securing the transport layer with a real domain, I ensured the cloud environment behaves identically to the local development environment.
