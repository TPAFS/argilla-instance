import argilla as rg

from argilla.client.feedback.schemas import SuggestionSchema, SpanValueSchema

import json

ARGILLA_API_URL = "http://localhost:6900"
ARGILLA_API_KEY = "argilla.apikey"

def construct_feedback_dataset() -> rg.FeedbackDataset:
    # Span Based extractive QA dataset
    ds = rg.FeedbackDataset(
        guidelines="Select the spans for all specified subsections of the text, if they exist.",
        fields=[
            rg.TextField(name="case-summary", title="Case Summary"),
            rg.TextField(name="market-segment", title="Market Segment"),
            rg.TextField(name="final-outcome", title="Final Outcome"),
        ],
        questions=[
            rg.SpanQuestion(
                name="case-spans",
                title="Highlight the entities in the text:",
                labels={
                    "BC": "Background Context",
                    "DG": "Diagnosis",
                    "SVC": "Service",
                    "RTL": "Adjudication Rationale",
                    "OUTCOME": "Adjudication Recommendation",
                    "DNLRTL": "Denial Rationale",
                },
                field="case-summary",
                required=True,
                visible_labels=6,
                allow_overlapping=True
            )
        ],
    )
    return ds


if __name__ == "__main__":
    # Construct a dataset
    target_workspace = "case-outcomes"

    # Create workspace if it doesn't exist
    try:
        workspace = rg.Workspace.create(target_workspace)
    except ValueError:
        pass

    rg.init(
        api_url=ARGILLA_API_URL, api_key=ARGILLA_API_KEY, workspace=target_workspace
    )

    # Create new users
    # user = rg.User.create(
    #     username="new-user",
    #     first_name="New",
    #     last_name="User",
    #     password="new-password",
    #     role="admin",
    #     workspaces=["ws1", "ws2"])

    name = "case-outcomes"
    ds = construct_feedback_dataset()

    # Add records
    records = []
    jsonl_path = "./data/outcomes/nydfs.jsonl"
    with open(jsonl_path, "r") as jsonl_file:
        for idx, line in enumerate(jsonl_file):
            json_obj = json.loads(line)
            full_text = json_obj["text"]
            appeal_type = json_obj["appeal_type"]
            outcome = json_obj["decision"]
            background = json_obj["background"]
            justification = json_obj["justification"]

            # Calculate start / end indices
            background_start = full_text.index(background)
            background_end = background_start + len(background)
            if background_start >= background_end:
                continue

            justification_start = full_text.index(justification)
            justification_end = justification_start + len(justification)
            if justification_start >= justification_end:
                continue

            record = rg.FeedbackRecord(
                fields={
                    "case-summary": full_text,
                    "market-segment": appeal_type,
                    "final-outcome": outcome,
                },
                suggestions=[
                    SuggestionSchema(
                        question_name="case-spans",
                        value=[
                            SpanValueSchema(
                                start=background_start,  # position of the first character of the span
                                end=background_end,  # position of the character right after the end of the span
                                label="BC",
                                score=0.9,
                            ),
                            SpanValueSchema(
                                start=justification_start,  # position of the first character of the span
                                end=justification_end,  # position of the character right after the end of the span
                                label="RTL",
                                score=0.9,
                            ),
                        ],
                        agent="nydfs-manual-rules-v0.0.0",
                    ),
                ],
            )
            records.append(record)

    ds.add_records(records)

    ds.push_to_argilla(name=name, workspace=target_workspace)
