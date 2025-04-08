import pandas as pd
import numpy as np
import subprocess
import json

# load and clean translation file
df = pd.read_csv("CMB 2025 - Genpop-EN-FR.csv")

# TODO: Refactor to remove lines not starting with QID[0-9]*
df = df.iloc[1:]  # Returns all rows starting from index 1
df = df.iloc[:-2]

df = df[["PhraseID", "FR"]]

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
    | ("Préfère ne pas répondre")
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

out_name = "out.md"

with open(out_name, "w", encoding="UTF-8") as file:
    for row in df.itertuples(index=True):
        if row.text_type == "QuestionText":
            tag = tags[row.Attr]
            file.write(f"### {row.PhraseID}\n\n**{tag}** {row.FR}\n\n")
        else:
            file.write(f"- {row.FR} ({row.Values})\n\n")

cmd = "pandoc " + out_name + " -o out.docx"

subprocess.run(cmd, shell=True)

df.to_csv("data.csv", index=False)
