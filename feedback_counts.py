"""Count recorded trivia feedback and verify it belongs to session traces."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from logfire.query_client import LogfireQueryClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default="2026-10-23T18:11:00+00:00")
    args = parser.parse_args()
    credentials = json.loads(Path(".logfire/read_token.json").read_text())
    if (credentials["organization"], credentials["project_name"]) != ("micah-sircularity", "demo-test"):
        raise ValueError("Expected credentials for micah-sircularity/demo-test")
    with LogfireQueryClient(read_token=credentials["token"], base_url=credentials["base_url"]) as client:
        result = client.query_json_rows(
            sql="""
                SELECT f.attributes->>'feedback' AS feedback,
                       count(*) AS events,
                       count(DISTINCT f.trace_id) AS sessions,
                       count(s.span_id) AS attached_to_session
                FROM records f
                LEFT JOIN records s ON f.trace_id = s.trace_id
                    AND f.parent_span_id = s.span_id
                    AND s.span_name = 'trivia_session' AND s.kind = 'span'
                WHERE f.kind = 'log'
                    AND f.service_name = 'homework-monitoring'
                    AND f.attributes->>'event_type' = 'trivia_feedback'
                GROUP BY f.attributes->>'feedback'
                ORDER BY feedback DESC
                LIMIT 10
            """,
            min_timestamp=datetime.fromisoformat(args.since),
        )
    print(json.dumps(result["rows"], indent=2))


if __name__ == "__main__":
    main()
