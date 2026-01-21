---
source_url: https://platform.claude.com/docs/en/api/admin/invites/delete
source_type: sitemap
content_hash: sha256:81dfae08c140091ffc93cc928d024ad9edd9b018dc6793235fc67c628361f69e
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Delete

**delete** `/v1/organizations/invites/{invite_id}`

Delete Invite

### Path Parameters

- `invite_id: string`

  ID of the Invite.

### Returns

- `id: string`

  ID of the Invite.

- `type: "invite_deleted"`

  Deleted object type.

  For Invites, this is always `"invite_deleted"`.

  - `"invite_deleted"`

### Example

```http
curl https://api.anthropic.com/v1/organizations/invites/$INVITE_ID \
    -X DELETE \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY"
```
