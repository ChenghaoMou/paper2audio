import os
from collections import Counter, defaultdict

import fitz
import numpy as np
import regex as re
import torch
from transformers import (
    AutoTokenizer,
    LayoutLMv2ForTokenClassification,
    LayoutLMv2ImageProcessor,
)
from alive_progress import alive_bar

os.environ["TOKENIZERS_PARALLELISM"] = "false"

model_id = (
    "pierreguillou/layout-xlm-base-finetuned-with-DocLayNet-base-at-linelevel-ml384"
)
tokenizer_id = "xlm-roberta-base"
model = LayoutLMv2ForTokenClassification.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)
feature_extractor = LayoutLMv2ImageProcessor(apply_ocr=False)

id2label = model.config.id2label
label2id = model.config.label2id
num_labels = len(id2label)

citations = re.compile(
    r"\(([; ]*((?:\p{Uppercase_Letter}[\p{Alphabetic}'`-]+)(?:,? (?:(?:and |& )?(?:\p{Uppercase_Letter}[\p{Alphabetic}'`-]+)|(?:et al.?)))*(?:, *(?:19|20)[0-9][0-9][a-f,]?(?:, p.? [0-9]+)?| *\((?:19|20)[0-9][0-9][a-f,]?(?:, p.? [0-9]+)?\))))+\)",
    re.IGNORECASE,
)

inline_ciations = re.compile(r"\[[0-9, ]+\]")


def extract_data(path):
    doc = fitz.open(path)
    data = []
    nested_data = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )

    for p, page in enumerate(doc):
        page_height = page.rect.height
        page_width = page.rect.width
        page_data = []
        page_image = page.get_pixmap()
        page_image = np.frombuffer(page_image.samples, dtype=np.uint8).reshape(
            page_image.h, page_image.w, 3
        )
        for b, block in enumerate(page.get_text("rawdict")["blocks"]):
            if block["type"] != 0:
                continue
            for l, line in enumerate(block["lines"]):
                s = 0
                for span in line["spans"]:
                    for char in span["chars"]:
                        if not char["c"].isprintable():
                            continue
                        page_data.append(
                            {
                                "x0": int(char["bbox"][0] / page_width * 1000),
                                "y0": int(char["bbox"][1] / page_height * 1000),
                                "x1": int(char["bbox"][2] / page_width * 1000),
                                "y1": int(char["bbox"][3] / page_height * 1000),
                                "c": char["c"],
                                "page": p,
                                "block": b,
                                "line": l,
                                "span": s,
                            }
                        )
                        nested_data[p][b][l][s].append(
                            {
                                "x0": int(char["bbox"][0] / page_width * 1000),
                                "y0": int(char["bbox"][1] / page_height * 1000),
                                "x1": int(char["bbox"][2] / page_width * 1000),
                                "y1": int(char["bbox"][3] / page_height * 1000),
                                "c": char["c"],
                            }
                        )
        data.append((page_image, page_data))
    return data, nested_data


def prepare_input(data):
    for page_idx, (page_image, page_data) in enumerate(data):
        page_text = "".join([c["c"] for c in page_data])
        inputs = tokenizer(
            page_text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=384,
            stride=128,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
        )
        inputs["image"] = feature_extractor(images=page_image, return_tensors="pt")[
            "pixel_values"
        ]
        offset_mapping = inputs.pop("offset_mapping")
        inputs["bbox"] = torch.zeros(
            (inputs["input_ids"].shape[0], inputs["input_ids"].shape[1], 4),
            dtype=torch.long,
        )
        for i, sequence in enumerate(inputs["input_ids"]):
            for j, token in enumerate(sequence):
                start, end = offset_mapping[i][j]
                if start >= end:
                    continue
                inputs["bbox"][i, j][0] = min(
                    page_data[k]["x0"] for k in range(start, end)
                )
                inputs["bbox"][i, j][1] = min(
                    page_data[k]["y0"] for k in range(start, end)
                )
                inputs["bbox"][i, j][2] = max(
                    page_data[k]["x1"] for k in range(start, end)
                )
                inputs["bbox"][i, j][3] = max(
                    page_data[k]["y1"] for k in range(start, end)
                )

        yield (
            page_idx,
            {
                "bbox": inputs["bbox"],
                "image": inputs["image"],
                "attention_mask": inputs["attention_mask"],
                "input_ids": inputs["input_ids"],
                "offset_mapping": offset_mapping,
            },
        )


