import argilla as rg

from argilla.client.feedback.schemas import SuggestionSchema, SpanValueSchema

import json
import os

ARGILLA_API_URL = os.environ.get("ARGILLA_API_URL", "http://localhost:6900")
ARGILLA_API_KEY = os.environ.get("DEFAULT_USER_API_KEY", "argilla.apikey")


def construct_feedback_dataset() -> rg.FeedbackDataset:
    guidelines = """Select the spans associated with the background text for the case.

    Include terminal punctuation for full sentence spans.\n

    Use the following guidelines to select spans:\n:


    **Background Context**
    This is (ideally the maximal) case detail which is known at the time of the appeal review. This includes, but is not necessarily limited
    to, all details provided that describe the situation leading up to the adverse coverage denial, and all actions taken by the insurer
    before an appeal was submitted to an independent reviewer.


    **Note**: Spans (or subsections thereof) can be given multiple labels. For example, a diagnosis is likely to occur
    within background context.
    """

    ds = rg.FeedbackDataset(
        guidelines=guidelines,
        fields=[
            rg.TextField(name="case-summary", title="Case Summary"),
            rg.TextField(name="final-outcome", title="Final Outcome"),
        ],
        questions=[
            rg.SpanQuestion(
                name="case-spans",
                title="Highlight spans associated with the following quantities in the text:",
                labels={
                    "BC": "Background Context",
                    "DG": "Diagnosis",
                    "SVC": "Service",
                    "RV-DC": "Reviewer's Decision",
                },
                field="case-summary",
                required=True,
                visible_labels=4,
                allow_overlapping=True,
            ),
            rg.RatingQuestion(
                name="info-sufficiency",
                title="Is the Background Context you've highlighted sufficient to determine the case outcome?",
                description="Use a scale from 1 to 5, 1 being the information is certainly insufficient, 5 being certainly sufficient.",
                values=[1, 2, 3, 4, 5],
                required=False,
            ),
        ],
    )
    return ds


def make_workspace(ws_name: str) -> None:
    # Create workspace if it doesn't exist
    try:
        _workspace = rg.Workspace.create(ws_name)
    except ValueError:
        print(f"Skipping creation of workspace {ws_name} as it already exists.")

    return None


def construct_ds_records(jsonl_path: str, include_suggestions: bool) -> list:
    """From a standardized jsonl format (namely that of HICRIC processed files),
    construct a list of records to submit into an argilla dataset of the format above.
    """
    # Add records
    records = []
    with open(jsonl_path, "r") as jsonl_file:
        for idx, line in enumerate(jsonl_file):
            json_obj = json.loads(line)
            full_text = json_obj["text"]
            outcome = json_obj.get("decision", "unknown")

            # TODO: come up with some good initial rules
            if include_suggestions:
                background = ""
                justification = ""
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
                    "final-outcome": outcome,
                },
            )
            if include_suggestions:
                suggestions = (
                    [
                        SuggestionSchema(
                            question_name="case-spans",
                            value=[
                                SpanValueSchema(
                                    start=background_start,  # position of the first character of the span
                                    end=background_end,  # position of the character right after the end of the span
                                    label="BC",
                                    score=0.9,
                                )
                            ],
                            agent="annotator-bot-0.0.1",
                        ),
                    ],
                )
                record.suggestions = suggestions

            records.append(record)

    return records


if __name__ == "__main__":
    # Config
    include_suggestions = False  # Include suggestions

    rg.init(api_url=ARGILLA_API_URL, api_key=ARGILLA_API_KEY)

    # Make a workspace
    target_workspace = "case-summaries"
    make_workspace(target_workspace)

    rg.set_workspace(target_workspace)

    # Construct a dataset for each raw source:
    sources = [
        ("NY DFS External Appeal Database", "./data/processed/nydfs.jsonl"),
        ("CA CDI External Appeal Database", "./data/processed/ca_cdi/summaries/aggregate.jsonl"),
        (
            "CA DMHC External Appeal Database",
            "./data/processed/independent-medical-review-imr-determinations-trend.jsonl",
        ),
    ]

    for ds_name, path in sources:
        ds = construct_feedback_dataset()
        records = construct_ds_records(path, include_suggestions)
        ds.add_records(records)
        ds.push_to_argilla(name=ds_name, workspace=target_workspace)
