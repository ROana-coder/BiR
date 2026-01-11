# Documentație Serviciu Ontologie - Literature Explorer

## Prezentare Generală

Serviciul de ontologie permite stocarea și interogarea datelor despre literatură într-un format standardizat RDF (Resource Description Framework), folosind biblioteca **RDFLib** pentru Python.

---

## Rolul Ontologiei în Arhitectura Sistemului

### Două Surse de Date

Literature Explorer utilizează **două surse de date complementare**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LITERATURE EXPLORER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │   WIKIDATA (Live)   │         │  ONTOLOGIE LOCALĂ   │           │
│  │                     │         │   (literature.ttl)  │           │
│  │  • Date reale       │         │                     │           │
│  │  • Milioane entități│         │  • Schema/Model     │           │
│  │  • Actualizat       │         │  • Date exemplu     │           │
│  │  • Latență network  │         │  • Definții clase   │           │
│  └──────────┬──────────┘         └──────────┬──────────┘           │
│             │                               │                       │
│             ▼                               ▼                       │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │   WikidataClient    │         │  OntologyService    │           │
│  │   SearchService     │         │                     │           │
│  │   GraphService      │         │                     │           │
│  │   GeoService        │         │                     │           │
│  └──────────┬──────────┘         └──────────┬──────────┘           │
│             │                               │                       │
│             └───────────────┬───────────────┘                       │
│                             ▼                                       │
│                    ┌─────────────────┐                              │
│                    │    FastAPI      │                              │
│                    │   (Routers)     │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
│                             ▼                                       │
│                    ┌─────────────────┐                              │
│                    │    Frontend     │                              │
│                    │    (React)      │                              │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

**De ce două surse de date?**
> 1. **Wikidata** oferă date reale, actualizate, despre milioane de autori și opere
> 2. **Ontologia locală** definește schema (structura) și oferă un subset de date pentru dezvoltare/testare
> 3. Separarea permite lucrul offline și testare fără dependență de servicii externe

---

### Ce Face Fiecare Serviciu

| Serviciu | Sursă Date | Rol |
|----------|------------|-----|
| `WikidataClient` | Wikidata SPARQL Endpoint | Execută query-uri SPARQL către Wikidata |
| `SearchService` | Wikidata (prin WikidataClient) | Caută cărți și autori cu filtre |
| `GraphService` | Wikidata (prin WikidataClient) | Construiește graful de influențe |
| `GeoService` | Wikidata (prin WikidataClient) | Obține locații pentru hartă |
| `CacheService` | Redis | Cache pentru rezultate Wikidata |
| **`OntologyService`** | **literature.ttl (local)** | **Interogări pe ontologia locală** |

**De ce OntologyService este separat?**
> OntologyService operează pe date locale (fișierul TTL), nu pe Wikidata. Aceasta permite:
> - Definirea propriei scheme de date (clase, proprietăți)
> - Testare izolată fără network
> - Interogări rapide pe date statice

---

### Rolurile Ontologiei

#### 1. **Definiția Schemei (TBox)**

Ontologia definește **ce tipuri de entități există** și **ce proprietăți au**:

```turtle
# CLASE (tipuri de entități)
:Author a owl:Class ;
    rdfs:label "Author"@en ;
    owl:equivalentClass wd:Q482980 .  # Legătură cu Wikidata

:LiteraryWork a owl:Class ;
    rdfs:subClassOf schema:CreativeWork .

# PROPRIETĂȚI (relații)
:influencedBy a owl:ObjectProperty ;
    rdfs:domain :Author ;
    rdfs:range :Author ;
    owl:equivalentProperty wdt:P737 .  # = P737 în Wikidata
```

**De ce avem nevoie de schemă?**
> Schema definește regulile: "Un autor poate fi influențat de alt autor" (nu de o carte). Aceasta asigură consistența datelor și permite validare.

#### 2. **Date Exemplu (ABox)**

Ontologia conține și **instanțe concrete** pentru testare:

```turtle
:Hemingway a :Author ;
    :name "Ernest Hemingway" ;
    :birthDate "1899-07-21"^^xsd:date ;
    :influencedBy :Gertrude_Stein .

:TheOldManAndTheSea a :Novel ;
    :title "The Old Man and the Sea" ;
    :writtenBy :Hemingway .
```

