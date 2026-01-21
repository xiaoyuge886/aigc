---
source_url: https://platform.claude.com/docs/en/api/admin/workspaces/members/update
source_type: sitemap
content_hash: sha256:93d9ddda5bbc04f00868743bbb3efc5b98a6562332fe8b239cae8c7ead5abf11
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Update

**post** `/v1/organizations/workspaces/{workspace_id}/members/{user_id}`

Update Workspace Member

### Path Parameters

- `workspace_id: string`

  ID of the Workspace.

- `user_id: string`

  ID of the User.

### Body Parameters

- `workspace_role: "workspace_user" or "workspace_developer" or "workspace_admin" or "workspace_billing"`

  New workspace role for the User.

  - `"workspace_user"`

  - `"workspace_developer"`

  - `"workspace_admin"`

  - `"workspace_billing"`

### Returns

- `WorkspaceMember = object { type, user_id, workspace_id, workspace_role }`

  - `type: "workspace_member"`

    Object type.

    For Workspace Members, this is always `"workspace_member"`.

    - `"workspace_member"`

  - `user_id: string`

    ID of the User.

  - `workspace_id: string`

    ID of the Workspace.

  - `workspace_role: "workspace_user" or "workspace_developer" or "workspace_admin" or "workspace_billing"`

    Role of the Workspace Member.

    - `"workspace_user"`

    - `"workspace_developer"`

    - `"workspace_admin"`

    - `"workspace_billing"`

### Example

```http
curl https://api.anthropic.com/v1/organizations/workspaces/$WORKSPACE_ID/members/$USER_ID \
    -H 'Content-Type: application/json' \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY" \
    -d '{
          "workspace_role": "workspace_user"
        }'
```
