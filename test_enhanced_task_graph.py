#!/usr/bin/env python3
"""Credential-dependent smoke test using a public AcademyBugs fixture."""

import json
import logging
import os
from pathlib import Path

from src.ingestion.task_graph_generator import TaskGraphGenerator
from src.scripts.convert_to_standard_input import convert_generic_test_case

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_enhanced_task_graph_generator():
    """Generate a task graph from the first public AcademyBugs example."""
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is required for this smoke test")

    with open("academybugs_bug_reports.json", "r", encoding="utf-8") as source_file:
        public_cases = json.load(source_file)

    bug_data = convert_generic_test_case(public_cases[0])
    output_dir = Path("data/test_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = TaskGraphGenerator(output_dir=str(output_dir), log_level=logging.INFO)
    task_graph = generator.generate_task_graph(bug_data)

    output_file = output_dir / "academybugs_task_graph_test_result.json"
    with open(output_file, "w", encoding="utf-8") as result_file:
        json.dump(task_graph, result_file, indent=2)

    logger.info("Task graph saved to %s", output_file)
    return task_graph


if __name__ == "__main__":
    run_enhanced_task_graph_generator()
