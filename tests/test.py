# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-preview-04-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Please generate a synthetic bug task graph data with the following schema- IMPORTANT GUIDELINES:
1. Create a structured task graph with sequential steps for reproducing the bug
2. Each step must be highly detailed and actionable for a computer agent to follow
3. Reference specific screenshots to provide visual context for each step (e.g., \"See page_2_img_1.jpeg for the location of the button\")
4. Include precise inputs, UI element interactions, and expected results for each step
5. Steps should be specific enough that a computer agent could automate the reproduction process

CONTEXT ABOUT THE DATA:
- Raw text is marked with page numbers (\"== PAGE 1 ==\") 
- Images are named with page and sequence numbers (e.g., \"page_2_img_1.jpeg\")
- OCR text from images is marked with \"--- OCR from [image filename] ---\"
- All screenshot filenames should be referenced exactly as they appear in the data

OUTPUT FORMAT - YOU MUST USE THIS EXACT STRUCTURE:
{
  \"name\": \"bug_[identifier]\",
  \"description\": \"[Concise description of the bug]\",
  \"environment\": {
    \"application\": \"[Application name and version]\",
    \"browser\": \"[Browser name and version if applicable]\",
    \"operating_system\": \"[OS name and version if applicable]\"
  },
  \"task_graph\": {
    \"nodes\": [
      {
        \"id\": \"1\",
        \"type\": \"action\",
        \"content\": \"[DETAILED step description, e.g., 'Click the Login button in the top-right corner of the screen']\",
        \"metadata\": {
          \"image_refs\": [\"page_2_img_1.jpeg\"],  // List of referenced screenshots for this step
          \"ui_elements\": [\"Login button\"],      // UI elements to interact with
          \"inputs\": [\"username=admin\"],        // Any input values to enter
          \"expected_result\": \"Login form appears\" // What should happen after this step
        }
      }
    ],
    \"edges\": [
      {
        \"source\": \"1\",
        \"target\": \"2\"
      }
    ]
  },
  \"verification_steps\": [
    \"Step 1: [How to verify the bug is present]\"
  ],
  \"confidence_score\": 0.85,  // Your confidence in these reproduction steps
  \"missing_information\": [\"Any critical information missing from the report\"] 
}"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""The user wants a synthetic bug task graph in JSON format based on provided (simulated) raw text and OCR data.

Here's a plan:
1.  Define the structure of the JSON output as specified.
2.  Invent a plausible bug based on the *idea* of raw text/OCR data. Since no actual text/OCR data is provided, I will create a simple scenario, e.g., a UI element disappears or misbehaves after a sequence of actions.
3.  Invent page numbers, image filenames, and OCR content to simulate the raw data needed to build the task graph.
4.  Create a `name`, `description`, and `environment` for the synthetic bug.
5.  Construct the `task_graph`:
    *   Identify a sequence of actions that *could* lead to a bug. A simple sequence could be: Log in -> Navigate to a specific page -> Interact with an element -> Observe the bug.
    *   For each action step:
        *   Assign a unique `id`.
        *   Set `type` to \"action\".
        *   Write a detailed `content` description, referencing the simulated image filenames.
        *   Populate `metadata` with `image_refs`, `ui_elements`, `inputs` (if any), and `expected_result`.
    *   Create `edges` to connect the nodes sequentially.
6.  Define `verification_steps` explaining how to confirm the bug exists after following the task graph.
7.  Assign a plausible `confidence_score`.
8.  Identify any `missing_information` that would typically be in a real bug report but isn't simulated here (like actual logs, user details, etc., though the prompt doesn't require these).

Let's simulate some data:

**Simulated Raw Text:**
== PAGE 1 ==
I found a problem when trying to save a report. After clicking the 'Save' button, the success message didn't appear, and the 'Edit' button vanished.

== PAGE 2 ==
Screenshot showing the report edit page before clicking save.
(page_2_img_1.jpeg)
--- OCR from page_2_img_1.jpeg ---
Report Title: Daily Sales
Generated On: 2023-10-27
[Edit Button] [Save Button]

== PAGE 3 ==
Screenshot showing the page after clicking save.
(page_3_img_1.jpeg)
--- OCR from page_3_img_1.jpeg ---
Report Title: Daily Sales
Generated On: 2023-10-27
[Save Button] (Note: Edit button is missing)

Okay, based on this simulated data, the bug is that the \"Edit\" button disappears after saving a report, and no success message appears.

Now, let's build the JSON structure based on this simulated scenario.