**De ce date exemplu în ontologie?**
> Permit testarea aplicației fără a interoga Wikidata. Dezvoltatorii pot lucra offline și pot verifica că query-urile funcționează corect.

#### 3. **Mapare către Wikidata**

Ontologia creează echivalențe cu Wikidata:

```turtle
:Author owl:equivalentClass wd:Q482980 .
:influencedBy owl:equivalentProperty wdt:P737 .
:Hemingway owl:sameAs wd:Q23434 .
```

**De ce mapare?**
> Permite interoperabilitate. Un sistem extern poate înțelege că `:Author` din ontologia noastră este același concept ca `Q482980` din Wikidata.

---

## Fluxul de Date: Scenarii Concrete

### Scenariul 1: Căutare Cărți (folosește Wikidata)

```
┌─────────┐    GET /search?country=Q30&genre=Q24925
│ Browser │ ─────────────────────────────────────────────▶
└────┬────┘
     │
     ▼
┌─────────────────┐
│  search.py      │  ← Router FastAPI
│  (router)       │
└────────┬────────┘
         │ apelează
         ▼
┌─────────────────┐
│ SearchService   │  ← Construiește query SPARQL
└────────┬────────┘
         │ apelează
         ▼
┌─────────────────┐
│ WikidataClient  │  ← Trimite query la Wikidata
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│ Wikidata SPARQL │  ← Endpoint public Wikidata
│ Endpoint        │
└────────┬────────┘
         │ JSON Response
         ▼
┌─────────────────┐
│ CacheService    │  ← Salvează în Redis (cache)
└────────┬────────┘
         │
         ▼
    [JSON cu cărți] ──────────────────────────▶ Browser
```

**IMPORTANT**: În acest scenariu, **ontologia locală NU este folosită**. Datele vin direct din Wikidata.

---

### Scenariul 2: Interogare Ontologie Locală

```
┌─────────┐    POST /ontology/query
│ Browser │    { "query": "SELECT ?name WHERE { ?a a lit:Author }" }
└────┬────┘ ────────────────────────────────────────────▶
     │
     ▼
┌─────────────────┐
│  ontology.py    │  ← Router FastAPI
│  (router)       │
└────────┬────────┘
         │ apelează
         ▼
┌─────────────────┐
│ OntologyService │  ← Procesează query SPARQL
└────────┬────────┘
         │ parsează
         ▼
┌─────────────────┐
│ literature.ttl  │  ← Fișier TTL local (în memorie)
└────────┬────────┘
         │ RDFLib query
         ▼
    [JSON cu autori din ontologie] ──────────▶ Browser
```

**IMPORTANT**: În acest scenariu, **Wikidata NU este contactat**. Datele vin din fișierul TTL local.

---

### Scenariul 3: Obținere Clase/Proprietăți (Metadata)

```
┌─────────┐    GET /ontology/classes
│ Browser │ ─────────────────────────────────▶
└────┬────┘
     │
     ▼
┌─────────────────┐
│  ontology.py    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     SPARQL: SELECT ?class WHERE { ?class a owl:Class }
│ OntologyService │  ─────────────────────────────────────────────────────▶
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ literature.ttl  │  ← Returnează: Author, LiteraryWork, Genre, etc.
└────────┬────────┘
         │
         ▼
    [JSON cu lista de clase] ────────────────▶ Browser
```

**Utilizare**: Frontend-ul poate afișa ce tipuri de entități există în sistem.

---

## Când Se Folosește Fiecare Sursă

| Acțiune Utilizator | Serviciu | Sursă Date |
|--------------------|----------|------------|
| Caută cărți americane | SearchService | **Wikidata** |
| Vizualizează graf influențe | GraphService | **Wikidata** |
| Afișează hartă locații | GeoService | **Wikidata** |
| Obține recomandări | RecommendationService | **Wikidata** |
| Listează clase ontologie | OntologyService | **literature.ttl** |
| Listează proprietăți | OntologyService | **literature.ttl** |
| Query SPARQL custom pe ontologie | OntologyService | **literature.ttl** |
| Obține autori din ontologie | OntologyService | **literature.ttl** |

---

## Integrare Viitoare: Ontologie ca Schemă pentru Wikidata

