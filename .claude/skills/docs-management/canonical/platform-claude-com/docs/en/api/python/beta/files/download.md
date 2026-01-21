---
source_url: https://platform.claude.com/docs/en/api/python/beta/files/download
source_type: sitemap
content_hash: sha256:65a70fcd59a0155d9150092dc16562cd8f5ad4cc8d35114329b4b2f43511f136
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Download

`beta.files.download(strfile_id, FileDownloadParams**kwargs)  -> BinaryResponseContent`

**get** `/v1/files/{file_id}/content`

Download File

### Parameters

- `file_id: str`

  ID of the File.

- `betas: Optional[List[AnthropicBetaParam]]`

  Optional header to specify the beta version(s) you want to use.

  - `UnionMember0 = str`

  - `UnionMember1 = Literal["message-batches-2024-09-24", "prompt-caching-2024-07-31", "computer-use-2024-10-22", 16 more]`

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

- `BinaryResponseContent`

### Example

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)
response = client.beta.files.download(
    file_id="file_id",
)
print(response)
content = response.read()
print(content)
```
