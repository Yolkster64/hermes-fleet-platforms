# LLM Usage Guide

This guide explains how to use Large Language Models (LLMs) within the project.

## Integration
- LLMs are accessed via API endpoints defined in the `/api/llm/` directory.
- Supported providers: OpenAI, Azure, and local models (e.g., llama.cpp).
- Configure provider credentials in the `.env` file.

## Usage
- Use the provided SDK or HTTP endpoints to send prompts and receive completions.
- Handle rate limits and errors gracefully in your application code.

## Best Practices
- Always sanitize user input before sending to the LLM.
- Log usage for monitoring and debugging.
- Respect provider terms of service and usage limits.

## Example
```js
const response = await fetch('/api/llm/completion', { method: 'POST', body: JSON.stringify({ prompt: 'Hello, world!' }) });
const data = await response.json();
console.log(data.result);
```