În prezent, cele două surse operează **independent**. O îmbunătățire viitoare ar fi:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ARHITECTURĂ VIITOARE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐                                            │
│  │  literature.ttl     │                                            │
│  │  (Schema/TBox)      │                                            │
│  └──────────┬──────────┘                                            │
│             │ validează                                             │
│             ▼                                                       │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │  Query Generator    │ ──────▶ │     Wikidata        │           │
│  │  (folosește schema) │         │     SPARQL          │           │
│  └─────────────────────┘         └─────────────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Beneficii**:
- Ontologia ar valida query-urile înainte de a le trimite la Wikidata
- Schema ar genera automat query-uri SPARQL corecte
- Consistență între modelul local și datele Wikidata

---

## Plan de Implementare: Ontologie ca Schemă de Validare

### Obiectiv

Integrarea ontologiei locale (`literature.ttl`) ca **schemă de validare** pentru datele primite de la Wikidata, asigurând:
1. Validarea structurii datelor
2. Generarea automată de query-uri SPARQL
3. Maparea consistentă între proprietăți locale și Wikidata

---

## Resurse Suplimentare

- [RDFLib Documentation](https://rdflib.readthedocs.io/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/)
- [Turtle - Terse RDF Triple Language](https://www.w3.org/TR/turtle/)

---

# Sistem de Validare Ontologică

## Prezentare Generală

Sistemul de validare folosește ontologia locală ca **schemă** pentru a valida datele primite de la Wikidata. Aceasta asigură consistența și corectitudinea datelor înainte de a fi afișate utilizatorului.

**De ce?**
> Wikidata este o sursă externă, necontrolată. Datele pot fi incomplete, în formate neașteptate sau inconsistente. Validarea garantează că aplicația noastră procesează doar date conforme cu modelul nostru semantic.

---

## Arhitectura Sistemului de Validare

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SISTEMUL DE VALIDARE ONTOLOGICĂ                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ONTOLOGIE (literature.ttl)                    │   │
│  │                                                                  │   │
│  │  owl:equivalentClass    owl:equivalentProperty    rdfs:domain    │   │
│  │  owl:equivalentProperty rdfs:range                xsd:datatype   │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        SchemaMapper                               │  │
│  │                                                                   │  │
│  │  Extrage mapări:                                                  │  │
│  │  • Author ↔ Q482980        • writtenBy ↔ P50                     │  │
│  │  • LiteraryWork ↔ Q7725634 • birthDate ↔ P569                    │  │
│  │  • Genre ↔ Q223393         • hasGenre ↔ P136                     │  │
│  └──────────────┬────────────────────────────────────┬──────────────┘  │
│                 │                                    │                  │
│                 ▼                                    ▼                  │
│  ┌──────────────────────────┐      ┌──────────────────────────────┐   │
│  │     SPARQLGenerator      │      │     ResponseValidator         │   │
│  │                          │      │                               │   │
│  │  Generează interogări    │      │  Validează răspunsuri:        │   │
│  │  Wikidata bazate pe      │      │  • Tipuri de date             │   │
│  │  proprietățile din       │      │  • Proprietăți lipsă          │   │
│  │  ontologie               │      │  • Formate invalide           │   │
│  └──────────────────────────┘      └──────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Componente

### 1. SchemaMapper (`schema_mapper.py`)

Extrage mapările `owl:equivalentClass` și `owl:equivalentProperty` din ontologie.

**Funcționalități:**
- `extract_mappings()` - Extrage toate mapările clasă ↔ Wikidata QID
- `get_class_mapping(identifier)` - Găsește maparea pentru o clasă
- `get_property_mapping(identifier)` - Găsește maparea pentru o proprietate
- `translate_to_wikidata(identifier)` - Traduce din ontologie în Wikidata
- `translate_from_wikidata(identifier)` - Traduce din Wikidata în ontologie

**Exemplu:**
```python
from app.services.schema_mapper import get_schema_mapper

mapper = get_schema_mapper()
schema = mapper.extract_mappings()

# Afișează mapări
print(f"Clase mapate: {schema.class_count}")
print(f"Proprietăți mapate: {schema.property_count}")

# Traducere
wikidata_id = mapper.translate_to_wikidata("Author")  # → "Q482980"
ontology_name = mapper.translate_from_wikidata("P50")  # → "writtenBy"
```

**De ce?**
> SchemaMapper creează o "punte" între vocabularul nostru local și cel al Wikidata. Aceasta permite interogări și validări automate fără a hardcoda ID-urile Wikidata în cod.

---

### 2. SPARQLGenerator (`sparql_generator.py`)

Generează interogări SPARQL pentru Wikidata bazate pe schema din ontologie.

**Funcționalități:**
- `generate_entity_query(entity_type)` - Generează query pentru un tip de entitate
- `generate_author_query(...)` - Query specializat pentru autori
- `generate_work_query(...)` - Query specializat pentru opere literare
- `generate_validation_query(entity_type, qid)` - Query pentru validare

**Exemplu:**
```python
from app.services.sparql_generator import get_sparql_generator

generator = get_sparql_generator()

# Generează query pentru autori americani
query = generator.generate_author_query(
    country_qid="Q30",  # USA
    year_start=1800,
    year_end=1900,
    limit=50
)

print(query)
# PREFIX wd: <http://www.wikidata.org/entity/>
# PREFIX wdt: <http://www.wikidata.org/prop/direct/>
# SELECT DISTINCT ?author ?authorLabel ?birthDate ?deathDate ...
# WHERE {
#   ?author wdt:P31 wd:Q482980 .
#   ?author wdt:P27 wd:Q30 .
#   OPTIONAL { ?author wdt:P569 ?birthDate . }
#   ...
# }
```

**De ce?**
> În loc să scriem manual interogări SPARQL, le generăm din ontologie. Aceasta asigură că interogările folosesc întotdeauna proprietățile corecte și pot fi actualizate automat când ontologia se schimbă.

---

### 3. ResponseValidator (`response_validator.py`)

Validează datele primite de la Wikidata conform schemei din ontologie.

**Funcționalități:**
- `validate_entity(entity_type, data)` - Validează o singură entitate
- `validate_batch(entity_type, data_list)` - Validează mai multe entități
- `validate_wikidata_response(entity_type, bindings)` - Validează răspuns SPARQL brut

**Tipuri de Validare:**

| Tip | Descriere | Severitate |
|-----|-----------|------------|
| `missing_required` | Proprietate obligatorie lipsă | ERROR |
| `type_mismatch` | Tip de dată greșit | ERROR/WARNING |
| `invalid_range` | Valoare în afara intervalului | WARNING |
| `unknown_property` | Proprietate nedefinită în ontologie | WARNING |
| `format` | Format neașteptat (ex: dată) | WARNING |

**Exemplu:**
```python
from app.services.response_validator import get_response_validator

validator = get_response_validator()

# Date de la Wikidata
author_data = {
    "qid": "Q23434",
    "birthDate": "1899-07-21",
    "birthPlace": "Q183287",
    "citizenship": "Q30"
}

result = validator.validate_entity("Author", author_data)

print(f"Valid: {result.valid}")
print(f"Erori: {result.error_count}")
print(f"Avertismente: {result.warning_count}")

for issue in result.issues:
    print(f"[{issue.severity}] {issue.field}: {issue.message}")
```

**De ce?**
> Validarea detectează probleme precum date lipsă, formate greșite sau inconsistențe înainte ca acestea să afecteze vizualizările sau experiența utilizatorului.

---

## Endpoint-uri API

### Schema și Mapări

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/validation/schema` | GET | Toate mapările clasă/proprietate |
| `/validation/schema/classes` | GET | Doar mapări de clase |
| `/validation/schema/properties` | GET | Doar mapări de proprietăți |
| `/validation/schema/class/{id}` | GET | Mapare pentru o clasă specifică |
| `/validation/schema/property/{id}` | GET | Mapare pentru o proprietate |
| `/validation/schema/translate` | GET | Traduce între ontologie ↔ Wikidata |

### Generare SPARQL

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/validation/sparql/entity/{type}` | GET | Query generic pentru tip de entitate |
| `/validation/sparql/author` | GET | Query specializat pentru autori |
| `/validation/sparql/work` | GET | Query specializat pentru opere |
| `/validation/sparql/influence` | GET | Query pentru graf de influențe |
| `/validation/sparql/validation/{type}/{qid}` | GET | Query pentru validare |

### Validare

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/validation/validate` | POST | Validează o entitate |
| `/validation/validate/batch` | POST | Validează mai multe entități |
| `/validation/expected-properties/{type}` | GET | Proprietăți așteptate pentru un tip |
| `/validation/summary/{type}` | GET | Sumar complet pentru un tip de entitate |

---

## Flux de Date cu Validare

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUX DE DATE CU VALIDARE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CERERE UTILIZATOR                                                   │
│     └─► "Arată-mi autorii americani din secolul XIX"                    │
│                                                                         │
│  2. GENERARE SPARQL (SPARQLGenerator)                                   │
│     └─► Folosește ontologia pentru a genera query Wikidata             │
│         SELECT ?author ?birthDate ... WHERE { ?author wdt:P27 wd:Q30 } │
│                                                                         │
│  3. INTEROGARE WIKIDATA                                                 │
│     └─► WikidataClient execută query-ul                                │
│         Returnează: [{qid: "Q23434", birthDate: "1899-07-21", ...}]    │
│                                                                         │
│  4. VALIDARE RĂSPUNS (ResponseValidator)                                │
│     └─► Verifică fiecare entitate conform schemei                      │
│         ✓ birthDate: format corect (xsd:date)                          │
│         ✓ birthPlace: referință validă (Q-number)                      │
│         ⚠ deathPlace: lipsă (opțional)                                 │
│                                                                         │
│  5. RĂSPUNS FILTRAT/ÎMBOGĂȚIT                                           │
│     └─► Date validate + metadate de validare                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Exemple de Utilizare

### Exemplu 1: Verificare Schemă

```bash
# Obține toate mapările
curl http://localhost:8000/validation/schema

# Traduce un identificator
curl "http://localhost:8000/validation/schema/translate?identifier=Author&direction=to_wikidata"
# Răspuns: {"original": "Author", "translated": "Q482980"}
```

### Exemplu 2: Generare SPARQL

```bash
# Generează query pentru autori francezi
curl "http://localhost:8000/validation/sparql/author?country_qid=Q142&limit=10"

# Răspuns include query-ul SPARQL complet gata de executat pe Wikidata
```

### Exemplu 3: Validare Date

```bash
# Validează un autor
curl -X POST http://localhost:8000/validation/validate \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Author",
    "data": {
      "qid": "Q23434",
      "birthDate": "1899-07-21",
      "birthPlace": "Q183287"
    }
  }'

# Răspuns:
# {
#   "valid": true,
#   "entity_type": "Author",
#   "issues": [
#     {"type": "missing_required", "severity": "info", "field": "deathPlace", ...}
#   ],
#   "error_count": 0,
#   "warning_count": 0
# }
```

### Exemplu 4: Validare în Lot

```bash
# Validează mai mulți autori
curl -X POST http://localhost:8000/validation/validate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Author",
    "data": [
      {"qid": "Q23434", "birthDate": "1899-07-21"},
      {"qid": "Q150905", "birthDate": "1927-03-06"}
    ]
  }'

