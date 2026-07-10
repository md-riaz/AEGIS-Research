# AEGIS — How It Works: A Visual Explainer

> **For repo visitors who want to understand the thesis without reading the manuscript.**
> Every concept has a diagram. Start at the top and follow the flow.

---

## 1. The Problem in One Picture

Every prior NL-to-SQL system has the same shape:

```
User question  →  LLM  →  SQL string  →  database
```

The LLM **writes SQL**. That means a clever user question can manipulate the LLM into writing:

- `DROP TABLE orders`
- `UNION SELECT password FROM users`
- `; INSERT INTO admin_users VALUES ('hacker', 'secret')`

Even without malice, the LLM invents column names, wrong join conditions, and broken aggregations — and the system executes them anyway.

**Existing defenses** try to detect bad SQL after the LLM generates it: regex filters, classifiers, validators. They're an arms race. AEGIS rejects this entirely.

---

## 2. The AEGIS Approach: Make SQL Injection Structurally Impossible

AEGIS enforces a hard boundary. The LLM **never touches SQL**. It only answers one question:

> *"Which metric, which dimension, which filter does the user want?"*

A separate deterministic compiler — which contains no AI — generates SQL from a pre-approved, finite template library.

```mermaid
flowchart LR
    Q([User Question]) --> LLM

    subgraph AI_LAYER ["🤖 AI Layer  (untrusted output)"]
        LLM["LLM\n─────────────\nInput: natural language\nOutput: IntentObject JSON\n\nCan only pick from\napproved vocabulary"]
    end

    LLM -->|"IntentObject\n{metric, dimension,\nfilters, sort, limit}"| COMPILER

    subgraph SQL_LAYER ["⚙️ Deterministic Layer  (no AI)"]
        COMPILER["SQL Compiler\n─────────────\nInput: validated IntentObject\nOutput: parameterised SQL\n\nSQL expressions are\ncompile-time constants"]
    end

    COMPILER --> DB[(Database)]
    DB --> RESULT([Dashboard Widget])

    style AI_LAYER fill:#fff3cd,stroke:#f0ad4e
    style SQL_LAYER fill:#d4edda,stroke:#28a745
```

**The formal guarantee:** The set of SQL statements AEGIS can produce equals the Cartesian product of *(15 metrics) × (34 dimensions) × (finite filter operators)*. That set is enumerable and auditable. SQL injection requires generating SQL *outside* this set, which the architecture makes impossible.

---

## 3. The 7-Stage Pipeline

Every user query travels through exactly seven stages. Stages 2–7 contain zero AI — they are deterministic code.

```mermaid
flowchart TD
    S0([Natural Language Query])

    S1["Stage 1 — Intent Extraction\n──────────────────────────────\nLLM reads the query + system prompt\nOutputs a validated IntentObject\n\n🤖 Only AI stage"]

    S2["Stage 2 — Coverage Validation\n──────────────────────────────\nChecks that metric_term and dimension_term\nexist in the semantic layer vocabulary\nRejects unknown IDs before any SQL runs"]

    S3["Stage 3 — Semantic Mapping\n──────────────────────────────\nExpands business logic aliases\n('abandoned' → OrderStatusId = 40)\nResolves time expressions\n('this year' → YEAR(CreatedOnUtc) = 2026)"]

    S4["Stage 4 — Permission Rewriting\n──────────────────────────────\nAppends row-level security WHERE clauses\nBased on the authenticated user's role\nUser can never bypass this — it runs after LLM"]

    S5["Stage 5 — SQL Compilation\n──────────────────────────────\nBFS over JOIN_GRAPH finds minimal join path\nSubstitutes pre-compiled SQL expressions\nAll values are parameterised (no concatenation)"]

    S6["Stage 6 — Visualisation Selection\n──────────────────────────────\nRule engine picks chart type:\ntrend→line, ranking→bar, kpi→card...\nNo AI — pure deterministic rules"]

    S7["Stage 7 — Widget Persistence\n──────────────────────────────\nSHA-256 hash of (intent + permissions)\nDeduplicates identical widgets\nStores for dashboard refresh"]

    RESULT([Dashboard Widget])

    S0 --> S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> RESULT

    style S1 fill:#fff3cd,stroke:#f0ad4e
    style S2 fill:#d4edda,stroke:#28a745
    style S3 fill:#d4edda,stroke:#28a745
    style S4 fill:#d4edda,stroke:#28a745
    style S5 fill:#d4edda,stroke:#28a745
    style S6 fill:#d4edda,stroke:#28a745
    style S7 fill:#d4edda,stroke:#28a745
```

---

## 4. The Semantic Layer — The Closed Vocabulary

The semantic layer (`aegis/server/semantic_layer.py`) defines the **complete, finite set of things AEGIS can answer**. It has three components.

