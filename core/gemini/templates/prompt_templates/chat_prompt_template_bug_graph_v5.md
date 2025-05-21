Given the following bug details, please generate a Bug Reproduction Graph and a Reproduction Summary.

Adhere strictly to the **V5 System Instructions** (which includes the detailed JSON schema) and ensure your output conforms to the **Bug Reproduction Graph Schema V5** structure detailed therein.

Key requirements for V5:
-   Each node in the graph MUST have `id` and `position: { "x": number, "y": number }` fields for React Flow compatibility.
-   Edges MUST have `id`, `source`, `target`, and a **REQUIRED `label`** field, referencing valid node IDs.
-   Optionally, edges can include `edge_render_type` (e.g., "default", "straight", "step", "smoothstep") for visual styling, and `source_handle_id` / `target_handle_id` for specific connection points on nodes if custom handles are implied by the graph logic.
-   Use the specified `role` (for nodes) and `relationship_type` (for edges) enums from the V5 schema.
-   Provide a concise and actionable `developer_actionable_takeaway` in the summary.
-   Ensure the overall graph is intuitive and visually plannable for a developer.
-   Utilize the optional `backgroundColor` and `borderColor` fields for nodes to enhance visual differentiation based on their role, aiming for a clear and aesthetically pleasing graph (refer to V5 System Instructions for color suggestions).

Bug Details Text:
```
{{BUG_DETAILS_TEXT}}
```

Your output must be a single JSON object structured as follows, conforming to the Bug Reproduction Graph Schema V5 detailed in the V5 System Instructions:
```json
{
  "bug_reproduction_graph": {
    "nodes": [
      {
        "id": "node-example-1",
        "role": "UserAction",
        "label": "Click 'Submit'",
        "description": "User clicks the main submission button on the form.",
        "position": { "x": 100, "y": 100 },
        "details": { "form_id": "payment-form" },
        "backgroundColor": "#D4EFDF",
        "borderColor": "#7DCEA0"
      }
    ],
    "edges": [
      {
        "id": "edge-example-1-2",
        "source": "node-example-1",
        "target": "node-example-2",
        "relationship_type": "Triggers",
        "label": "Form Submission", // This label is REQUIRED
        "edge_render_type": "smoothstep", // Optional: Example for visual style
        "source_handle_id": "src-handle-id-optional", // Optional: Example
        "target_handle_id": "tgt-handle-id-optional"  // Optional: Example
      }
    ]
  },
  "reproduction_summary": {
    "overall_bug_title": "Descriptive Bug Title",
    "associated_issue_id": "PROJECT-123",
    "developer_actionable_takeaway": "Focus on the interaction between ModuleA and ModuleB during data processing.",
    "estimated_reproduction_complexity": "Medium",
    "critical_environment_factors": ["Browser: Chrome vLatest", "OS: Windows 11"],
    "key_steps_count": 5
  }
}
```
