```mermaid
flowchart TD
    Q[User Question<br/>CLI Input]

    Q --> G[Guardrail Layer<br/>Keyword / Regex Checks]
    G -->|Allowed| T[Tokenisation<br/>BM25-style Indexing]
    G -->|Refused| R[Refusal Response<br/>Limitations + Low Confidence]

    T --> M[Deterministic Retrieval<br/>Keyword & Regex Matching]

    M -->|No / Weak Matches| L[Failure Handler<br/>Explicit Limitations<br/>confidence = very_low]
    M -->|Relevant Sections| S[Bounded Synthesis<br/>Extractive summary only]

    S -->|Mode A (current)| O[Structured JSON Output<br/>Summary<br/>Relevant Sections<br/>Limitations<br/>Confidence]
    S -->|Mode B (planned)| X[Post-Retrieval LLM<br/>Paraphrase / summarise retrieved text]
    X --> O
    L --> O
    R --> O
```

_Mode B (LLM-assisted) is planned and not yet wired into the pipeline. Retrieval, guardrails, and refusal stay deterministic in both modes._