```mermaid
flowchart LR
    SL["Semantic Layer\nsemantic_layer.py"]

    M["📊 15 METRICS\nNamed SQL aggregate expressions\ne.g. revenue, order_count, profit"]
    D["🔖 34 DIMENSIONS\nGrouping & filtering axes\ne.g. product_name, order_month, country"]
    J["🔗 11 JOIN PATHS\nUndirected graph of table relationships\nCompiler does BFS to find minimal joins"]

    SL --> M
    SL --> D
    SL --> J
```

### 4.1 The 15 Metrics

A metric is a **named SQL aggregate expression**. The LLM outputs only the ID string. The compiler substitutes the full SQL — the LLM never sees or touches the expression.

| ID | Label | SQL Expression |
|----|-------|----------------|
| `revenue` | Total Revenue | `SUM(COALESCE(o.OrderTotal,0) - COALESCE(o.RefundedAmount,0))` |
| `order_count` | Number of Orders | `COUNT(DISTINCT o.Id)` |
| `avg_order_value` | Average Order Value | `AVG(COALESCE(o.OrderTotal,0))` |
| `item_quantity` | Quantity Sold | `SUM(COALESCE(oi.Quantity,0))` |
| `shipping_cost` | Shipping Cost | `SUM(o.OrderShippingExclTax)` |
| `customer_count` | Number of Customers | `COUNT(DISTINCT cu.Id)` |
| `refund_count` | Number of Refunds | `COUNT(DISTINCT CASE WHEN o.RefundedAmount > 0 THEN o.Id END)` |
| `refund_amount` | Total Refunded | `SUM(o.RefundedAmount)` |
| `discount_amount` | Total Discount | `SUM(o.OrderDiscount)` |
| `profit` | Profit | `SUM(COALESCE(o.OrderTotal,0) - COALESCE(o.OrderSubtotalExclTax,0))` |
| `line_item_revenue` | Product Revenue | `SUM(oi.PriceExclTax)` |
| `tax_amount` | Tax Amount | `SUM(o.OrderTax)` |
| `line_item_cost` | Product Cost | `SUM(oi.OriginalProductCost)` |
| `line_item_discount` | Line Item Discount | `SUM(oi.DiscountAmountExclTax)` |
| `shipment_count` | Shipment Count | `COUNT(DISTINCT sh.Id)` |

### 4.2 The 34 Dimensions

Dimensions are grouped by domain. Each defines the SQL expression used in `SELECT` and `GROUP BY`.

**Products** — `product_name`, `product_sku`, `product_price`, `product_cost`, `product_stock`, `product_rating`, `product_published`, `product_created_date`

**Taxonomy** — `category_name`, `manufacturer_name`

**Customers** — `customer_name`, `customer_email`, `customer_active`, `customer_registration_date`

**Orders (time)** — `order_date`, `order_month`, `order_year`, `order_id`, `order_number`

**Orders (status)** — `order_status`, `payment_status`, `shipping_status`, `payment_method`, `shipping_method`, `currency_code` *(all pre-compiled CASE expressions — no raw status codes reach the user)*

**Geography** — `country_name`, `billing_city`

**Shipments** — `tracking_number`, `shipped_date`, `delivery_date`

**Store** — `store_name`

### 4.3 The Join Graph — 11 Edges

The SQL compiler uses **Breadth-First Search (BFS)** over this graph to find the minimal set of JOIN clauses for any metric+dimension pair. No joins are hardcoded per query — the graph is the single source of truth.

```mermaid
graph LR
    Order(["🛒 Order\n(anchor table)"])
    Customer(["👤 Customer"])
    OrderItem(["📦 OrderItem"])
    Product(["🏷️ Product"])
    PCM(["Product_Category\n_Mapping"])
    Category(["🗂️ Category"])
    PMM(["Product_Manufacturer\n_Mapping"])
    Manufacturer(["🏭 Manufacturer"])
    Address(["📍 Address"])
    Country(["🌍 Country"])
    Shipment(["🚚 Shipment"])
    Store(["🏪 Store"])

    Order -->|"CustomerId = cu.Id"| Customer
    Order -->|"Id = oi.OrderId"| OrderItem
    OrderItem -->|"ProductId = p.Id"| Product
    Product -->|"Id = pcm.ProductId"| PCM
    PCM -->|"CategoryId = c.Id"| Category
    Product -->|"Id = pmm.ProductId"| PMM
    PMM -->|"ManufacturerId = mf.Id"| Manufacturer
    Order -->|"BillingAddressId = addr.Id"| Address
    Address -->|"CountryId = co.Id"| Country
    Order -->|"Id = sh.OrderId"| Shipment
    Order -->|"StoreId = st.Id"| Store
```

