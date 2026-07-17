# Standardized Bug Data Input Schema

This document describes the structure and data types for the standardized JSON format used as input for the `TaskGraphGenerator`.

## Root Object

| Field          | Type         | Description                                                                 |
| -------------- | ------------ | --------------------------------------------------------------------------- |
| `bug_metadata` | Object       | Contains high-level information about the bug report.                       |
| `bug_content`  | Object       | Contains the descriptive content of the bug.                                |
| `attachments`  | Array[Object] | List of attachments associated with the bug report.                         |
| `comments`     | Array[Object] | List of comments or discussion entries related to the bug.                  |
| `history`      | Array[Object] | List of changes or events in the bug report's lifecycle (optional).         |

---

## `bug_metadata` Object

| Field         | Type   | Description                                                        |
| ------------- | ------ | ------------------------------------------------------------------ |
| `bug_id`      | String | Unique identifier for the bug.                                     |
| `bug_title`   | String | Title or summary of the bug.                                       |
| `test_environment_url` | String | URL or descriptive name of an authorized test environment (e.g., "http://localhost:3000", "ExampleApp v19"). |
| `severity`    | Object | Object containing severity information.                            |
| `status`      | Object | Object containing status information.                              |
| `customer`    | Object | Object containing customer information.                            |
| `product`     | Object | Object containing product information.                             |
| `component`   | Object | Object describing the affected component/area (optional).          |
| `dates`       | Object | Object containing relevant dates.                                  |
| `reporter`    | String | Identifier for the person/system reporting the bug (optional).     |
| `assignee`    | String | Identifier for the person/system assigned to the bug (optional).   |

### `bug_metadata.severity` Object

| Field         | Type    | Description                                |
| ------------- | ------- | ------------------------------------------ |
| `level`       | Integer | Numerical severity level (e.g., 1-5).      |
| `description` | String  | Textual description of severity (e.g., "High"). |

### `bug_metadata.status` Object

| Field         | Type   | Description                                  |
| ------------- | ------ | -------------------------------------------- |
| `code`        | String | Status code (e.g., "51", "NEW").             |
| `description` | String | Textual description of status (e.g., "Closed"). |

### `bug_metadata.customer` Object

| Field         | Type   | Description                         |
| ------------- | ------ | ----------------------------------- |
| `name`        | String | Customer name or identifier.        |
| `environment` | String | Environment type (e.g., "Web", "On premises"). |

### `bug_metadata.product` Object

| Field     | Type   | Description                         |
| --------- | ------ | ----------------------------------- |
| `id`      | String | Product identifier (optional).      |
| `name`    | String | Product name.                       |
| `version` | Object | Object containing version details. |

### `bug_metadata.product.version` Object

| Field           | Type   | Description                                     |
| --------------- | ------ | ----------------------------------------------- |
| `reported`      | String | Version in which the bug was reported.          |
| `component_ver` | String | Specific component version affected (optional). |
| `fixed_ver`     | String | Version in which the bug is fixed (optional).   |

### `bug_metadata.component` Object

| Field         | Type   | Description                          |
| ------------- | ------ | ------------------------------------ |
| `name`        | String | Name of the component/module.        |
| `type`        | String | Type of component (e.g., "Platform"). |
| `subcomponent`| String | Sub-component name (optional).       |

### `bug_metadata.dates` Object

| Field     | Type   | Description                          |
| --------- | ------ | ------------------------------------ |
| `created` | String | ISO 8601 timestamp of creation.      |
| `updated` | String | ISO 8601 timestamp of last update.   |
| `fix_eta` | String | Estimated fix date (optional).       |

---

## `bug_content` Object

| Field                | Type   | Description                                                                                      |
| -------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| `description`        | String | Detailed description of the bug/issue.                                                           |
| `steps_to_reproduce` | String | Steps to reproduce the bug. Can be detailed or indicate inference is needed.                     |
| `expected_outcome`   | String | What the expected behavior should be.                                                            |
| `additional_info`    | String | Any other relevant information.                                                                  |
| `reproducible`       | Object | Object containing information about reproducibility (optional).                                  |

### `bug_content.reproducible` Object

| Field         | Type    | Description                                      |
| ------------- | ------- | ------------------------------------------------ |
| `by_customer` | Boolean | Whether the customer could reproduce the issue.  |
| `by_support`  | Boolean | Whether support could reproduce the issue.       |
| `environment` | String  | Environment where reproducibility was tested.  |

---

## `attachments` Array Items (Object)

| Field           | Type         | Description                                                     |
| --------------- | ------------ | --------------------------------------------------------------- |
| `id`
