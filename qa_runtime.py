import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from qa_config import (
    ALLOWED_FAILURE_CATEGORIES,
    DEFAULT_LLM,
    FRAMEWORK_CONFIG,
    HTML_DEBUG_DIR,
    VECTOR_DB_DIR,
    get_llm,
    load_prompt_system,
    load_prompt_template,
)

load_dotenv()


def _setup_tracing() -> tuple:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
    auth = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip().replace("Authorization=", "", 1)
    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        headers={"Authorization": auth},
    )
    provider = TracerProvider(resource=Resource.create({"service.name": "ai-natural-language-tests"}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ai-natural-language-tests"), provider


tracer, _otel_provider = _setup_tracing()


def _setup_loki_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    _logger = logging.getLogger("ai-natural-language-tests")
    try:
        import logging_loki

        _logger.addHandler(
            logging_loki.LokiHandler(
                url=f"{os.getenv('GRAFANA_LOKI_URL').strip()}/loki/api/v1/push",
                tags={"service_name": "ai-natural-language-tests", "app": "ai-quality-lab"},
                auth=(os.getenv("GRAFANA_INSTANCE_ID").strip(), os.getenv("GRAFANA_API_TOKEN").strip()),
                version="1",
            )
        )
        _logger.info("[LOKI] Handler attached")
    except Exception as e:
        _logger.warning(f"[LOKI] Skipped: {e}")
    return _logger


logger = _setup_loki_logging()
_PATTERN_STORE: Optional["TestPatternStore"] = None


class TestPatternStore:
    """Simple FAISS + SQLite pattern store."""

    def __init__(self, db_name: str = "test_patterns.db") -> None:
        logger.info("Setting up FAISS + SQLite vector store")
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

        self.db_path = VECTOR_DB_DIR / db_name
        self.faiss_index_path = VECTOR_DB_DIR / "faiss_index"
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})

        self._init_sqlite()
        self.vectorstore = self._load_faiss_index()
        logger.info("FAISS + SQLite vector store ready")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _get_table_columns(self) -> set:
        with self._connect() as conn:
            rows = conn.execute("PRAGMA table_info(test_patterns)").fetchall()
            return {row[1] for row in rows}

    def _init_sqlite(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS test_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requirement TEXT NOT NULL,
                    url TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    test_code TEXT NOT NULL
                )
                """
            )
            conn.commit()

        columns = self._get_table_columns()
        if "test_code" not in columns:
            with self._connect() as conn:
                conn.execute("ALTER TABLE test_patterns ADD COLUMN test_code TEXT NOT NULL DEFAULT ''")
                conn.commit()

    def _load_faiss_index(self) -> Optional[FAISS]:
        if not self.faiss_index_path.exists():
            return None

        try:
            logger.info("Loading existing FAISS index")
            return FAISS.load_local(
                str(self.faiss_index_path),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
            return None

    def store_pattern(self, test_code: str, requirement: str, url: str, test_type: str, filepath: str) -> None:
        logger.info(f"Storing pattern: {requirement}")
        timestamp = datetime.now().isoformat()
        metadata = {
            "requirement": requirement,
            "url": url,
            "test_type": test_type,
            "filepath": filepath,
            "timestamp": timestamp,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO test_patterns (requirement, url, test_type, filepath, timestamp, test_code)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (requirement, url, test_type, filepath, timestamp, test_code),
            )
            conn.commit()

        doc = Document(page_content=test_code, metadata=metadata)
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents([doc], self.embeddings)
        else:
            self.vectorstore.add_documents([doc])

        self.vectorstore.save_local(str(self.faiss_index_path))
        logger.info("Pattern stored")

    def search_similar_patterns(self, requirement: str, k: int = 2) -> List[Document]:
        logger.info(f"Searching for patterns like: {requirement}")
        if self.vectorstore is None:
            return []

        try:
            results = self.vectorstore.similarity_search(requirement, k=max(1, k))
            logger.info(f"Found {len(results)} similar patterns")
            return results
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

    def get_all_patterns(self) -> List[Document]:
        logger.info("Retrieving all patterns")
        columns = self._get_table_columns()
        query = (
            """
            SELECT requirement, url, test_type, filepath, timestamp, test_code
            FROM test_patterns
            ORDER BY id DESC
            """
            if "test_code" in columns
            else """
            SELECT requirement, url, test_type, filepath, timestamp, '' AS test_code
            FROM test_patterns
            ORDER BY id DESC
            """
        )
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        return [
            Document(
                page_content=row[5],
                metadata={
                    "requirement": row[0],
                    "url": row[1],
                    "test_type": row[2],
                    "filepath": row[3],
                    "timestamp": row[4],
                },
            )
            for row in rows
        ]


def get_pattern_store() -> TestPatternStore:
    global _PATTERN_STORE
    if _PATTERN_STORE is None:
        _PATTERN_STORE = TestPatternStore()
    return _PATTERN_STORE


def fetch_html_content(url: str) -> str:
    logger.info(f"Fetching URL: {url}")
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    html = response.text[:5000]
    logger.info(f"Got {len(html)} characters of HTML")
    return html


def build_html_analysis_result(url: str, html: str, llm_provider: str) -> tuple[Dict[str, Any], str, str]:
    llm = get_llm(llm_provider)
    prompt = load_prompt_template("html_analysis.yaml", url=url, html=html)
    ai_response = llm.invoke(prompt)
    content = ai_response.content.strip()
    raw_response = content

    if "```" in content:
        content = content.split("```")[1].replace("json", "").strip()

    test_data = json.loads(content)
    return test_data, prompt, raw_response


def save_html_analysis_debug(payload: Dict[str, Any]) -> str:
    run_id = payload.get("run_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
    HTML_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    debug_path = HTML_DEBUG_DIR / f"{run_id}.json"
    payload["run_id"] = run_id
    with open(debug_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=True)
    return run_id


def load_html_analysis_debug(run_id: str) -> Dict[str, Any]:
    with open(HTML_DEBUG_DIR / f"{run_id}.json", "r", encoding="utf-8") as file:
        return json.load(file)


def list_html_replay_ids() -> List[str]:
    files = sorted(HTML_DEBUG_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [path.stem for path in files]


def build_run_command(framework: str, generated_tests: List, output_dir: str, use_prompt_mode: bool) -> str:
    fw = FRAMEWORK_CONFIG[framework]

    if framework == "playwright":
        specs = [f'"{t["filepath"]}"' for t in generated_tests if t.get("filepath", "").endswith(fw["file_ext"])]
        if specs:
            return f"npx playwright test {' '.join(specs)}"

        base_output = output_dir
        if output_dir == "cypress/e2e":
            base_output = fw["default_output"]
        return f"npx playwright test {base_output}/generated"

    if framework == "webdriverio":
        spec_paths = [t["filepath"] for t in generated_tests if t.get("filepath", "").endswith(fw["file_ext"])]
        spec_arg = ",".join(spec_paths)
        if spec_arg:
            return f'npx wdio run wdio.conf.js --spec "{spec_arg}"'
        return "npx wdio run wdio.conf.js"

    folder_name = "generated"
    if use_prompt_mode:
        folder_name = "prompt-powered"
    return f"npx cypress run --spec 'cypress/e2e/{folder_name}/**/*.cy.js'"


def build_failure_analysis_messages(log_text: str) -> List[Dict[str, str]]:
    system_content = load_prompt_system("failure_analysis.yaml")
    user_content = load_prompt_template("failure_analysis.yaml", log=log_text)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _read_value(content: str, key: str) -> str:
    prefix = f"{key}:"
    for line in content.splitlines():
        clean_line = line.strip()
        if clean_line.upper().startswith(prefix):
            return clean_line[len(prefix):].strip()
    return ""


FAILURE_DEFAULTS = {
    "REASON": "Unable to determine root cause from log; output did not include structured reason.",
    "FIX": "Add explicit waits/assertions around the failing step and verify selectors for the detected framework.",
}


def format_failure_analysis(content: str) -> str:
    category = _read_value(content, "CATEGORY").upper()
    reason = _read_value(content, "REASON") or FAILURE_DEFAULTS["REASON"]
    fix = _read_value(content, "FIX") or FAILURE_DEFAULTS["FIX"]
    if category not in ALLOWED_FAILURE_CATEGORIES:
        category = "CONFIGURATION"
    return f"CATEGORY: {category}\nREASON: {reason}\nFIX: {fix}"


def analyze_test_failure(log_text: str) -> str:
    with tracer.start_as_current_span("analyze_test_failure") as span:
        logger.info("Analyzing test failure")
        span.set_attribute("log_length", len(log_text))
        messages = build_failure_analysis_messages(log_text)
        llm = get_llm(DEFAULT_LLM)
        response = llm.invoke(messages)
        logger.info("Analysis complete")
        content = response.content if isinstance(response.content, str) else str(response.content)
        span.set_attribute("success", True)
        return format_failure_analysis(content)