# Răspuns include statistici agregate și rezultate individuale
```

---

## Integrare cu Serviciile Existente

Sistemul de validare poate fi integrat în serviciile existente:

```python
# În SearchService sau GraphService

from app.services.response_validator import get_response_validator
from app.services.sparql_generator import get_sparql_generator

class SearchService:
    def __init__(self):
        self.validator = get_response_validator()
        self.generator = get_sparql_generator()
    
    async def search_authors(self, country_qid: str, validate: bool = True):
        # 1. Generează query din ontologie
        query = self.generator.generate_author_query(country_qid=country_qid)
        
        # 2. Execută pe Wikidata
        results = await self.wikidata_client.execute_query(query)
        
        # 3. Validează dacă cerut
        if validate:
            validation = self.validator.validate_batch("Author", results)
            if validation.invalid_entities > 0:
                logger.warning(f"{validation.invalid_entities} entități invalide")
        
        return results
```

**De ce?**
> Integrarea validării în serviciile existente permite detectarea automată a problemelor de date fără modificări majore ale codului existent.

---

## Beneficii ale Sistemului de Validare

| Beneficiu | Descriere |
|-----------|-----------|
| **Consistență** | Datele respectă întotdeauna schema definită |
| **Detectare Erori** | Problemele sunt identificate înainte de afișare |
| **Documentare Vie** | Ontologia servește ca documentație a modelului de date |
| **Interogări Corecte** | SPARQL generat automat din schemă |
| **Flexibilitate** | Modificări în ontologie se reflectă automat |
| **Transparență** | Utilizatorii pot vedea ce date sunt așteptate |

---

## Considerații de Performanță

1. **Caching**: Schema este extrasă o singură dată și cache-uită
2. **Lazy Loading**: Mapările se încarcă la prima cerere
3. **Singleton Pattern**: Un singur mapper/validator per aplicație
4. **Validare Opțională**: Poate fi dezactivată pentru performanță

**De ce?**
> Sistemul de validare adaugă overhead minimal. Schema este în memorie, iar validarea este O(n) unde n = numărul de proprietăți per entitate.

---

## Validare SHACL (W3C Standard)

Pe lângă validarea custom bazată pe ontologie, Literature Explorer suportă și **SHACL (Shapes Constraint Language)** - standardul W3C pentru validarea datelor RDF.

### Ce este SHACL?

SHACL este un limbaj declarativ pentru definirea constrângerilor asupra datelor RDF:

```turtle
# Exemplu: Shape pentru Author
lit:AuthorShape a sh:NodeShape ;
    sh:targetClass lit:Author ;
    
    sh:property [
        sh:path lit:name ;
        sh:minCount 1 ;           # Obligatoriu
        sh:maxCount 1 ;           # Maxim unul
        sh:datatype xsd:string ;  # Trebuie să fie string
        sh:minLength 1 ;          # Minim 1 caracter
        sh:severity sh:Violation ; # Eroare dacă lipsește
    ] ;
    
    sh:property [
        sh:path lit:birthDate ;
        sh:maxCount 1 ;
        sh:datatype xsd:date ;
        sh:severity sh:Warning ;  # Avertisment, nu eroare
    ] .
