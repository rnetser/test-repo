# Custom workflows

## Supported workflows  
- Add PR size label
- Add to or removed from label from PR; supported labels: `wip`, `lgtm`, `verified`  

## How to add a new workflow
1. Create a new file in `.github/workflows` directory.
2. Add relevant steps to the workflow.
3. Code should be implemented in python and placed in `.github/scripts` directory.
4. Make sure that the workflow is triggered only on relevant events.
5. Set `ACTION` environment variable in the workflow and use it in the code to identify the relevant workflow.
