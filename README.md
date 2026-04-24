# 404NotFounders

## LintasNiaga Project Blueprint (Simple Overview)

**LintasNiaga** is a cross-border procurement + FX decision copilot for Malaysian SME importers.

In simple terms:
- **You provide** a few supplier quotations (PDF/images/manual entry) and basic purchase context (SKU, quantity, required-by date).
- **The system pulls** supporting macro and FX context (e.g., exchange rates and key indicators) to ground the analysis.
- **The reasoning engine** uses **ilmu-glm-5.1** (with auditable thinking) orchestrated via an agent workflow (e.g., LangGraph) so decisions are explainable and traceable.
- **It outputs** a recommended supplier choice, an appropriate **hedge ratio**, and a clear explanation of *why*—including the assumptions and supporting data.

At a high level, the intended architecture is:
- **Web app** (Next.js) for upload, review, and results visualization
- **Backend agent** (FastAPI) for data retrieval + reasoning orchestration
- **Database/auth** (Supabase) for users, analyses, and stored results
- **Caching/rate-limits** (Upstash) for external data calls
- **Observability** (Langfuse) to trace and audit model/tool calls end-to-end

For the full blueprint and guiding principles, see:
- `LintasNiaga_WINNING_PLAYBOOK.md`