def extract_layout(
    path: str,
    level: str = "line",
    exclude: list[str] | None = None,
    stop_at_section: str | None = None,
    merge_consecutive_section: bool = False,
    remove_citations: bool = False,
):
    if exclude is None:
        exclude = []

    assert level in ["line", "block"], "level must be either 'line' or 'block'"

    data, nested_data = extract_data(path)

    output = []
    stopped = False

    with alive_bar(len(data)) as bar:
        for page_idx, encoding in prepare_input(data):
            bar()
            outputs = model(
                input_ids=encoding["input_ids"],
                bbox=encoding["bbox"],
                attention_mask=encoding["attention_mask"],
                image=encoding["image"],
            )
            labels = torch.argmax(outputs.logits, dim=2)

            lookup = defaultdict(
                lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
            )

            curr_page_data = data[page_idx][1]

            for i, sequence in enumerate(labels):
                for j, label in enumerate(sequence):
                    start, end = encoding["offset_mapping"][i][j]
                    label = id2label[label.item()]
                    assert start >= 0 and end <= len(curr_page_data)
                    for offset in range(start, end):
                        lookup[curr_page_data[offset]["page"]][
                            curr_page_data[offset]["block"]
                        ][curr_page_data[offset]["line"]][curr_page_data[offset]["span"]][
                            label
                        ] += 1

            for page in sorted(lookup.keys()):
                for block in sorted(lookup[page].keys()):
                    block_counter = Counter()
                    block_text = []
                    line_sep = " "

                    for line in sorted(lookup[page][block].keys()):
                        line_counter = Counter()
                        line_text = []
                        span_sep = ""

                        for span in sorted(lookup[page][block][line].keys()):
                            line_text.append(
                                "".join(
                                    [c["c"] for c in nested_data[page][block][line][span]]
                                )
                            )
                            line_counter.update(lookup[page][block][line][span])

                        block_text.append(span_sep.join(line_text))
                        block_counter.update(line_counter)
                        if (
                            level == "line"
                            and (label := line_counter.most_common(1)[0][0]) not in exclude
                        ):
                            output.append(
                                {
                                    "label": label,
                                    "text": span_sep.join(line_text),
                                }
                            )

                    if (
                        level == "block"
                        and (label := block_counter.most_common(1)[0][0]) not in exclude
                    ):
                        if (
                            label == "Section-header"
                            and line_sep.join(block_text).strip() == stop_at_section
                        ):
                            stopped = True
                            break

                        output.append(
                            {
                                "label": label,
                                "text": line_sep.join(block_text),
                            }
                        )
                if stopped:
                    break

            if stopped:
                break

    # filter out text in between title and abstract
    new_output = []
    start = False
    for i, part in enumerate(output):
        if part["label"] == "Section-header" and part["text"].lower().startswith(
            "abstract"
        ):
            new_output.extend(output[i:])
            break
        if part["label"] == "Title":
            start = True
            new_output.append(part)
            continue
        if start and part["label"] != "Title":
            continue

    output = new_output

    if merge_consecutive_section:
        merged_output = []
        prev_part = None
        for part in output:
            if (
                prev_part is not None
                and prev_part["label"] == part["label"]
                and not prev_part["text"].endswith(".")
            ):
                prev_part["text"] += " " + part["text"]
            else:
                if prev_part is not None:
                    merged_output.append(prev_part)
                prev_part = part
        output = merged_output

    if remove_citations:
        output = [
            {
                "label": part["label"],
                "text": inline_ciations.sub("", citations.sub("", part["text"])),
            }
            for part in output
        ]

    return output
