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

    # Held fixed across every version. Changing the generation model mid-project
    # contaminates every eval delta after it -- can't no longer tell whether an
    # improvement came from retrieval work or from the model upgrade.
    generation_model: str = "claude-haiku-4-5"

    # --- retrieval parameters ---
    chunk_tokens: int = 750
    # Tokens repeated from the end of one chunk at the start of the next. 0 means
    # chunk N ends exactly where N+1 begins, and a fact split across that boundary
    # appears whole in neither. Must be smaller than chunk_tokens.
    chunk_overlap: int = 100
    tokenizer_encoding: str = "cl100k_base"  # matches text-embedding-3-small
    top_k: int = 5

    # --- chunking strategy ---
    # "fixed"    -- token windows, ignores meaning, the v0.1 baseline
    # "semantic" -- cut where the topic moves, measured by embedding distance
    #               between adjacent sentences
    #
    # Switching this re-chunks the corpus, so the index must be rebuilt and the
    # result is only comparable against runs made with the same value.
    chunk_strategy: str = "fixed"
    # Cut at the top (100 - N)% of adjacent-sentence distances *within a single
    # document*. Per-document rather than corpus-wide because a tightly-focused
    # spec and a rambling email thread have different distance distributions;
    # one global threshold would over-split one and never split the other.
    semantic_percentile: int = 95
    # Floor and ceiling on the result. Both are guards, not tuning knobs.
    # Without the floor a strong seam emits a one-sentence chunk that retrieves
    # well and answers nothing. Without the ceiling a document with uniformly
    # low distances never splits at all.
    semantic_min_tokens: int = 60
    semantic_max_tokens: int = 750
    # The encoder that measures distance between adjacent windows. Local and
    # deliberately so: the OpenAI endpoint returns slightly different vectors for
    # identical input at realistic batch sizes (max|delta| 3.3e-03 over 66
    # windows), which moves a percentile threshold and flips boundaries that sit
    # near it. Harmless for ranking, not harmless for a cut-or-not decision.
    #
    # Boundary detection is an easier task than retrieval -- it only needs
    # consistent *relative* distance between neighbouring windows. A small local
    # model is therefore a reasonable fit, and bge-small-en-v1.5 was measured:
    # deterministic and free, but worse, taking the dense arm from 90% to 85%
    # hit@5 and MRR 0.656 to 0.615. The fused arm was unchanged at 92%, so the
    # pipeline may absorb it, but there was no quality case for the swap.
    #
    # "openai" means reuse `embedding_model` -- the same vectors the index is
    # built from, with the cache below handling its non-determinism. Any other
    # value is a sentence-transformers model name and runs locally. Changing
    # this changes where chunks split, so the index must be rebuilt and results
    # re-measured.
    #
    # Both were measured head to head, one variable, 40 questions:
    #
    #   bge-small (local)   judged precision 0.880   dense hit@5 85%
    #   openai (cached)     judged precision 0.810   dense hit@5 90%
    #
    # The local encoder wins by 0.07 of precision, more than twice the noise
    # floor, despite losing on the document-level dense arm. hit@5 only asks
    # whether an acceptable source is in the top 5; Contextual Precision scores
    # all five chunks by rank and punishes the irrelevant ones. OpenAI
    # boundaries find the right document more often and drag in more plausible
    # near-misses alongside it.
    #
    # So the local encoder is kept: better on the metric that counts, free, and
    # deterministic without needing the cache at all.
    boundary_encoder: str = "BAAI/bge-small-en-v1.5"
    # Cache boundary vectors by (model, text) hash. The OpenAI endpoint does not
    # return identical vectors for identical input at realistic batch sizes --
    # max|delta| 3.3e-03 over 66 windows -- which moves the percentile threshold
    # and flips boundaries sitting near it: two ingests of an unchanged corpus
    # gave 365 then 366 chunks. Caching makes a re-ingest read every vector back
    # byte-identical, so chunking becomes reproducible without giving up the
    # better boundaries. Reproducible *given the cache*: a cold cache on another
    # machine re-requests and may land a boundary differently.
    boundary_cache: bool = True

    # --- hybrid retrieval ---
    # Off by default. Turning it on changes the collection schema, so the index
    # has to be rebuilt -- the dense vector stops being anonymous and a sparse
    # vector sits beside it.
    hybrid_enabled: bool = True
    # Candidates each arm contributes before fusion. Dense and BM25 rank the same
    # corpus differently; RRF only sees the ranks, so this decides how deep each
    # opinion goes.
    hybrid_prefetch: int = 20

    # --- reranking ---
    # Off by default: turning it on changes what reaches the prompt, so it should
    # be a deliberate switch rather than something that arrives with an upgrade.
    rerank_enabled: bool = True
    # A cross-encoder reads (question, chunk) together instead of comparing two
    # separately-built vectors, so it can see that a chunk about renewal pricing
    # happens to contain a user count. It cannot be precomputed -- it runs once
    # per pair at query time -- which is why it reranks a shortlist rather than
    # the whole collection.
    # reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    # bge-base was measured and it was actively harmful once hybrid fusion was in
    # place: on the fused ordering it took rank-1 accuracy from 62% to 40% and
    # discarded six correct documents out of the top 5 entirely. It had helped at
    # +0.148 precision when it was fixing a dense-only ordering, which places the
    # answer first only ~50% of the time -- there was a lot to fix. RRF already
    # reaches 62%, so a weak cross-encoder overwrites a better ordering with its
    # own.
    #
    # bge-large preserves hit@5 and edges MRR up, and judged precision went
    # 0.800 -> 0.880 on the 40-question set. Costs 2.24GB against ~400MB and
    # about 13s more per eval run.
    reranker_model: str = "BAAI/bge-reranker-large"
    # How many candidates the vector search hands to the reranker. The dense
    # retriever's job becomes "get the answer into this many" rather than "rank it
    # first", which is the easier job it is already good at.
    rerank_candidates: int = 20

    # --- paths ---
    # Properties, not fields: these are derived from the repo layout, so there is
    # no reason to expose them to the environment.

    @property
    def corpus_dir(self) -> Path:
        return REPO_ROOT / "data" / "corpus"

    @property
    def fixtures_dir(self) -> Path:
        return REPO_ROOT / "eval" / "fixtures"

    @property
    def golden_dataset(self) -> Path:
        return REPO_ROOT / "eval" / "golden_dataset.json"

    @property
    def results_dir(self) -> Path:
        return REPO_ROOT / "eval" / "results"

    @property
    def boundary_cache_path(self) -> Path:
        # Kept rather than treated as scratch: deleting it does not corrupt
        # anything, but it does cost the reproducibility the cache exists for.
        return REPO_ROOT / "data" / "boundary_cache.sqlite"


# type: ignore[call-arg] -- pydantic-settings reads the required credentials from
# the environment, which a static checker cannot see, so it reads this as a call
# missing two arguments. Giving those fields defaults would silence it and throw
# away the reason they have none: failing loudly at import when a key is absent,
# instead of with a 401 twenty seconds into an ingest run.
settings = Settings()  # type: ignore[call-arg]