```

### Avantaje SHACL vs Validare Custom

| Aspect | Validare Custom | SHACL |
|--------|-----------------|-------|
| **Standard** | Proprietar | W3C Standard |
| **Portabilitate** | Doar în Python | Orice implementare SHACL |
| **Expresivitate** | Limitată | Foarte bogată |
| **Severități** | Error/Warning/Info | sh:Violation/Warning/Info |
| **Interoperabilitate** | Nu | Da, cu alte tool-uri RDF |

### Fișierul de Shapes

Shapes sunt definite în `backend/app/ontology/literature_shapes.ttl`:

```
literature_shapes.ttl
├── AuthorShape           # 10 constrângeri
├── LiteraryWorkShape     # 9 constrângeri  
├── NovelShape            # Moștenește de la LiteraryWork
├── GenreShape            # 2 constrângeri
├── LocationShape         # 3 constrângeri
├── LiteraryMovementShape # 2 constrângeri
├── PublisherShape        # 1 constrângere
└── AwardShape            # 1 constrângere
```

### Endpoint-uri SHACL

#### 1. Listare Shapes

```bash
# Vezi toate shapes disponibile
curl http://localhost:8000/validation/shacl/shapes

# Răspuns:
{
  "shapes": [
    {
      "shape_name": "AuthorShape",
      "target_class": "http://literature-explorer.org/ontology#Author",
      "property_count": 10,
      "constraints": [...]
    }
  ],
  "total_shapes": 8
}
```

#### 2. Detalii Shape Specific

```bash
# Vezi constrângerile pentru Author
curl http://localhost:8000/validation/shacl/shapes/AuthorShape

