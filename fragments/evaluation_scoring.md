Scoring:
- 1 = More than one non-trivial counterexample was found, or one especially major counterexample was found that has a large impact on overall quality for that criterion.
- 2 = Exactly one non-trivial counterexample was found, and it is meaningful enough to lower the rating.
- 3 = No non-trivial counterexamples were found.

Scoring discipline:
- Do not award a 3 if you identified any non-trivial counterexample for that criterion.
- Do not award a 1 unless you identified either (a) two or more non-trivial counterexamples for that criterion, or (b) one counterexample with outsized impact on that criterion.
- A major failure on one criterion does not by itself lower adjacent criteria unless the same flaw independently violates them.

<Output Format>
Output exactly one JSON object with this shape:
{
  "counter_examples": [
    {
      "dimension": "<dimension_name>",
      "criteria": [
        {
          "id": "<criterion_id>",
          "text": "<criterion_text>",
          "counter_examples": [
            "No non-trivial counterexamples found."
          ]
        }
      ]
    }
  ],
  "scores": {
    "<criterion_id>": 1
  }
}

Output requirements:
- Output valid JSON only. Do not output markdown, XML, prose, commentary, or code fences.
- The top-level object must contain exactly two keys, in this order:
  1. "counter_examples"
  2. "scores"
- "counter_examples" must be an array containing every dimension exactly once, in the order given in RUBRIC_JSON.
- Each dimension object must contain exactly two keys, in this order:
  1. "dimension"
  2. "criteria"
- "criteria" must be an array containing every criterion for that dimension exactly once, in the order given in RUBRIC_JSON.
- Each criterion object must contain exactly three keys, in this order:
  1. "id"
  2. "text"
  3. "counter_examples"
- The value of "id" must be the exact criterion ID from RUBRIC_JSON.
- The value of "text" must be the exact criterion text from RUBRIC_JSON.
- The value of "counter_examples" must be either:
  - an array with exactly one string: "No non-trivial counterexamples found."
  - or an array of one or more strings, each beginning with "Counterexample 1:", "Counterexample 2:", and so on
- Each counterexample string must:
  - identify the specific location in the cleaned transcript (entry, sentence, section, schema element, or omission)
  - quote or paraphrase the offending text when applicable
  - explain in one sentence why it violates the criterion
- For omission counterexamples, explicitly name the missing fact and the section where it most naturally should have appeared.
- "scores" must be a flat JSON object using every criterion ID exactly once as a key, in the order given in RUBRIC_JSON.
- Each score value must be an integer: 1, 2, or 3.
- Do not add extra keys anywhere.
- Do not use null values.
- Do not use comments.

<RUBRIC_JSON>
