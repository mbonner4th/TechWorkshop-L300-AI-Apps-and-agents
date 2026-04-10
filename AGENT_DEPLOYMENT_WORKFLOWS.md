# Foundry Agent Deployment Workflows

This document describes the automated GitHub Actions workflows for deploying Microsoft Foundry agents.

## Overview

Six GitHub Actions workflows have been created to automate the deployment of Zava shopping assistant agents to Microsoft Foundry. Each workflow is triggered by changes to agent definition JSON files and their corresponding prompt files.

## Workflows

| Workflow | Agent JSON | Prompt File |
|----------|-----------|-------------|
| `customer-loyalty-agent-update.yml` | `src/infra/agents/customer-loyalty.json` | `src/prompts/CustomerLoyaltyAgentPrompt.txt` |
| `cart-manager-agent-update.yml` | `src/infra/agents/cart-manager.json` | `src/prompts/CartManagerPrompt.txt` |
| `cora-agent-update.yml` | `src/infra/agents/cora.json` | `src/prompts/ShopperAgentPrompt.txt` |
| `handoff-service-agent-update.yml` | `src/infra/agents/handoff-service.json` | `src/prompts/HandoffAgentPrompt.txt` |
| `interior-designer-agent-update.yml` | `src/infra/agents/interior-designer.json` | `src/prompts/InteriorDesignAgentPrompt.txt` |
| `inventory-agent-update.yml` | `src/infra/agents/inventory-agent.json` | `src/prompts/InventoryAgentPrompt.txt` |

## Workflow Triggers

Each workflow is configured to trigger on:

1. **Push to main branch** when either:
   - The agent definition JSON file changes
   - The corresponding prompt file changes
2. **Manual trigger** via `workflow_dispatch` from the Actions tab

## Workflow Steps

### 1. Checkout Code
Uses `actions/checkout@v4` to fetch the repository.

### 2. Azure Authentication
Authenticates to Azure using `azure/login@v2.1.1` with the `AZURE_CREDENTIALS` secret containing the service principal credentials.

### 3. Prepare Agent Definition
Uses `jq` to:
- Load the agent definition JSON template
- Substitute `${GPT_DEPLOYMENT}` with the value from `GPT_DEPLOYMENT` secret (default: `gpt-5.4-mini`)
- Read the prompt file using `--rawfile` flag to properly handle multiline text
- Replace `${INSTRUCTIONS}` placeholder with the prompt content
- Output compact JSON for the REST API call

Example jq command:
```bash
jq \
  --arg gpt_deployment "gpt-5.4-mini" \
  --rawfile instructions src/prompts/CustomerLoyaltyAgentPrompt.txt \
  '.definition.model = $gpt_deployment | .definition.instructions = $instructions' \
  src/infra/agents/customer-loyalty.json
```

### 4. Deploy Agent Version to Foundry
Uses Azure CLI `az rest` to POST the prepared agent definition to the Foundry REST API:

```bash
az rest \
  --method POST \
  --url "${FOUNDRY_ENDPOINT}/agents/{agent-name}/versions?api-version=2025-11-15-preview" \
  --resource "https://ai.azure.com" \
  --headers "Content-Type=application/json" \
  --body '<prepared-definition>'
```

## Required GitHub Secrets

The workflows require the following secrets to be set in your GitHub repository:

| Secret | Description | Example |
|--------|-------------|---------|
| `AZURE_CREDENTIALS` | Service principal credentials (JSON from `az ad sp create-for-rbac`) | `{"clientId":"...", "clientSecret":"...", ...}` |
| `FOUNDRY_ENDPOINT` | Microsoft Foundry project endpoint | `https://aif-xxx.services.ai.azure.com/api/projects/proj-xxx` |
| `GPT_DEPLOYMENT` | GPT model deployment name | `gpt-5.4-mini` |

Verify secrets are set:
```bash
gh secret list -R <owner>/<repo> | grep -E 'AZURE_CREDENTIALS|FOUNDRY_ENDPOINT|GPT_DEPLOYMENT'
```

## How to Use

### Automatic Deployment
1. Edit the agent JSON file or corresponding prompt file
2. Commit and push to the main branch
3. The workflow will automatically trigger and deploy the agent version to Foundry

### Manual Deployment
1. Go to the GitHub Actions tab
2. Select the desired workflow (e.g., "Update Customer Loyalty Agent")
3. Click "Run workflow" and select "Run workflow"

### Check Deployment Status
1. Navigate to the Actions tab in the repository
2. Select the workflow run
3. Review the logs to confirm successful deployment

## Agent Definition Template Format

Each agent JSON file has this structure:

```json
{
  "description": "Agent description",
  "definition": {
    "kind": "prompt",
    "model": "${GPT_DEPLOYMENT}",
    "instructions": "${INSTRUCTIONS}",
    "tools": [
      {
        "type": "function",
        "name": "tool_name",
        "description": "Tool description",
        "parameters": { ... }
      }
    ]
  }
}
```

The workflow replaces:
- `${GPT_DEPLOYMENT}` with the actual deployment name
- `${INSTRUCTIONS}` with the contents of the corresponding prompt file

## Troubleshooting

### Workflow Fails with "Resource not accessible"
- Verify `AZURE_CREDENTIALS` secret is properly set
- Ensure the service principal has Contributor role on the resource group

### Agent Definition Deployment Fails
- Verify `FOUNDRY_ENDPOINT` is correct in the secret
- Check that the API version `2025-11-15-preview` is supported
- Ensure the agent name in the URL matches the JSON filename (without .json)

### Prompt File Not Found
- Verify the prompt file path in the workflow matches `src/prompts/` location
- Ensure the prompt file exists and is readable

## Testing the Workflow Locally

To test the jq transformation locally before pushing:

```bash
jq \
  --arg gpt_deployment "gpt-5.4-mini" \
  --rawfile instructions src/prompts/CustomerLoyaltyAgentPrompt.txt \
  '.definition.model = $gpt_deployment | .definition.instructions = $instructions' \
  src/infra/agents/customer-loyalty.json | jq .
```

## API Reference

Foundry Agent Deployment API:
- **Endpoint**: `{FOUNDRY_ENDPOINT}/agents/{agent-name}/versions`
- **Method**: POST
- **API Version**: `2025-11-15-preview`
- **Resource Scope**: `https://ai.azure.com`
- **Content-Type**: `application/json`

Request body structure:
```json
{
  "description": "Agent description",
  "definition": {
    "kind": "prompt",
    "model": "gpt-5.4-mini",
    "instructions": "Full prompt text here",
    "tools": [...]
  }
}
```
