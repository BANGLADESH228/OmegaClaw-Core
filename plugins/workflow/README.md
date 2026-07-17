# Workflow loading plugin

Workflow loading plugin allows loading agent skills written according to the
[common specification](https://agentskills.io/specification). Each workflow
consists of short description, detailed description in `SKILL.md` file and
optionally `skill.metta` file which contains related skills implementation in
MeTTa language.

[Research workflow](./instructions/research-workflow) is a ready-to-use example
of the workflow. One can try it starting the agent and asking it doing a
research on some topic:
```
Start research. Build a classifier for iris dataset using sklearn, compare
logistic regression and random forest.
```

## Workflow files

`description.txt` (required) contains short usually one-line workflow
description for the agent. For example:
```
When user asks to demonstrate workflow plugin load test-workflow instructions: (workflow-load-instructions \"test-workflow\")
```

`SKILL.md` (required) is an agent skills file in the [common
format](https://agentskills.io/specification). For example:
```
---
name: test-workflow
description: Created to check how SKILL.md is loaded to OmegaClaw.
---
Next are instructions and MeTTa  functions  that should be performed step by step
# Test Workflow (OmegaClaw)
## Step 1 - demonstrate usage of skills
- Call test-skill with "This is a test workflow demonstration" message
## Step 2 - complete workflow
- Call `(workflow-unload-instructions)`
```

`skill.metta` (optional) contains the list of the OmegaClaw skills to load
when workflow is active and additional MeTTa functions which are mentioned in
`SKILL.md` file.

Skill description are added as high-level expressions. Each such expression
adds one skill to the OmegaClaw. First atom of the expression is `skill` symbol
and other atoms are parameters of the `add-skill` function. See
[pluginapi.metta](/src/pluginapi.metta) for details. Skill implementations are
added as MeTTa functions.

For example:
```
(skill test-skill "Test skill to demonstrate workflow by sending message to the user" (message_in_quotes))

(= (test-skill $message)
   (send $message))
```

## Using workflow

Start an agent and ask it to use the workflow. For the test workflow above
send: `Demonstrate workflow plugin`

