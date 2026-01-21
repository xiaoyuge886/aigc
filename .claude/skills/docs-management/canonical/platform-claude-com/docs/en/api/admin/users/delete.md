---
source_url: https://platform.claude.com/docs/en/api/admin/users/delete
source_type: sitemap
content_hash: sha256:6635dd6d4c0dea6a9b4156954e5ec252aec559d43b25fe38cbed4cae4f877132
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Delete

**delete** `/v1/organizations/users/{user_id}`

Remove User

### Path Parameters

- `user_id: string`

  ID of the User.

### Returns

- `id: string`

  ID of the User.

- `type: "user_deleted"`

  Deleted object type.

  For Users, this is always `"user_deleted"`.

  - `"user_deleted"`

### Example

```http
curl https://api.anthropic.com/v1/organizations/users/$USER_ID \
    -X DELETE \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY"
```
