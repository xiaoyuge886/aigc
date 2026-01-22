---
source_url: https://platform.claude.com/docs/en/api/typescript/beta/files/download
source_type: sitemap
content_hash: sha256:81a345d1c94fdbe944fbadee0b1f56af7387e5d3b5257390c01f0836ac9b76f4
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Download

`client.beta.files.download(stringfileID, FileDownloadParamsparams?, RequestOptionsoptions?): Response`

**get** `/v1/files/{file_id}/content`

Download File

### Parameters

- `fileID: string`

  ID of the File.

- `params: FileDownloadParams`

  - `betas?: Array<AnthropicBeta>`

    Optional header to specify the beta version(s) you want to use.

    - `(string & {})`

    - `"message-batches-2024-09-24" | "prompt-caching-2024-07-31" | "computer-use-2024-10-22" | 16 more`

      - `"message-batches-2024-09-24"`

      - `"prompt-caching-2024-07-31"`

      - `"computer-use-2024-10-22"`

      - `"computer-use-2025-01-24"`

      - `"pdfs-2024-09-25"`

      - `"token-counting-2024-11-01"`

      - `"token-efficient-tools-2025-02-19"`

      - `"output-128k-2025-02-19"`

      - `"files-api-2025-04-14"`

      - `"mcp-client-2025-04-04"`

      - `"mcp-client-2025-11-20"`

      - `"dev-full-thinking-2025-05-14"`

      - `"interleaved-thinking-2025-05-14"`

      - `"code-execution-2025-05-22"`

      - `"extended-cache-ttl-2025-04-11"`

      - `"context-1m-2025-08-07"`

      - `"context-management-2025-06-27"`

      - `"model-context-window-exceeded-2025-08-26"`

      - `"skills-2025-10-02"`

### Returns

- `unnamed_schema_0 = Response`

### Example

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env['ANTHROPIC_API_KEY'], // This is the default and can be omitted
});

const response = await client.beta.files.download('file_id');

console.log(response);

const content = await response.blob();
console.log(content);
```
