---
source_url: https://platform.claude.com/docs/en/api/typescript/beta/files/retrieve_metadata
source_type: sitemap
content_hash: sha256:546d25e4e0867fdb964e8685d9f560b0c8c000750f40e403935a993d3c464bc2
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Retrieve Metadata

`client.beta.files.retrieveMetadata(stringfileID, FileRetrieveMetadataParamsparams?, RequestOptionsoptions?): FileMetadata`

**get** `/v1/files/{file_id}`

Get File Metadata

### Parameters

- `fileID: string`

  ID of the File.

- `params: FileRetrieveMetadataParams`

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

- `FileMetadata`

  - `id: string`

    Unique object identifier.

    The format and length of IDs may change over time.

  - `created_at: string`

    RFC 3339 datetime string representing when the file was created.

  - `filename: string`

    Original filename of the uploaded file.

  - `mime_type: string`

    MIME type of the file.

  - `size_bytes: number`

    Size of the file in bytes.

  - `type: "file"`

    Object type.

    For files, this is always `"file"`.

    - `"file"`

  - `downloadable?: boolean`

    Whether the file can be downloaded.

### Example

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env['ANTHROPIC_API_KEY'], // This is the default and can be omitted
});

const fileMetadata = await client.beta.files.retrieveMetadata('file_id');

console.log(fileMetadata.id);
```