# Sau folosind numele entității
curl http://localhost:8000/validation/shacl/shapes/Author
```

#### 3. Validare JSON cu SHACL

```bash
# Validează date JSON
curl -X POST http://localhost:8000/validation/shacl/validate/json \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Author",
    "data": {
      "qid": "Q23434",
      "name": "Ernest Hemingway",
      "birthDate": "1899-07-21"
    }
  }'

# Răspuns valid:
{
  "conforms": true,
  "violations": [],
  "violation_count": 0,
  "warning_count": 0,
  "validation_time_ms": 5.2
}
```

#### 4. Validare Date Invalide

```bash
# Autor fără nume (câmp obligatoriu)
curl -X POST http://localhost:8000/validation/shacl/validate/json \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Author",
    "data": {
      "qid": "Q12345",
      "birthDate": "1900-01-01"
    }
  }'

# Răspuns cu violații:
{
  "conforms": false,
  "violations": [
    {
      "focus_node": "http://literature-explorer.org/data/author/Q12345",
      "result_path": "http://literature-explorer.org/ontology#name",
      "severity": "Violation",
      "message": "Author must have exactly one non-empty name"
    }
  ],
  "violation_count": 1
}
```

#### 5. Validare RDF Direct

```bash
# Validează date RDF în format Turtle
curl -X POST http://localhost:8000/validation/shacl/validate \
  -H "Content-Type: application/json" \
  -d '{
    "data": "@prefix lit: <http://literature-explorer.org/ontology#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n<http://example.org/author1> a lit:Author ;\n    lit:name \"Test Author\"^^xsd:string .",
    "data_format": "turtle",
    "target_shapes": ["AuthorShape"]
  }'
