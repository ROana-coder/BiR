# Literature Explorer

**A Big Data Retriever & Visualization Platform for the "Literature Explorer"**

> Built for the "Big Data Retriever" assignment: A microservice-based platform to intelligently query, visualize, and recommend literary resources using Wikidata.

Literature Explorer is a sophisticated web application that enables users to explore global literary networks, visualize author migrations, and discover connections between literary movements across time and space.

---

## 🚀 Key Features

*   **Intelligent Knowledge Retrieval**: Dynamically queries [Wikidata](https://www.wikidata.org/) using optimized SPARQL templates to fetch high-fidelity data about authors, books, and literary movements.
*   **Interactive Visualizations**:
    *   **🗺️ Map View**: Dual-layer geospatial visualization showing **Author Birthplaces** (Red Pins) and **Narrative Locations** (Blue Pins) to contrast where authors lived vs. where their stories are set.
    *   **🔗 Network Graph**: Force-directed graph revealing influence networks and shared stylistic movements.
    *   **📅 Timeline**: Interactive timeline of literary publications to identify historical trends.
*   **Faceted Search**: Filter large datasets by Nationality, Genre, and Time Period.
*   **Smart Recommendations**: Suggests similar authors based on shared movements, genres, and eras using Jaccard similarity indices.
*   **Resilient Architecture**:
    *   **Caching**: Redis-based "Cache-Aside" strategy to handle Wikidata API limits and improve latency.
    *   **Microservices**: Modular FastAPI backend and React frontend.
    *   **Robustness**: Exponential backoff retry logic for 3rd party API stability.

---

## 🏛️ Use Cases Implemented

### 1. The "Lost Generation" & Transatlantic Modernism
**Goal**: Visualize the influence of American expatriate writers in Europe.
*   **Visual Proof**: The Map View highlights a cluster of **Birthplaces** in the USA (Midwest/East Coast) while the **Narrative Locations** and biography centers shift to Paris, London, and Spain.

### 2. Magic Realism: A Global Phenomenon
**Goal**: Trace the spread of a specific genre beyond its Latin American roots.
*   **Visual Proof**: Selecting the "Magic Realism" preset reveals a dense network of Latin American authors (García Márquez, Allende) connected to global authors (Murakami, Rushdie), visualizing cross-cultural literary influence.

---

## 🛠️ Technology Stack

*   **Backend**: Python, FastAPI, SPARQLWrapper, NetworkX
*   **Frontend**: React, TypeScript, Vite, D3.js, React-Leaflet
*   **Data**: Wikidata (SPARQL Endpoint)
*   **Infrastructure**: Docker, Docker Compose, Redis

---

## 📦 Getting Started

### Prerequisites
*   Docker & Docker Compose

### Installation & Run

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd Literature-Explorer
    ```

2.  **Launch with Docker Compose** (Recommended)
    This builds the frontend, backend, and Redis cache containers.
    ```bash
    docker-compose up --build
    ```

3.  **Access the Application**
    *   **Frontend**: [http://localhost:5173](http://localhost:5173)
    *   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## 📂 Project Structure

```
├── backend/            # FastAPI Microservice
│   ├── app/
│   │   ├── routers/    # API Endpoints (Graph, Geo, Search)
│   │   ├── services/   # Business Logic & Wikidata Client
│   │   ├── sparql/     # Optimized SPARQL Templates
│   │   └── models/     # Data Models
├── frontend/           # React Application
│   ├── src/
│   │   ├── components/ # Visualization Components (Map, Graph)
│   │   ├── api/        # Axios Client
│   │   └── types/      # TypeScript Definitions
└── docker-compose.yml  # Container Orchestration
```

---