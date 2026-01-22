---
source_url: https://platform.claude.com/docs/en/api/admin/workspaces/create
source_type: sitemap
content_hash: sha256:5446981e66510a224001bc77b7a2e773cc9aa863257f4fa046de3ad2a70f4a7e
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Create

**post** `/v1/organizations/workspaces`

Create Workspace

### Body Parameters

- `name: string`

  Name of the Workspace.

### Returns

- `Workspace = object { id, archived_at, created_at, 3 more }`

  - `id: string`

    ID of the Workspace.

  - `archived_at: string`

    RFC 3339 datetime string indicating when the Workspace was archived, or null if the Workspace is not archived.

  - `created_at: string`

    RFC 3339 datetime string indicating when the Workspace was created.

  - `display_color: string`

    Hex color code representing the Workspace in the Anthropic Console.

  - `name: string`

    Name of the Workspace.

  - `type: "workspace"`

    Object type.

    For Workspaces, this is always `"workspace"`.

    - `"workspace"`

### Example

```http
curl https://api.anthropic.com/v1/organizations/workspaces \
    -H 'Content-Type: application/json' \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY" \
    -d '{
          "name": "x"
        }'
```
