---
source_url: https://platform.claude.com/docs/en/api/python/models/retrieve
source_type: sitemap
content_hash: sha256:5d7c7cb1abbd3960580c11eb2c2270b4c750cf10986b00521812d55be10b0d0b
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Retrieve

`models.retrieve(strmodel_id, ModelRetrieveParams**kwargs)  -> ModelInfo`

**get** `/v1/models/{model_id}`

Get a specific model.

The Models API response can be used to determine information about a specific model or resolve a model alias to a model ID.

### Parameters

- `model_id: str`

  Model identifier or alias.

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

- `class ModelInfo: …`

  - `id: str`

    Unique model identifier.

  - `created_at: datetime`

    RFC 3339 datetime string representing the time at which the model was released. May be set to an epoch value if the release date is unknown.

  - `display_name: str`

    A human-readable name for the model.

  - `type: Literal["model"]`

    Object type.

    For Models, this is always `"model"`.

    - `"model"`

### Example

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)
model_info = client.models.retrieve(
    model_id="model_id",
)
print(model_info.id)
```