**BFS example:** Query asks for `revenue` by `category_name`.
- `revenue` binds to `Order` (start node)
- `category_name` binds to `Category` (target node)
- BFS path: `Order → OrderItem → Product → Product_Category_Mapping → Category`
- Compiler emits exactly those four JOIN clauses — no more, no less

### 4.4 Vocabulary Injection — How the LLM Learns the Vocabulary

AEGIS does **not** maintain a synonym dictionary. Instead, all 15 metric IDs and 34 dimension IDs are embedded directly into the LLM system prompt at startup (~1,100 tokens). The LLM performs synonym resolution at inference time.

```mermaid
sequenceDiagram
    participant SP as System Prompt (built at startup)
    participant LLM as LLM
    participant IP as IntentParser

    Note over SP: Built once from semantic_layer.py<br/>Contains all 15 metric IDs + descriptions<br/>Contains all 34 dimension IDs + descriptions<br/>Contains 11 intent class definitions + examples

    IP->>LLM: system_prompt + user query
    Note over LLM: "top 5 products by sales"
    LLM-->>IP: {"intent_class":"ranking",<br/>"metric_term":"revenue",<br/>"dimension_term":"product_name",<br/>"sort":"desc","limit":5}

    Note over IP: Validates every field<br/>against the semantic layer.<br/>Unknown IDs → rejected.
```

The key insight: the LLM maps *"sales"* → `revenue`, *"products"* → `product_name` **at inference time** using its language understanding. The system prompt teaches the vocabulary without a separate lookup table.

### 4.5 Business Logic Mappings

Some domain terms can't be mapped by the LLM alone because they require internal status codes. These are handled by the **SemanticMapper** (Stage 3) with a hardcoded dictionary:

| User says... | Expands to... |
|---|---|
| `"abandoned"` | `OrderStatusId = 40` |
| `"referral_source"` | `cu.AdminComment CONTAINS 'ref:'` |

This keeps domain expertise in code, not in the LLM prompt.

---

## 5. Complete Query Walkthrough

**Query:** *"Show me the top 5 products by revenue"*

```mermaid
sequenceDiagram
    participant U as User
    participant IP as Stage 1: IntentParser
    participant CV as Stage 2: Coverage Validator
    participant SM as Stage 3: SemanticMapper
    participant PR as Stage 4: Permission Rewriter
    participant SC as Stage 5: SQL Compiler
    participant VS as Stage 6: Viz Selector
    participant WE as Stage 7: Widget Engine
    participant DB as Database

    U->>IP: "Show me the top 5 products by revenue"

    Note over IP: LLM reads query + system prompt
    IP-->>CV: IntentObject {<br/>intent_class: "ranking",<br/>metric_term: "revenue",<br/>dimension_term: "product_name",<br/>sort: "desc", limit: 5<br/>}

    Note over CV: Checks "revenue" ∈ METRICS ✓<br/>Checks "product_name" ∈ DIMENSIONS ✓
    CV-->>SM: validated IntentObject

    Note over SM: No business logic aliases here<br/>Resolves time_term if present
    SM-->>PR: expanded IntentObject

    Note over PR: User role = "manager"<br/>Appends: AND o.StoreId = 3
    PR-->>SC: permission-filtered IntentObject

    Note over SC: BFS: Order→OrderItem→Product<br/>Substitutes pre-compiled expressions
    SC-->>VS: SELECT p.Name, SUM(...) AS revenue<br/>FROM Order o<br/>JOIN OrderItem oi ON o.Id = oi.OrderId<br/>JOIN Product p ON oi.ProductId = p.Id<br/>WHERE o.StoreId = 3<br/>GROUP BY p.Name<br/>ORDER BY revenue DESC<br/>LIMIT 5

    Note over VS: intent_class="ranking", sort="desc"<br/>→ horizontal bar chart
    VS-->>WE: {sql, chart_type: "bar_h"}

    Note over WE: SHA-256 hash → check for duplicate<br/>Store widget if new
    WE->>DB: execute SQL (parameterised)
    DB-->>WE: result rows
    WE-->>U: Bar chart widget on dashboard
```

---

## 6. The 11 Intent Classes

The LLM must classify every query into one of these classes. The class drives both the SQL template and the visualisation rule.

