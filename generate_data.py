import argilla as rg

import json

ARGILLA_API_URL = "http://localhost:6900"
ARGILLA_API_KEY = "argilla.apikey"


def construct_feedback_dataset(
    workspace: str,
) -> rg.FeedbackDataset:
    pass


if __name__ == "__main__":
    rg.init(
        api_url=ARGILLA_API_URL,
        api_key=ARGILLA_API_KEY,
    )

    # Construct a dataset
    target_workspace = "argilla"

    # # Extractive QA dataset
    # extractive_qa_ds = rg.FeedbackDataset.for_question_answering(
    #     use_markdown=True,
    #     guidelines=None,
    #     metadata_properties=None,
    #     vectors_settings=None,
    # )

    # # Dataset to label liklihood of overturn

    # # Add records
    # records = []
    # jsonl_path = "./ny_dfs.jsonl"
    # with open(jsonl_path, "r") as jsonl_file:
    #     for idx, line in enumerate(jsonl_file):
    #         json_obj = json.loads(line)
    #         response = json_obj["response"].strip()
    #         record = rg.FeedbackRecord(
    #             fields={
    #                 "question": "What is the diagnosis in this appeal adjudication?",
    #                 "context": response,
    #             }
    #         )
    #         records.append(record)

    # extractive_qa_ds.add_records(records)

    # extractive_qa_ds.push_to_argilla(
    #     name="extractive-qa-test", workspace=target_workspace
    # )

    # rg.init(
    #     api_url=ARGILLA_API_URL,
    #     api_key=ARGILLA_API_KEY,
    # )

    # Span Based extractive QA dataset
    span_ds = rg.FeedbackDataset(
        fields=[rg.TextField(name="text")],
        questions=[
            rg.SpanQuestion(
                name="adjudication-spans",
                title="Highlight the entities in the text:",
                labels={
                    "DG": "Diagnosis",
                },
                field="text",
                required=True,
            )
        ],
    )

    # Dataset to label liklihood of overturn

    # Add records
    records = []
    jsonl_path = "./ny_dfs.jsonl"
    with open(jsonl_path, "r") as jsonl_file:
        for idx, line in enumerate(jsonl_file):
            json_obj = json.loads(line)
            response = json_obj["response"].strip()
            record = rg.FeedbackRecord(
                fields={
                    # "question": "What is the diagnosis in this appeal adjudication?",
                    "text": response,
                }
            )
            records.append(record)

    span_ds.add_records(records)

    span_ds.push_to_argilla(name="adjudication-spans", workspace=target_workspace)

    # RAG dataset
    # rag_ds = rg.FeedbackDataset.for_retrieval_augmented_generation(
    #     number_of_retrievals=1,
    #     rating_scale=7,
    #     use_markdown=False,
    #     guidelines=None,
    #     metadata_properties=None,
    #     vectors_settings=None,
    # )
