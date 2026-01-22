---
source_url: https://platform.claude.com/docs/en/api/go/messages/batches/delete
source_type: sitemap
content_hash: sha256:646f74b47911415e5bf68f98faf63b3195123369f63ff9ea9d47029de680a535
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Delete

`client.Messages.Batches.Delete(ctx, messageBatchID) (*DeletedMessageBatch, error)`

**delete** `/v1/messages/batches/{message_batch_id}`

Delete a Message Batch.

Message Batches can only be deleted once they've finished processing. If you'd like to delete an in-progress batch, you must first cancel it.

Learn more about the Message Batches API in our [user guide](https://docs.claude.com/en/docs/build-with-claude/batch-processing)

### Parameters

- `messageBatchID string`

  ID of the Message Batch.

### Returns

- `type DeletedMessageBatch struct{…}`

  - `ID string`

    ID of the Message Batch.

  - `Type MessageBatchDeleted`

    Deleted object type.

    For Message Batches, this is always `"message_batch_deleted"`.

    - `const MessageBatchDeletedMessageBatchDeleted MessageBatchDeleted = "message_batch_deleted"`

### Example

```go
package main

import (
  "context"
  "fmt"

  "github.com/anthropics/anthropic-sdk-go"
  "github.com/anthropics/anthropic-sdk-go/option"
)

func main() {
  client := anthropic.NewClient(
    option.WithAPIKey("my-anthropic-api-key"),
  )
  deletedMessageBatch, err := client.Messages.Batches.Delete(context.TODO(), "message_batch_id")
  if err != nil {
    panic(err.Error())
  }
  fmt.Printf("%+v\n", deletedMessageBatch.ID)
}
```
