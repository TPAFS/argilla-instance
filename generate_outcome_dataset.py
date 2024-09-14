import argilla as rg

from argilla.client.feedback.schemas import SuggestionSchema, SpanValueSchema

import json
import os

ARGILLA_API_URL = os.environ.get("ARGILLA_API_URL", "http://localhost:6900")
ARGILLA_API_KEY = os.environ.get("ARGILLA_API_KEY", "argilla.apikey")


def construct_feedback_dataset() -> rg.FeedbackDataset:
    guidelines = """

    ## **Span Selection**

    ### General Guidance
    Select spans associated with each of four token-type classes.

    The four token-types, and guideline descriptions for each are:

    - **Background Context**

    This is (ideally the maximal) case detail which is known at the time of the appeal review. This includes, but is not necessarily limited to, all details provided that describe the situation leading up to the adverse coverage denial, and all actions taken by the insurer _before_ an appeal was submitted to an independent reviewer. This should not include information which leaks the adjudication outcome, which constitutes the opinion of the reviewer, or which could not be known prior to appeal submission.

    - **Diagnosis**

    This should be some indication of the diagnosis associated with an appeal. It could be a diagnosis code, a plain text but precise description, or a broad category of diagnoses (e.g. "cancer"). Some reviews do not detail the relevant diagnosis.

    - **Service**

    This should be some indication of the service associated with an appeal. It could be a procedure code, a plain text but precise description, or a broad category of services (e.g. "oral surgery"). Some reviews do not detail the relevant services.

    - **Reviewer's Decision**

    This should be some indication of the decision of the reviewer writing the summary. This could be a single sentence in the review such as "The insurer's denial should be Overturned", or a  more implicit decision, such as "The insurer did not act in the best interest of the patient". Note that reviewer's decisions need not agree with the final outcome, as sometimes multiple reviewers vote on the outcome in a majority rule fashion.


    _Note_: Spans (or subspans) can be given multiple labels, or zero labels. The labels are not mutually exclusive, nor are they exhaustive. For example, a diagnosis is likely to occur _within_ background context.

    #### Additional Details

    -  Include terminal punctuation for full sentence spans.
    - The background context span labeling task is particularly subtle, as there are often summary descriptions of background context made by a reviewer imbued with potentially leaking, opinion based, or subjective language. When in doubt about whether a background span leaks the adjudication rationale or decision of a reviewer, do **not** highlight the background context.

    ## **Background Sufficiency**

    ### General Guidance

    Rate the selected background context span on a scale from 1 to 5, to indicate the degree to which the background context alone is sufficient to make an informed guess about the likelihood of denial overturn.

    #### Additional Details
    This is a highly subjective matter. In general, none of the case descriptions included in these datasets are completely sufficient to make case adjudication determinations of accurately predict perfectly what the decisions are likely to be. This is because they uniformly lack context such as diagnosis and procedural codes, office and chart notes, patient medical history, etc, etc.

    The goal here is primarily to retain _relative_ sufficiency estimates, on a per-annotator basis.

    As normalizing guideposts, let's discuss the extreme cases. It is clear, for example, that some case description backgrounds are completely insufficient to make an informed guess about overturn likelihood. For example, some case backgrounds say only completely general things like "A patient was denied inpatient admission". There are a multitude of reasons why one could be denied inpatient admission that would result in overturn and a multitude of reasons that would not. Cases with only such completely unspecific backgrounds should receive a score of 1. On the other hand, the most detailed case backgrounds will include detailed diagnosis and service descriptions, as well as lengthy, detailed explanation about what led to the care event, what the patient's medical records suggest about the medical details of the event, why the insurer has issued a denial, and wh"""

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
                title="Is the Background Context you've highlighted sufficient to make an informed prediction for the case outcome?",
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

    add_existing_annotations = True
    add_to_userid = str(rg.User.me().id)  # Add existing annotations to user running script

    # Used to add previously annotated records
    if add_existing_annotations:
        annotations = {}
        with open("./data/annotated/case-summaries-w-sufficiency.jsonl", "r") as jsonl_file:
            for idx, line in enumerate(jsonl_file):
                json_obj = json.loads(line)
                context = json_obj["context"].strip()
                answers = json_obj.get("answers")
                sufficiency_score = json_obj.get("sufficiency_score")
                annotations[context] = {"answers": answers, "sufficiency_score": sufficiency_score}

    # Add records
    records = []
    with open(jsonl_path, "r") as jsonl_file:
        for _idx, line in enumerate(jsonl_file):
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

            # Used to add previously annotated records
            if add_existing_annotations:
                if full_text.strip() in annotations:
                    existing_annotations = annotations[full_text.strip()]
                    answers = existing_annotations["answers"]
                    sufficiency_score = existing_annotations["sufficiency_score"]
                    texts = answers["text"]
                    starts = answers["answer_start"]
                    ends = [start + len(text) for (start, text) in zip(starts, texts)]

                    span_values = [
                        SpanValueSchema(
                            start=start,  # position of the first character of the span
                            end=end,  # position of the character right after the end of the span
                            label="BC",
                        )
                        for (start, end) in zip(starts, ends)
                    ]
                    values = {"case-spans": {"value": span_values}, "info-sufficiency": {"value": sufficiency_score}}

                    record.responses = [
                        {
                            "user_id": add_to_userid,
                            "values": values,
                            "status": "submitted",
                        }
                    ]

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