```

#### 6. Obține Constrângeri pentru Tip

```bash
# Vezi ce constrângeri există pentru Author
curl http://localhost:8000/validation/shacl/constraints/Author

# Răspuns:
{
  "entity_type": "Author",
  "shape_name": "AuthorShape",
  "required_properties": ["name"],
  "optional_properties": ["birthDate", "deathDate", "birthPlace", ...],
  "constraints_by_property": {
    "name": {
      "required": true,
      "datatype": "string",
      "minLength": 1,
      "severity": "Violation"
    },
    "birthDate": {
      "required": false,
      "datatype": "date",
      "severity": "Warning"
    }
  }
}
```

### Severități SHACL

SHACL definește trei niveluri de severitate:

| Severitate | Simbol SHACL | Semnificație |
|------------|--------------|--------------|
| **Violation** | `sh:Violation` | Eroare gravă - datele sunt invalide |
| **Warning** | `sh:Warning` | Avertisment - date incomplete sau potențial problematice |
| **Info** | `sh:Info` | Informațional - sugestie de îmbunătățire |

### Tipuri de Constrângeri Suportate

```turtle
# Cardinalitate
sh:minCount 1 ;     # Minim 1 valoare
sh:maxCount 1 ;     # Maxim 1 valoare

# Tip de date
sh:datatype xsd:string ;  # String
sh:datatype xsd:date ;    # Data (YYYY-MM-DD)
sh:datatype xsd:integer ; # Număr întreg

# Referințe la clase
sh:class lit:Author ;     # Trebuie să fie de tip Author
sh:class lit:Location ;   # Trebuie să fie de tip Location

# Lungime string
sh:minLength 1 ;    # Minim 1 caracter
sh:maxLength 500 ;  # Maxim 500 caractere

# Pattern (regex)
sh:pattern "^Q[0-9]+$" ;  # Format QID Wikidata
```

### Utilizare în Cod Python

```python
from app.services.shacl_validator import get_shacl_validator

# Obține validator
validator = get_shacl_validator()

# Validează JSON
result = validator.validate_json("Author", {
    "qid": "Q23434",
    "name": "Ernest Hemingway",
    "birthDate": "1899-07-21"
})

if result.conforms:
    print("✓ Date valide")
else:
    for violation in result.violations:
        print(f"✗ {violation.severity}: {violation.message}")

# Validează RDF Turtle
turtle_data = '''
    @prefix lit: <http://literature-explorer.org/ontology#> .
    <http://example.org/author1> a lit:Author ;
        lit:name "Test" .
'''
result = validator.validate_rdf(turtle_data, data_format="turtle")

# Obține informații despre shapes
shapes = validator.get_shapes_info()
print(f"Total shapes: {shapes.total_shapes}")

# Obține shape pentru tip specific
author_shape = validator.get_shape_for_type("Author")
print(f"Constrângeri Author: {author_shape.property_count}")
```

### Reîncărcare Shapes

După modificarea fișierului `literature_shapes.ttl`:

```bash
# Reîncarcă shapes fără restart server
curl -X POST http://localhost:8000/validation/shacl/reload

# Răspuns:
{
  "message": "SHACL shapes reloaded successfully",
  "total_shapes": "8"
}
```

---

## Comparație: Validare Custom vs SHACL

| Scenariu | Recomandare |
|----------|-------------|
| Validare rapidă JSON din Wikidata | Validare Custom (mai rapidă) |
| Validare completă RDF | SHACL |
| Export date către alte sisteme | SHACL (standard) |
| Debugging probleme de date | SHACL (mesaje detaliate) |
| Integrare cu tool-uri RDF externe | SHACL |
| Performanță critică | Validare Custom |

**Recomandare**: Folosiți ambele sisteme complementar:
- **Validare Custom** pentru verificări rapide în runtime
- **SHACL** pentru validare completă și export de date