**Bug Details:**
*   `name`: bug_report_save_ui
*   `description`: After saving a report, the \"Edit\" button disappears, and no success confirmation message is displayed.
*   `environment`: Let's assume a web application.
    *   `application`: \"Report Management System v1.5\"
    *   `browser`: \"Chrome 118.0\"
    *   `operating_system`: \"Windows 10\"

**Task Graph Steps:**
1.  Access the Report Edit page.
    *   `content`: \"Navigate to the specific report edit page URL: [URL]\"
    *   `metadata`: `image_refs`: [], `ui_elements`: [], `inputs`: [], `expected_result`: \"The report edit page is displayed with the 'Edit' and 'Save' buttons visible.\"
2.  Click the Save Button.
    *   `content`: \"Click the 'Save Button' located below the report details.\"
    *   `metadata`: `image_refs`: [\"page_2_img_1.jpeg\"], `ui_elements`: [\"Save Button\"], `inputs`: [], `expected_result`: \"The report should be saved, a success message should appear, and the 'Edit' button should remain visible.\"
3.  Observe the UI.
    *   `content`: \"Observe the state of the page after clicking 'Save'.\"
    *   `metadata`: `image_refs`: [\"page_3_img_1.jpeg\"], `ui_elements`: [\"Edit Button\"], `inputs`: [], `expected_result`: \"The 'Edit Button' is missing, and no success message is displayed.\"

**Edges:**
1 -> 2
2 -> 3

**Verification Steps:**
1.  Load the report edit page.
2.  Click the 'Save' button.
3.  Observe if the 'Edit' button disappears from the page.
4.  Observe if a success message is displayed.

**Confidence Score:** Let's say 0.90, assuming the steps are clear from the screenshots.

**Missing Information:** \"Actual user identifier\", \"Report ID used for testing\", \"Server logs from the time of saving\".

Okay, planning complete. I will now generate the JSON based on this plan."""),
                types.Part.from_text(text="""{
  \"name\": \"bug_report_save_ui\",
  \"description\": \"After saving a report, the 'Edit' button disappears, and no success confirmation message is displayed.\",
  \"environment\": {
    \"application\": \"Report Management System v1.5\",
    \"browser\": \"Chrome 118.0\",
    \"operating_system\": \"Windows 10\"
  },
  \"task_graph\": {
    \"nodes\": [
      {
        \"id\": \"1\",
        \"type\": \"action\",
        \"content\": \"Navigate to the Report Edit page for a specific report. Use the URL 'https://reports.example.com/edit/report_id_123'.\",
        \"metadata\": {
          \"image_refs\": [],
          \"ui_elements\": [],
          \"inputs\": [],
          \"expected_result\": \"The report edit page is displayed, showing the report details and action buttons like 'Edit' and 'Save'.\"
        }
      },
      {
        \"id\": \"2\",
        \"type\": \"action\",
        \"content\": \"Locate and click the 'Save Button' on the report edit page. See page_2_img_1.jpeg for the general layout and button position.\",
        \"metadata\": {
          \"image_refs\": [\"page_2_img_1.jpeg\"],
          \"ui_elements\": [\"Save Button\"],
          \"inputs\": [],
          \"expected_result\": \"The report data is saved successfully, a success message appears (e.g., 'Report saved'), and the 'Edit Button' remains visible.\"
        }
      },
      {
        \"id\": \"3\",
        \"type\": \"action\",
        \"content\": \"Observe the page state after clicking the 'Save Button'. Check for the presence of a success message and the 'Edit Button'. Refer to page_3_img_1.jpeg which shows the state observed after the bug occurs.\",
        \"metadata\": {
          \"image_refs\": [\"page_3_img_1.jpeg\"],
          \"ui_elements\": [\"Edit Button\", \"Success Message Area\"],
          \"inputs\": [],
          \"expected_result\": \"The 'Edit Button' is missing from the page, and no success message is displayed.\"
        }
      }
    ],
    \"edges\": [
      {
        \"source\": \"1\",
        \"target\": \"2\"
      },
      {
        \"source\": \"2\",
        \"target\": \"3\"
      }
    ]
  },
  \"verification_steps\": [
    \"1. Navigate to the report edit page.\",
    \"2. Click the 'Save' button.\",
    \"3. Check if the 'Edit' button is still visible on the page.\",
    \"4. Check if a success message confirming the save operation is displayed.\"
  ],
  \"confidence_score\": 0.90,
  \"missing_information\": [
    \"Actual content of the report being edited\",
    \"Server response details after clicking 'Save'\",
    \"Console logs from the browser\"
  ]
}"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
