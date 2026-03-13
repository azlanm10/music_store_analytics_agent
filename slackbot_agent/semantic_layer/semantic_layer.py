"""
Semantic layer: pai.create() to register, pai.load() to get datasets, then Agent(sources).

Flow: for each table/view, pai.load(path). If not found, read schema.yaml → pai.create() → pai.load(path).
Sources list contains only what pai.load() returns; never append the return value of pai.create().

After changing schema YAML: restart the app. On startup we clear PandasAI cache/registry.
"""

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pandasai as pai
import yaml

logger = logging.getLogger(__name__)

# Folder names use hyphens (e.g. datasets/chinook/invoice-line/schema.yaml). Matches PandasAI path rules.
DATASET_NAMES = [
    "album",
    "artist",
    "customer",
    "employee",
    "genre",
    "invoice",
    "invoice-line",
    "media-type",
    "playlist",
    "playlist-track",
    "track",
    "music-analytics",
]


def _base_dir() -> Path:
    """Project root datasets/chinook: __file__ -> .../slackbot_agent/semantic_layer -> parent.parent.parent = slackbot."""
    return Path(__file__).resolve().parent.parent.parent / "datasets" / "chinook"


def _db_connection() -> dict[str, Any]:
    """DB config from env (used when building sources from YAML)."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASS", ""),
    }


def _columns_from_yaml(columns: list) -> list[dict]:
    """
    Turn YAML column list into list of dicts for pai.create.
    - Do not pass alias (avoids sqlglot "AS Album ID" parse errors from any cached schema).
    - Skip columns with expression (measures) so load_head() doesn't SELECT them without GROUP BY.
    """
    out = []
    for c in columns or []:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        if c.get("expression"):
            continue  # measure column; omit so load_head() doesn't SELECT it without GROUP BY
        col = {"name": c["name"]}
        if c.get("type"):
            t = c["type"].lower().strip()
            col["type"] = "float" if t == "number" else t
        if c.get("description"):
            col["description"] = c["description"]
        # Do not pass alias to pai.create(); keeps generated SQL parseable and avoids stale-registry issues
        out.append(col)
    return out


def _clear_pandasai_registry() -> None:
    """
    Clear all known PandasAI cache/registry paths so pai.create() re-registers from YAML.
    Fixes: load_head() failing with "AS AlbumID" + COUNT (stale schema with aliases and measures).
    """
    try:
        pai.clear_cache()
    except Exception:  
        pass
    project_root = Path(__file__).resolve().parent.parent.parent
    # Project and home .pandasai and cache.db
    to_remove: list[tuple[Path, str]] = []
    to_remove.append((project_root / "cache" / "cache.db", "file"))
    to_remove.append((project_root / ".pandasai", "dir"))
    to_remove.append((Path.home() / ".pandasai", "dir"))
    # Virtualenv ( Poetry puts venvs in pypoetry Cache ); registry may live under venv
    try:
        venv_base = Path(sys.prefix)
        if venv_base and venv_base.exists():
            to_remove.append((venv_base / ".pandasai", "dir"))
            to_remove.append((venv_base / "cache" / "cache.db", "file"))
    except Exception:  # noqa: S110
        pass
    for path, kind in to_remove:
        try:
            if kind == "dir" and path.is_dir():
                shutil.rmtree(path)
                logger.info("Removed PandasAI registry: %s", path)
            elif kind == "file" and path.is_file():
                path.unlink()
                logger.info("Removed PandasAI cache: %s", path)
        except OSError as e:
            logger.debug("Could not remove %s: %s", path, e)


def load_sources() -> list[Any]:
    """
    pai.create() to register each dataset, then pai.load(path) per dataset.
    Returns list of what pai.load() returns; pass to Agent(sources). Never use pai.create() return value.
    Clears PandasAI cache at start so a fresh run picks up current schema (like restarting the kernel).
    """
    base = _base_dir()
    connection = _db_connection()
    sources = []

    for name in DATASET_NAMES:
        path_str = f"chinook/{name}"
        path = base / name / "schema.yaml"

        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            desc = data.get("description", f"Chinook: {name}")
            if isinstance(desc, list):
                desc = " ".join(str(x).strip() for x in desc).strip() or f"Chinook: {name}"
            desc = str(desc).strip() or f"Chinook: {name}"
            columns = _columns_from_yaml(data.get("columns", []))

            try:
                if data.get("view"):
                    relations = [
                        {"name": r["name"], "from": r["from"], "to": r["to"]}
                        for r in data.get("relations", [])
                        if isinstance(r, dict)
                    ]
                    pai.create(
                        path=path_str,
                        description=desc,
                        view=True,
                        columns=columns,
                        relations=relations,
                    )
                else:
                    table = (data.get("source") or {}).get("table") or name.replace("-", "_")
                    pai.create(
                        path=path_str,
                        description=desc,
                        source={"type": "postgres", "connection": connection, "table": table},
                        columns=columns,
                    )
                loaded = pai.load(path_str)
                if loaded is not None:
                    if isinstance(loaded, list):
                        sources.extend(loaded)
                    else:
                        sources.append(loaded)
                    logger.info("Dataset loaded successfully: %s", path_str)
                else:
                    logger.warning("pai.load(%s) returned None after create; not added to sources", path_str)
            except Exception as e:
                if "already exists" in str(e).lower() or "exist" in str(e).lower():
                    try:
                        loaded = pai.load(path_str)
                        if loaded is not None:
                            sources.extend(loaded) if isinstance(loaded, list) else sources.append(loaded)
                            logger.info("Dataset loaded successfully: %s", path_str)
                        else:
                            logger.warning(
                                "pai.load(%s) returned None (dataset already exists but load gave nothing); not added to sources",
                                path_str,
                            )
                    except Exception as load_err:
                        logger.warning("Dataset already exists at %s, pai.load failed: %s", path_str, load_err)
                else:
                    raise
            continue

        try:
            loaded = pai.load(path_str)
            if loaded is not None:
                if isinstance(loaded, list):
                    sources.extend(loaded)
                else:
                    sources.append(loaded)
                logger.info("Dataset loaded successfully: %s", path_str)
        except Exception:
            logger.warning("Missing: %s and pai.load failed", path)

    expected = len(DATASET_NAMES)
    if len(sources) < expected:
        logger.warning(
            "Only %d/%d sources in list (expected chinook/album and the other %d). Missing ones: pai.load() may have returned None.",
            len(sources),
            expected,
            expected - 1,
        )
    else:
        logger.info("Loaded %d sources (all chinook tables + music_analytics)", len(sources))
        logger.info("Sources: %s", sources)
    return sources
