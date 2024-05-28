import json

import argilla as rg
from argilla.client.feedback.schemas import ResponseSchema, SpanValueSchema

ARGILLA_API_URL = "http://localhost:6900"
ARGILLA_API_KEY = "argilla.apikey"


# Construct dataset chema (TODO: do this in an automated way by exporting schema at dump time)
# For now, hardcoded:
def construct_feedback_dataset() -> rg.FeedbackDataset:
    guidelines = """Select the spans for all specified subsections of the text, if they exist. TODO: specify punctuation rules, etc.\n

    Include terminal punctuation for full sentence spans.\n

    Use the following guidelines to select spans:\n:


    **Background Context**
    This is the maximal case detail which is known at the time of the appeal review. This includes, but is not necessarily limited
    to, all details provided that describe the situation leading up to the adverse coverage denial, and all actions taken by the insurer
    before an appeal was submitted to an independent reviewer.


    **Note**: Spans (or subsections thereof) can be given multiple labels. For example, a diagnosis is likely to occur
    within background context.
    """

    # Span Based extractive QA dataset
    ds = rg.FeedbackDataset(
        guidelines=guidelines,
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
                allow_overlapping=True,
            )
        ],
    )
    return ds


if __name__ == "__main__":
    # Load annotated dataset stored in HF datasets format
    annotated_ds_path = "./data/annotated/case-summaries.jsonl"

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

    name = "case-summaries"
    ds = construct_feedback_dataset()

    # Construct a dataset
    target_workspace = "case-summaries"

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

    name = "case-summaries"
    ds = construct_feedback_dataset()

    # Add records
    records = []
    with open(annotated_ds_path, "r") as jsonl_file:
        for idx, line in enumerate(jsonl_file):
            json_obj = json.loads(line)
            full_text = json_obj["case-summary"]
            market_segment = json_obj["market-segment"]
            outcome = json_obj["final-outcome"]

            response_jsons = json_obj["case-summary-spans"]

            responses = []
            for response_json in response_jsons:
                span_starts = response_json["value"]["start"]
                span_ends = response_json["value"]["end"]
                span_labels = response_json["value"]["label"]

                values = {
                    "case-spans": {
                        "value": [
                            SpanValueSchema(start=start, end=end, label=label)
                            for (start, end, label) in zip(
                                span_starts, span_ends, span_labels
                            )
                        ]
                    }
                }
                response = ResponseSchema(values=values)

                responses.append(response)

            record = rg.FeedbackRecord(
                fields={
                    "case-summary": full_text,
                    "market-segment": market_segment,
                    "final-outcome": outcome,
                },
                responses=responses,
            )

            records.append(record)

    ds.add_records(records)

    ds.push_to_argilla(name=name, workspace=target_workspace)
