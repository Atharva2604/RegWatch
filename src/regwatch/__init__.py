"""RegWatch: Autonomous Regulatory Intelligence & Compliance Monitoring Engine.

Clean Architecture & Modular Monolith layout:
- domain: Pure business logic, canonical models, ports (protocols).
- application: Pipeline stages, use cases, job handlers.
- infrastructure: Adapters (Supabase, Groq, fetchers, parsers, notifiers).
- interfaces: CLI, FastAPI endpoints, Streamlit dashboard.
"""

__version__ = "0.1.0"
