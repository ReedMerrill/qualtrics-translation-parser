import pandas as pd
import numpy as np
import subprocess
import json

# load and clean translation file
df = pd.read_csv("cmb-2025-trans-fr.csv")

df = df[["PhraseID", "FR"]]

df = df[df["PhraseID"].str.match("^QID.*$")]

# load survey spec
with open("survey-spec.json", "r") as f:
    spec = json.load(f)


def questions_dict(survey_spec):
    survey_elements = survey_spec["SurveyElements"]
    # tags dictionary has IDs as keys and export tags (variable names) as values
    tags = {}
    for element in survey_elements:
        if isinstance(element, dict) and isinstance(element["Payload"], dict):
            if "DataExportTag" in element["Payload"].keys():
                tags.update(
                    {element["PrimaryAttribute"]: element["Payload"]["DataExportTag"]}
                )
    return tags


tags = questions_dict(spec)

df[["Attr", "text_type"]] = df["PhraseID"].str.split("_", expand=True)
df["Values"] = df.groupby("Attr").cumcount()
condition = (
    (df["FR"] == "Ne sais pas / Pas d'opinion")
    | (df["FR"] == "Ne sais pas / Sans opinion")
    | (df["FR"] == "Ne sais pas")
    | (df["FR"] == "Pas d'opinion")
    | (df["FR"] == "Préfère ne pas répondre")
)
df["Values"] = np.where(
    condition,
    -99,
    df["Values"],
)

# Process HTML to align with pandoc
# linebreaks
df["FR"] = df["FR"].str.replace(r"<br />➘", "\n", regex=True)
# spans
df["FR"] = df["FR"].str.replace(r"(<span\b[^>]*>)|(<\/span>)", "", regex=True)
# style
df["FR"] = df["FR"].str.replace(r"<style\b[^>]*>.*?<\/style>", "", regex=True)
# table
df["FR"] = df["FR"].str.replace(r"<table\b[^>]*>.*?<\/table>", "", regex=True)

lines_out = []

for row in df.itertuples(index=True):
    if row.text_type == "QuestionText":
        tag = tags[row.Attr]
        lines_out.append(f"**{tag}** {row.FR}\n\n")
    else:
        lines_out.append(f"- {row.FR} ({row.Values})\n\n")
    prev_row = row

out_name = "out.md"

with open(out_name, "w", encoding="UTF-8") as file:
    for line in lines_out:
        file.write(line)

cmd = "pandoc " + out_name + " -o out.docx"

subprocess.run(cmd, shell=True)

# TEST:
df.to_csv("data.csv", index=False)
