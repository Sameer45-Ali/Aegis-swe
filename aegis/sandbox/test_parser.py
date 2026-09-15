"""
Pytest and Unittest Output Parser.
Extracts passed/failed/errored counts, failure tracebacks, and assertion mismatches.
"""

import re
from typing import Dict, List, Optional, Tuple


class TestOutputParser:
    """Parses standard pytest and unittest output into structured metrics."""

    @staticmethod
    def parse_pytest(stdout: str, stderr: str) -> Dict[str, any]:
        combined = f"{stdout}\n{stderr}"
        
        passed = 0
        failed = 0
        errored = 0

        # Pattern: "= 1 passed, 2 failed in 0.12s ="
        summary_match = re.search(r"=\s*(.*?)\s+in\s+[\d\.]+s", combined)
        if summary_match:
            summary_text = summary_match.group(1)
            
            p_match = re.search(r"(\d+)\s+passed", summary_text)
            if p_match:
                passed = int(p_match.group(1))

            f_match = re.search(r"(\d+)\s+failed", summary_text)
            if f_match:
                failed = int(f_match.group(1))

            e_match = re.search(r"(\d+)\s+error", summary_text)
            if e_match:
                errored = int(e_match.group(1))
        else:
            # Fallback patterns
            if "PASSED" in combined:
                passed = len(re.findall(r"::[\w_]+\s+PASSED", combined)) or 1
            if "FAILED" in combined:
                failed = len(re.findall(r"::[\w_]+\s+FAILED", combined)) or 1
            if "ERROR" in combined:
                errored = len(re.findall(r"::[\w_]+\s+ERROR", combined)) or 1

        # Extract failure tracebacks
        failures = []
        failure_blocks = re.findall(r"_{10,}\s+(.*?)\s+_{10,}(.*?)(?=(?:_{10,}|$))", combined, re.DOTALL)
        for name, trace in failure_blocks:
            clean_trace = "\n".join([line for line in trace.splitlines() if line.strip()][-12:])
            failures.append(f"FAILED: {name.strip()}\n{clean_trace}")

        return {
            "passed": passed,
            "failed": failed,
            "errored": errored,
            "total": passed + failed + errored,
            "is_all_passed": (passed > 0 and failed == 0 and errored == 0),
            "failures": failures[:5],
            "raw_summary": summary_match.group(0) if summary_match else ("All Passed" if passed > 0 and failed == 0 else "Execution Completed")
        }
