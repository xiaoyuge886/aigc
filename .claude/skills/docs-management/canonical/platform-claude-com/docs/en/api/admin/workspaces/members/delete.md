---
source_url: https://platform.claude.com/docs/en/api/admin/workspaces/members/delete
source_type: sitemap
content_hash: sha256:9e050ff54283e63ba1770d22f0df7cc6e98098a78f34c55f1cef0bdd336c10c2
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Delete

**delete** `/v1/organizations/workspaces/{workspace_id}/members/{user_id}`

Delete Workspace Member

### Path Parameters

- `workspace_id: string`

  ID of the Workspace.

- `user_id: string`

  ID of the User.

### Returns

- `type: "workspace_member_deleted"`

  Deleted object type.

  For Workspace Members, this is always `"workspace_member_deleted"`.

  - `"workspace_member_deleted"`

- `user_id: string`

  ID of the User.

- `workspace_id: string`

  ID of the Workspace.

### Example

```http
curl https://api.anthropic.com/v1/organizations/workspaces/$WORKSPACE_ID/members/$USER_ID \
    -X DELETE \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY"
```
