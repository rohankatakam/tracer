## 5. LLM Multimodal Reasoning Chain (Task Graph Generation)

This is the core AI component responsible for generating the task graph.

### 5.1. Engine

A powerful Multimodal Language Model (LLM) is used, such as **Google's Gemini 2.5 Pro** (specifically, `gemini-2.5-pro-preview-05-06` as per model details). Key characteristics of this model relevant to the system are:

*   **Supported Data Types**:
    *   Inputs: Audio, images, video, and text
    *   Output: Text
*   **Token Limits**:
    *   Input: 1,048,576 tokens
    *   Output: 65,536 tokens
*   **Capabilities**: Structured outputs, Caching, Function calling, Code execution, Search grounding, Thinking.
*   **Knowledge Cutoff**: January 2025 (latest update May 2025).

### 5.2. Input to LLM

The LLM receives a carefully constructed prompt containing:

1.  **Bug Context**: Information from the "Bug Instance" (name, description, comments, product, version, etc.).
2.  **Rich Multimodal Data**: Structured data retrieved from the PostgreSQL "Attachment Data Store". This includes:
    *   Transcribed audio from videos, along with associated Deepgram intelligence (summaries, topics, entities, sentiment).
    *   OCR text from images and PDFs.
    *   Key metadata and structural information extracted from all attachment types.
    *   References between different pieces of data (e.g., "text from screenshot X mentioned in comment Y").

### 5.3. Optimized Iterative Reasoning (OIR) Loop

The generation of the task graph is not a single-shot process but an **Optimized Iterative Reasoning (OIR) loop**. This advanced feedback mechanism is designed to dynamically construct the optimal input for the LLM at each stage of the reasoning process, especially when the initial generation is incomplete, ambiguous, or when the LLM requires more specific information to proceed. The primary constraints guiding this optimization are the LLM's input token limit (1,048,576 tokens for `gemini-2.5-pro-preview-05-06`) and the need to derive maximum insight from the available multimodal data (text, images, audio, video) stored in the PostgreSQL datastore and the initial bug details.

**Core Principles of OIR:**

1.  **Dynamic Context Assembly**: Instead of statically feeding all available information, the OIR strategically selects and assembles the most relevant data subset for each LLM call.
2.  **Token Budget-Awareness**: All selections are made with strict adherence to the `gemini-2.5-pro-preview-05-06` model's 1,048,576 input token limit.
3.  **Maximizing Multimodal Insight**: Prioritize the inclusion of high-value multimodal inputs (especially images, video segments, or audio clips) that are most likely to resolve ambiguity or provide critical context for a given reasoning step.
4.  **Progressive Refinement**: The task graph is built or refined incrementally, with each iteration aiming to add more detail, clarity, or confidence to the generated steps.

**OIR Process Steps:**

1.  **Initial Task Graph Generation Attempt**:
    *   The system first attempts to generate an initial task graph using a heuristically selected "best-guess" subset of the bug context and preprocessed attachment data from the PostgreSQL store. This initial selection will prioritize core bug descriptions, highly relevant comments, and key summary information from attachments.

2.  **Evaluation of LLM Output**:
    *   The LLM's output (a task graph segment or a complete graph) is evaluated for:
        *   **Completeness**: Are there missing steps?
        *   **Clarity**: Are the steps unambiguous and actionable?
        *   **Confidence**: (If the LLM provides confidence scores) Is the confidence high enough?
        *   **Implicit/Explicit Need for More Information**: Does the LLM's output suggest it lacked certain details, or does it explicitly ask for clarification?

3.  **Optimized Input Selection for Refinement/Clarification (The Core Loop)**:
    If the evaluation indicates a need for refinement or if the LLM is unable to generate a task step:
    *   **Identify Information Gaps/Ambiguities**: Determine the specific area where the LLM struggled or where the task graph is weak.
    *   **Candidate Data Retrieval**: Fetch all potentially relevant data points from:
        *   The full Bug Instance (description, all comments, metadata).
        *   The PostgreSQL Attachment Data Store (all processed text, image metadata, OCR results, video scene data, audio transcripts, Deepgram intelligence outputs like summaries, topics, entities, sentiments).
        *   The current (partially) generated task graph.
        *   History of previous OIR iterations for this bug (if any).
    *   **Relevance Scoring & Ranking**: Each candidate data point is scored for its relevance to the *current specific information gap or ambiguity*. This scoring can use:
        *   Semantic similarity (e.g., vector embeddings) to the problematic task step or the LLM's query.
        *   Keyword matching.
        *   Heuristics (e.g., temporal proximity of a comment to a user action, explicit mentions of attachment IDs in text).
        *   Measures of information density or novelty (to avoid redundant information).
    *   **Multimodal Prioritization**: Special attention is given to selecting the most impactful multimodal elements. For instance, if a step involves a specific UI interaction, the corresponding screenshot or video frame showing that UI state would be highly prioritized.
    *   **Token Budgeting & Dynamic Assembly**:
        *   The system estimates the token cost for each high-ranking candidate data point (text length, image token equivalents for the model, etc.).
        *   It then assembles the new input prompt for the LLM by selecting the highest-scoring data points that collectively fit within the 1,048,576 input token limit. This is a dynamic knapsack-like problem, prioritizing high-relevance items.
        *   This might involve sending only specific image frames, video snippets, or audio segments rather than entire files if token limits are tight but multimodal context is crucial.
    *   **"Context Load Balancing"**: If the amount of highly relevant information *still* exceeds the token limit, the system might employ strategies such as:
        *   Summarizing less critical text sections.
        *   Sending a sequence of more focused LLM calls, each addressing a sub-part of the problem with a tailored context.
        *   Leveraging LLM caching capabilities if available and appropriate (e.g., Gemini 2.5 Pro supports caching).
    *   **Query Formulation**: The prompt to the LLM is precisely formulated to address the identified gap, incorporating the newly selected context. If asking for clarification, the question itself is optimized for clarity.

4.  **LLM Re-invocation**: The LLM is called again with this new, optimized input.

5.  **Loop or Halt**:
    *   The process (steps 2-4) repeats.
    *   The loop continues until:
        *   The task graph (or relevant segment) meets the desired quality criteria.
        *   A predefined number of refinement attempts (N) is exceeded for a particular step or for the overall graph. In this case, the process might halt and flag the bug for manual review, potentially providing the partial task graph and a summary of unresolved ambiguities.
        *   The system determines that further iteration is unlikely to yield better results (diminishing returns).

**Calculation at Every Step**: This sophisticated optimization (candidate selection, relevance scoring, token budgeting, and input assembly) is computationally intensive but critical. It is performed *at each iteration* of the OIR loop to ensure that every interaction with the LLM is as productive as possible.

This OIR approach transforms the iterative refinement from a simple Q&A into a strategic, resource-aware reasoning process, significantly enhancing the potential to generate high-quality, comprehensive task graphs from complex, multimodal bug reports.
