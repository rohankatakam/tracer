Given the following GitHub issue data, please generate a Bug Reproduction Graph and a Reproduction Summary.

Focus on creating a graph that is **concise, intuitive, and directly helpful for a developer** trying to reproduce this bug. Prioritize clarity and the critical path to reproduction. Pay close attention to the schema and the detailed instructions provided in the system message, especially regarding summarization of errors/logs and the `developer_takeaway`.

GitHub Issue JSON:
```json
{{GITHUB_ISSUE_JSON}}
```

Your output must be a single JSON object structured as follows:
```json
{
  "bug_reproduction_graph": {
    // nodes and edges here
  },
  "reproduction_summary": {
    // summary details here, including 'developer_takeaway'
  }
}
```
