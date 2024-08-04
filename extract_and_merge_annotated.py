import argparse
import json
import uuid


def construct_squad_format_ex(rec: dict, question_name: str) -> dict | None:
    context = rec["case-summary"]
    question = "What is the background context in this case summary?"  # Q doesn't matter except for initial bootstrap
    id = uuid.uuid4().hex
    answers = get_background_answers(rec, question_name)
    if len(answers) == 0:
        answers.append({"answer_start": -1, "text": ""})
    return {"answers": answers, "context": context, "id": id, "question": question, "title": id}


def get_background_answers(rec: dict, question_name: str) -> list[dict]:
    """For a given record, collect answer spans corresponding to background
    context"""

    answers = {}
    annotations = rec[question_name]
    answer_texts = []
    answer_starts = []

    if len(annotations) > 0:
        span_vals = annotations[0]["value"]
        labels = span_vals["label"]
        for idx, label in enumerate(labels):
            if label == "BC":  # background
                answer_text = span_vals["text"][idx]

                # Something went wrong if we are using annotations
                # that have this terminology
                if "overturned" in answer_text or "upheld" in answer_text:
                    continue

                answer_start = span_vals["start"][idx]
                answer_texts.append(answer_text)
                answer_starts.append(answer_start)
    answers = {"text": answer_texts, "answer_start": answer_starts}
    return answers


def main(annotated_jsonl_paths: list[str], outpath: str) -> None:
    # Combine records from multiple dumped paths
    all_recs = []
    for path in annotated_jsonl_paths:
        with open(path, "r") as f:
            recs = f.readlines()
            recs = [json.loads(rec) for rec in recs]
            all_recs.extend(recs)

    # Isolate only those records for which a background context annotation was made
    question_name = "case-spans"
    annotated_recs = [
        rec
        for rec in all_recs
        if len(rec[question_name]) > 0 and rec[question_name][0].get("status", "unkown") != "discarded"
    ]

    # TODO: add option to filter by sufficiency scores here

    # Construct list of squad dicts
    squad_dicts = []
    for rec in annotated_recs:
        out = construct_squad_format_ex(rec, question_name)
        if out:
            squad_dicts.append(out)

    # Write out
    with open(outpath, "w") as f:
        for rec in squad_dicts:
            f.write(json.dumps(rec) + "\n")

    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annotated_jsonl_paths",
        nargs="+",
        default=[],
        help="List of jsonl argilla dump paths to merge.",
    )
    parser.add_argument(
        "--outpath",
        type=str,
        default=None,
        help="Optional output path.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    args_dict = vars(args)
    main(**args_dict)
