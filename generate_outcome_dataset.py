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
    
  This is (ideally the maximal) case detail which is known at the time of the appeal *submission*. This includes, but is not necessarily limited to, all details provided that describe the situation leading up to the adverse coverage denial, and all actions taken by the insurer *before* an appeal was submitted to an independent reviewer. This should not include information which leaks the adjudication outcome, which constitutes the opinion of the reviewer, or which could not be known prior to appeal submission.  
    
- **Diagnosis**  
    
  This should be some indication of the diagnosis associated with an appeal. It could be a diagnosis code, a plain text but precise description, or a broad category of diagnoses (e.g. "cancer"). Some reviews do not detail the relevant diagnosis.  
    
- **Service**  
    
  This should be some indication of the service associated with an appeal. It could be a procedure code, a plain text but precise description, or a broad category of services (e.g. "oral surgery"). Some reviews do not detail the relevant services.  
    
- **Reviewer's Decision**  
    
  This should be some indication of the decision of the reviewer writing the summary. This could be a single sentence in the review such as "The insurer's denial should be Overturned", or a more implicit decision, such as "The insurer did not act in the best interest of the patient". Note that reviewer's decisions need not agree with the final outcome, as sometimes multiple reviewers vote on the outcome in a majority rule fashion.

*Note*: Spans (or subspans) can be given multiple labels, or zero labels. The labels are not mutually exclusive, nor are they exhaustive. For example, a diagnosis is likely to occur *within* background context.

## **Background Sufficiency**

### General Guidance

Rate the selected background context span on a scale from 1 to 4, to indicate the degree to which the background context alone is sufficient to make an informed guess about the likelihood of denial overturn.

#### Additional Details

This is a highly subjective matter. In general, none of the case descriptions included in these datasets are sufficient to make case adjudication determinations or accurately predict perfectly what the decisions are likely to be. This is because they uniformly lack context such as diagnosis and procedural codes, office and chart notes, detailed patient medical history, information about the exact legal jurisdiction relevant to the case, a full copy of the insured's insurance contract, etc, etc.

The goal here is to nonetheless assign *relative* sufficiency scores from 1-4, that adhere to a consistent relative annotation standard for any given annotator. Any differences that might arise in the relative scales used by different annotators will be evaluated and controlled for after the fact.

As normalizing guideposts, let's begin by discussing the extreme cases. It is clear, for example, that some case description backgrounds are completely insufficient to make an informed guess about overturn likelihood. For example, some case backgrounds say only completely general things like "A patient was denied inpatient admission". There are a multitude of reasons why one could be denied inpatient admission that would result in overturn and a multitude of reasons that would not. Cases with only such completely unspecified backgrounds should receive a score of 1\. On the other hand, the most detailed case backgrounds will include detailed diagnosis and service descriptions, as well as lengthy, detailed explanation about what led to the care event, what the patient's medical records suggest about the medical details of the event, why the insurer has issued a denial, and why the patient or physician believes overturn is merited. Such cases should generally receive a score of 4.

Let's now turn to a specific rubric we've developed to help make the sufficiency determination. We reiterate what was stated earlier: a score of 4 does *not* mean that a case background description is sufficient to determine whether a case will be overturned. It simply means that it belongs to the class of background descriptions which is closest to sufficient, relative to other background descriptions.

| Score | Criteria | Example Selection |
| :---- | :---- | :---- |
| 1 | Little to no specific context for the denial is provided. The description can easily be extended to describe cases meriting coverage, and extended to describe cases not meriting coverage. Neither a specific condition, specific service or treatment, nor specific drug is stated in the description. | "A patient was denied coverage for an inpatient admission." |
| 2 | Some specific context for the denial is provided, but the information can still be easily extended to describe cases meriting coverage, and extended to cases not meriting coverage. At a minimum, the description mentions either the specific condition / medical situation being treated, *or* the specific service / treatment. | "An enrollee has requested bilateral sacroiliac (SI) joint fusion surgery for treatment of her medical condition." |
| 3 | Some specific context for the denial is provided. The information may or may not be able to be easily extended to describe cases meriting coverage and extended to cases not meriting coverage. Understanding whether or not such dual extension is possible may require medical expertise. At a minimum, the description mentions the specific condition / medical situation being treated, *and* the specific service / treatment. | "The parent of a male enrollee has requested authorization and coverage for immunotherapy with nivolumab (Opdivo). The Health Plan has denied this request indicating that the requested medication is considered investigational for treatment of the enrollees grade IV glioblastoma." |
| 4 | Some context for the denial has been provided. At a minimum the context includes the condition / medical situation being treated, and the service / treatment being used, and at some description of the specific events or rationale leading to the coverage request. | "An enrollee requested a power seat elevator for her power wheelchair for treatment of the enrollee, who has a history of a spinal cord injury. With power seat elevation, the patient would be able to adjust the seat of her wheelchair to be level with the transfer surface, to perform a level surface transfer independently with a sliding board." |
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
                title="Is the Background Context you've highlighted sufficient to make an informed prediction for the case outcome?",
                description="Use a scale from 1 to 4, 1 being least sufficient, 4 being most sufficient.",
                values=[1, 2, 3, 4],
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
                annotations[context] = {
                    "answers": answers,
                    "sufficiency_score": sufficiency_score
                    if sufficiency_score <= 4
                    else 4,  # Convert old 1-5 scores to new 1-4 scores
                }

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
                    values = {
                        "case-spans": {"value": span_values},
                        "info-sufficiency": {"value": sufficiency_score},
                    }

                    record.responses = [
                        {
                            "user_id": add_to_userid,
                            "values": values,
                            "status": "submitted",
                        }
                    ]

                    records.append(record)

                else:
                    continue

            # if include_suggestions:
            #     suggestions = (
            #         [
            #             SuggestionSchema(
            #                 question_name="case-spans",
            #                 value=[
            #                     SpanValueSchema(
            #                         start=background_start,  # position of the first character of the span
            #                         end=background_end,  # position of the character right after the end of the span
            #                         label="BC",
            #                         score=0.9,
            #                     )
            #                 ],
            #                 agent="annotator-bot-0.0.1",
            #             ),
            #         ],
            #     )
            #     record.suggestions = suggestions

    return records


if __name__ == "__main__":
    # Config
    include_suggestions = False  # Include suggestions

    rg.init(api_url=ARGILLA_API_URL, api_key=ARGILLA_API_KEY)

    # Make a workspace
    target_workspace = "hicric"
    make_workspace(target_workspace)

    rg.set_workspace(target_workspace)

    # Construct a dataset for each raw source:
    sources = [
        ("NY DFS External Appeal Database", "./data/processed/nydfs.jsonl"),
        (
            "CA CDI External Appeal Database",
            "./data/processed/ca_cdi/summaries/aggregate.jsonl",
        ),
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
