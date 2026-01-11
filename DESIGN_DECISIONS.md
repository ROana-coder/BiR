# Key Design Decisions

Throughout the development process of the Literature Explorer, we made several strategic choices to balance academic accuracy with a modern user experience. This document outlines the rationale behind those decisions.

## 1. Genre Simplification
*   **The Challenge**: Wikidata contains thousands of granular genres (e.g., "Historical Novel", "Epistolary Novel", "Roman à clef") which can overwhelm users.
*   **Decision**: We implemented a strategy to **group details under broad categories**. For the quick filters and main search logic, we often rely on high-level entities (e.g., "Novel" - Q8261) or remove genre constraints entirely for broader searches (like "French Classics").
*   **Rationale**: This prevents the filter interface from becoming unmanageable and ensures that users find relevant works without needing to know specific Wikidata sub-classifications.

## 2. Performance: Manual vs. Auto-Search
*   **The Challenge**: SPARQL queries to Wikidata are computationally expensive and can take 1-2 seconds to return.
*   **Decision**: We switched from a "search-as-you-type" model to a **Manual Search Trigger** (user must click "SEARCH").
*   **Rationale**: This prevents the application from firing multiple expensive, lag-inducing requests while a user is still adjusting parameters (e.g., sliding a year range). It makes the UI feel more responsive and stable.

## 3. Graph Visualization: Visual Noise Reduction
*   **The Challenge**: Symmetric relationships (e.g., "Shared Movement") theoretically have arrows pointing in both directions (A -> B and B -> A), which doubled the number of edges and cluttered the graph.
*   **Decision**: We **removed bidirectional arrows** for these relationships.
*   **Rationale**: visually, a single line connecting two authors is sufficient to show they share a movement. Removing the duplicate reverse edge significantly cleans up the visualization without losing information.

## 4. Layout Stability
*   **The Challenge**: As lists of books or authors grew, they often caused the main browser window to scroll, which broke the "sticky" positioning of the sidebar and revealed unsightly background gaps ("black area bug").
*   **Decision**: We enforced a **Fixed 100vh Layout**.
*   **Rationale**: The entire app is pinned to the viewport height. The Sidebar and Main Content areas have their own independent internal scrolling (`overflow-y: auto`). This provides a polished, app-like feel that never breaks layout, regardless of list length.

## 5. Quick Filter Robustness
*   **The Challenge**: Specific combinations of filters (e.g., "Russian Realism" + "Novel" genre) sometimes returned zero results due to missing data tags on Wikidata.
*   **Decision**: For presets like **French Classics** and **Russian Realism**, we removed strict genre constraints or broadened year ranges.
*   **Rationale**: It is better to return a slightly broader set of accurate results (e.g., all Russian works 1850-1920) than to return nothing because a specific book wasn't tagged explicitly as a "Novel".
