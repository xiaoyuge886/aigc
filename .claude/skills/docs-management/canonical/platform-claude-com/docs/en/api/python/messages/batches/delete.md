---
source_url: https://platform.claude.com/docs/en/api/python/messages/batches/delete
source_type: sitemap
content_hash: sha256:74cd4bbe006b91b26d57aac7a654f489294abe32b24f440a8465c45cb3977acf
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Delete

`messages.batches.delete(strmessage_batch_id)  -> DeletedMessageBatch`

**delete** `/v1/messages/batches/{message_batch_id}`

Delete a Message Batch.

Message Batches can only be deleted once they've finished processing. If you'd like to delete an in-progress batch, you must first cancel it.

Learn more about the Message Batches API in our [user guide](https://docs.claude.com/en/docs/build-with-claude/batch-processing)

### Parameters

- `message_batch_id: str`

  ID of the Message Batch.

### Returns

- `class DeletedMessageBatch: …`

  - `id: str`

    ID of the Message Batch.

  - `type: Literal["message_batch_deleted"]`

    Deleted object type.

    For Message Batches, this is always `"message_batch_deleted"`.

    - `"message_batch_deleted"`

### Example

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)
deleted_message_batch = client.messages.batches.delete(
    "message_batch_id",
)
print(deleted_message_batch.id)
```
