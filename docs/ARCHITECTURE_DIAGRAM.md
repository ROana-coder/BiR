graph TD
    classDef client fill:#e3f2fd,stroke:#2196f3,stroke-width:2px;
    classDef frontend fill:#e0f2f1,stroke:#009688,stroke-width:2px;
    classDef backend fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px;
    classDef infra fill:#fff3e0,stroke:#ff9800,stroke-width:2px;
    classDef external fill:#ffebee,stroke:#f44336,stroke-width:2px;

    User(("👤 User")):::client
    Browser["🖥️ Client Browser"]:::client

    subgraph Cloud ["☁️ AWS Cloud (EC2)"]
        style Cloud fill:#f8f9fa,stroke:#ff9900,stroke-width:2px,stroke-dasharray: 5 5

        subgraph Infrastructure ["Infrastructure (Docker Compose)"]
            style Infrastructure fill:#ffffff,stroke:#2496ed,stroke-width:2px

            subgraph Frontend_App ["Frontend (React + Vite)"]
                Components["React Components<br/>(Sidebar, Graph, Map)"]:::frontend
                API_Client["API Client<br/>(TanStack Query + Axios)"]:::frontend
            end

            subgraph Backend_App ["Backend (FastAPI)"]
                Router["API Router<br/>(/search, /graph, /geo)"]:::backend
                ServiceLayer["Service Layer<br/>(Search, Graph, Geo)"]:::backend
                WikiClient["Wikidata Client<br/>(SPARQL Wrapper)"]:::backend
                Validator["🛡️ Data Validation<br/>(Pydantic / SHACL)"]:::backend
            end

            Redis[("🧠 Redis Cache<br/>(Cache-Aside)")]:::infra
        end
    end

    subgraph External_Web ["External Data"]
        Wikidata((("🌐 Wikidata<br/>Query Service"))):::external
    end

    User -->|Interacts| Browser
    Browser -->|HTTP Requests| Components
    Components -->|Hooks| API_Client
    API_Client -->|REST API| Router

    Router -->|Invoke Service| ServiceLayer
    ServiceLayer -->|1. Check Cache| Redis
    
    ServiceLayer -- Cache Miss --> WikiClient
    WikiClient -->|2. SPARQL Query| Wikidata
    Wikidata -- 3. Raw RDF --> WikiClient
    WikiClient -->|4. Parse| Validator
    Validator -->|5. Validated Objects| ServiceLayer
    ServiceLayer -->|6. Store Cache| Redis
    
    Redis -- Cache Hit --> ServiceLayer
    ServiceLayer -->|7. JSON Response| Router
    Router -->|Data| API_Client