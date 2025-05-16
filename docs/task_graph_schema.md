# Task Graph Schema Documentation

This document outlines the standard schema for task graphs used in the Computer Use Agent. Task graphs define sequences of actions and verifications for browser automation, computer use tasks, and security testing workflows.

## Schema Overview

A task graph is represented as a JSON object with the following top-level structure:

```json
{
  "name": "task_name",
  "description": "Description of the overall task",
  "environment": {
    "application": "Application name (e.g., Google Chrome, ExampleApp)",
    "browser": "Browser used (e.g., Google Chrome)",
    "operating_system": "OS requirements"
  },
  "task_graph": {
    "nodes": [...],
    "edges": [...]
  },
  "verification_steps": [...],
  "confidence_score": 0.95,
  "missing_information": [...],
  "source": {
    "model": "model_name",
    "raw_data_package": "source_info"
  }
}
```

## Nodes

Nodes represent individual steps in the task graph. Each node has the following structure:

```json
{
  "id": "unique_identifier",
  "type": "action|verification",
  "content": "Description of the action or verification to perform",
  "metadata": {
    "image_refs": ["page_1_img_1.png", "page_2_img_1.jpeg"],
    "ui_elements": ["UI element 1", "UI element 2"],
    "inputs": [
      "input1=value1", 
      "input2=value2",
      "Complex JSON payload modification examples",
      "\"field\": \"value\""
    ],
    "expected_result": "Description of expected outcome"
  }
}
```

### Node Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | String | Unique identifier for the node |
| `type` | String | Type of node: "action" or "verification" |
| `content` | String | Description of the action to perform or verification to check |
| `metadata` | Object | Additional metadata for the node |

### Metadata Properties

| Property | Type | Description |
|----------|------|-------------|
| `image_refs` | Array | References to images that illustrate the step |
| `ui_elements` | Array | UI elements involved in this step |
| `inputs` | Array | Input values required for this step |
| `expected_result` | String | Description of the expected outcome |

## Edges

Edges define the relationships between nodes, determining the execution order:

```json
{
  "source": "source_node_id",
  "target": "target_node_id"
}
```

## Verification Steps

A list of strings that provide high-level descriptions of verification points:

```json
[
  "Step 1: Verify that Chrome opens and navigates to Google.com",
  "Step 2: Verify that 'search term' is entered in the search box",
  "Step 3: After forwarding the modified request, observe the server's response",
  "Step 4: Confirm that the record's details displayed in the UI match the unauthorized values"
]
```

## Missing Information

An optional array of strings that describe information that would be helpful but is currently missing from the task graph:

```json
[
  "Specific user roles and permissions required for the 'authorized' part of the test",
  "Detailed navigation steps to reach the target form",
  "Exact name of the submit button on the form",
  "Specific details on configuring the proxy tool"
]
```

This field is particularly useful for security testing and complex workflows where additional context might be required.

## Examples

### Example 1: Simple Chrome Search Task

```json
{
  "name": "chrome_search",
  "description": "Search for a term on Google",
  "environment": {
    "application": "Google Chrome",
    "browser": "Google Chrome",
    "operating_system": "Any"
  },
  "task_graph": {
    "nodes": [
      {
        "id": "1",
        "type": "action",
        "content": "Open Google Chrome and navigate to Google.com",
        "metadata": {
          "ui_elements": ["Chrome browser icon", "Address bar"],
          "inputs": [],
          "expected_result": "Google homepage is visible"
        }
      },
      {
        "id": "2",
        "type": "action",
        "content": "Enter search term in the search box",
        "metadata": {
          "ui_elements": ["Google search box"],
          "inputs": ["search_term=example"],
          "expected_result": "Search term appears in the search box"
        }
      }
    ],
    "edges": [
      {
        "source": "1",
        "target": "2"
      }
    ]
  },
  "verification_steps": [
    "Step 1: Verify Chrome opens",
    "Step 2: Verify search term entry"
  ]
}
```

### Example 2: Security Vulnerability Testing

```json
{
  "name": "security_vulnerability_test",
  "description": "Security vulnerability allowing unauthorized data modification by intercepting and altering JSON requests",
  "environment": {
    "application": "Enterprise Application",
    "browser": "Any modern web browser",
    "operating_system": "Any OS capable of running a browser and proxy tools"
  },
  "task_graph": {
    "nodes": [
      {
        "id": "1",
        "type": "action",
        "content": "Log in to the application and navigate to the target form page",
        "metadata": {
          "image_refs": ["page_1_img_1.png"],
          "ui_elements": ["Navigation menus", "Form interface"],
          "inputs": [],
          "expected_result": "The form is displayed with editable fields"
        }
      },
      {
        "id": "2",
        "type": "action",
        "content": "Fill in the standard user-modifiable fields on the form",
        "metadata": {
          "image_refs": ["page_1_img_1.png"],
          "ui_elements": ["Year dropdown", "Month dropdown", "Status dropdown"],
          "inputs": [
            "year=2025",
            "month=May",
            "status=Draft"
          ],
          "expected_result": "The form fields are populated with the entered values"
        }
      },
      {
        "id": "3",
        "type": "action",
        "content": "Configure an interception proxy to capture outgoing requests and submit the form",
        "metadata": {
          "image_refs": ["page_1_img_1.png"],
          "ui_elements": ["Submit button"],
          "inputs": [],
          "expected_result": "The HTTP request is intercepted by the proxy tool"
        }
      },
      {
        "id": "4",
        "type": "action",
        "content": "Modify the JSON payload in the intercepted request to include unauthorized data changes",
        "metadata": {
          "image_refs": ["page_2_img_1.jpeg"],
          "ui_elements": ["Proxy tool's request editor"],
          "inputs": [
            "JSON payload modifications:",
            "\"status\": \"Approved\"",
            "\"uucur_price_current\": 10000.0",
            "\"ugenProjectNumber\": \"P-0001\""
          ],
          "expected_result": "The JSON payload is modified with unauthorized data"
        }
      },
      {
        "id": "5",
        "type": "verification",
        "content": "Verify that the application accepts the modified data and displays it in the UI",
        "metadata": {
          "image_refs": ["page_2_img_3.png"],
          "ui_elements": ["Record details view"],
          "inputs": [],
          "expected_result": "The application displays the unauthorized modified data, confirming the vulnerability"
        }
      }
    ],
    "edges": [
      {"source": "1", "target": "2"},
      {"source": "2", "target": "3"},
      {"source": "3", "target": "4"},
      {"source": "4", "target": "5"}
    ]
  },
  "verification_steps": [
    "Step 1: Verify the form loads correctly",
    "Step 2: Verify form fields can be modified",
    "Step 3: Verify HTTP request is intercepted",
    "Step 4: Verify JSON payload can be modified",
    "Step 5: Verify the application accepts and displays the unauthorized data"
  ],
  "missing_information": [
    "Specific user roles and permissions required for testing",
    "Detailed navigation steps to reach the form",
    "Exact field names in the JSON payload",
    "Specific configuration details for the proxy tool"
  ],
  "confidence_score": 0.9,
  "source": {
    "model": "vulnerability_assessment",
    "raw_data_package": "security_testing"
  }
}
```

## Using Task Graphs with Anthropic's Computer Use Agent

Task graphs serve as structured inputs to guide Anthropic's computer use agent through complex tasks. The agent interprets each node as a directive, with the metadata providing context for executing and verifying the action.

The directed graph structure (via edges) ensures that dependencies between tasks are respected during execution.