```mermaid
flowchart TD
    IC["Intent Classes"]

    KPI["📌 kpi\nSingle scalar value\n'Total revenue this month'\n→ KPI card"]
    RANK["🏆 ranking\nTop / bottom N items\n'Top 5 products by sales'\n→ Bar chart"]
    TREND["📈 trend\nChange over time\n'Monthly revenue trend'\n→ Line chart"]
    COMP["⚖️ comparison\nA vs B side-by-side\n'Revenue: paid vs refunded'\n→ Grouped bar"]
    EXCEPT["⚠️ exception\nThreshold / anomaly filter\n'Orders with refund > $100'\n→ Table"]
    SUMM["📋 summary\nMulti-metric overview\n'Sales dashboard'\n→ KPI grid"]
    SEG["🥧 segment\nBreakdown by dimension\n'Revenue by category'\n→ Pie / bar"]
    FUNNEL["🔽 funnel\nConversion stages\n'Pending→Processing→Complete'\n→ Funnel chart"]
    COHORT["👥 cohort\nGroup behaviour analysis\n'New vs returning customers'\n→ Grouped bar"]
    CORR["🔀 correlate\nAttribute relationships\n'Price vs quantity sold'\n→ Scatter"]
    TAB["🗄️ tabular\nList / show / details\n'Show all orders today'\n→ Data table"]

    IC --> KPI
    IC --> RANK
    IC --> TREND
    IC --> COMP
    IC --> EXCEPT
    IC --> SUMM
    IC --> SEG
    IC --> FUNNEL
    IC --> COHORT
    IC --> CORR
    IC --> TAB
```

---

## 7. Two-Layer SQL Safety

AEGIS has two independent safety mechanisms that must *both* fail for an attack to succeed:

```mermaid
flowchart TD
    QUERY([Malicious Query\ne.g. 'DROP TABLE orders'])

    L1["Layer 1 — Vocabulary Constraint\n──────────────────────────────────\nLLM output is validated against\nthe 15-metric × 34-dimension vocabulary.\n\n'DROP TABLE' is not a metric ID.\nThe Pydantic model rejects unknown fields.\n✗ Attack fails here in nearly all cases."]

    L2["Layer 2 — Parameterised Compilation\n──────────────────────────────────\nEven if Layer 1 somehow passed a value,\nall user-supplied values go into\nSQL parameters — never concatenated.\n\nThe compiler only accepts validated\nIntentObject fields as inputs.\n✗ Attack structurally cannot produce DDL."]

    SAFE(["✅ Safe, parameterised SQL\nor ValueError — never malicious DDL"])

    QUERY --> L1 --> L2 --> SAFE
```

---

## 8. Benchmark Results (Summary)

| System | SQL Accuracy | Injection Success Rate | Latency |
|--------|-------------|----------------------|---------|
| Direct LLM-to-SQL (GPT-4) | 72% | **5.0%** | 1.2s |
| Retrieval-augmented NL2SQL | 81% | **3.2%** | 2.1s |
| Schema-aware fine-tuned | 85% | **2.8%** | 0.9s |
| **AEGIS** | **94%** | **0.0%** | 1.8s |

AEGIS achieved 0% injection success rate across all 100 benchmark queries. No prior baseline achieved below 2.8%.

---

## 9. Adding a New Schema (e.g. WooCommerce)

The semantic layer is the only thing that needs to change. No model training, no fine-tuning.

```mermaid
flowchart LR
    A["1. Identify business questions\nWhat does the team need to answer?\n~2 hours"] -->
    B["2. Define METRICS\nWrite SQL aggregate expressions\nfor each measurable fact\n~3 hours"] -->
    C["3. Define DIMENSIONS\nWrite SQL expressions for\neach grouping / filter axis\n~4 hours"] -->
    D["4. Define JOIN_GRAPH\nMap FK relationships between\ntables as JoinPath edges\n~3 hours"] -->
    E["5. Test & iterate\nRun benchmark queries\n~2 hours"] -->
    F(["✅ New schema live\n~14 person-hours total"])
```

The LLM automatically learns the new vocabulary because it is injected into the system prompt dynamically from `semantic_layer.py` at startup. No prompt editing required.

---

## 10. Code Map

```
aegis/server/
├── semantic_layer.py      ← START HERE: the 15 metrics, 34 dimensions, 11 join paths
├── intent_parser.py       ← Stage 1: LLM → IntentObject (the only AI code)
├── models.py              ← Pydantic contracts: IntentObject, IntentClass enum
├── mapper.py              ← Stage 3: business logic expansion + time resolution
├── permission_rewriter.py ← Stage 4: row-level security WHERE injection
├── compiler.py            ← Stage 5: BFS join resolution + SQL template engine
├── visualization.py       ← Stage 6: rule-based chart type selection
├── widget_engine.py       ← Stage 7: SHA-256 dedup + widget persistence
├── database_client.py     ← MySQL parameterised query executor
└── ai_config.py           ← LLM provider config (Groq, OpenRouter, Ollama, etc.)
```

The full research manuscript is at [`docs/AEGIS_Manuscript.md`](docs/AEGIS_Manuscript.md) (LaTeX: [`docs/AEGIS_Manuscript.tex`](docs/AEGIS_Manuscript.tex)).
