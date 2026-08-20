"""
Every tunable value in the system lives here.

Chunk size, top-k, model names -- all of it changes as the system grows
(bigger chunks, a reranker, a different embedding model). If those values
were scattered across modules, a tuning pass would mean hunting down every
file that still says 512. One file means one diff.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# src/atlas/config.py -> src/atlas -> src -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Fields without a default are REQUIRED. If one is missing, pydantic raises at 
    import time with every missing key listed -- not one at a time, and not a 
    confusing 401 twenty seconds into an ingest run.

    Field names map to environment variables case-insensitively, so
    `anthropic_api_key` reads ANTHROPIC_API_KEY.
    """

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # Our .env holds only these keys today, but 'ignore' means adding an
        # unrelated variable later in the .env does not crash the app. The default is
        # 'forbid', which would.
        extra="ignore"
    )


    # --- credentials (required) ---
    anthropic_api_key: str
    openai_api_key: str


    # --- vector store ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "atlas_mine_v01"

    # -- models ---
    # The embedding model determines the vector size below. Change one, change
    # both, and re-index -- query vectors and document vectors must come from the
    # same model or the similarity scores are meaningless.
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Held fixed across every version. Changing the synthesis model mid-project
    # contaminates every eval delta after it -- can't no longer tell whether an
    # improvement came from retrieval work or from the model upgrade.
    synthesis_model: str = "claude-haiku-4-5"

    # --- v0.1 retrieval parameters (deliberately naive) ---
    chunk_tokens: int = 512
    tokenizer_encoding: str = "cl100k_base" # matches text-embedding-3-small
    top_k: int = 5

    # --- paths ---
    # Properties, not fields: these are derived from the repo layout, so there is
    # no reason to expose them to the environment.

    @property
    def fixtures_dir(self) -> Path:
        return REPO_ROOT / "eval" / "fixtures"

    @property
    def golden_dataset(self) -> Path:
        return REPO_ROOT / "eval" / "golden_dataset.json"

    @property
    def results_dir(self) -> Path:
        return REPO_ROOT / "eval" / "results"


settings = Settings()