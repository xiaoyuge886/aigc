---
source_url: https://platform.claude.com/docs/en/api/admin/organizations/me
source_type: sitemap
content_hash: sha256:a47a10fa9717fd30e259e2d3278ed601ec43702ae770f823b037827956cf1bb0
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

## Me

**get** `/v1/organizations/me`

Retrieve information about the organization associated with the authenticated API key.

### Returns

- `Organization = object { id, name, type }`

  - `id: string`

    ID of the Organization.

  - `name: string`

    Name of the Organization.

  - `type: "organization"`

    Object type.

    For Organizations, this is always `"organization"`.

    - `"organization"`

### Example

```http
curl https://api.anthropic.com/v1/organizations/me \
    -H "X-Api-Key: $ANTHROPIC_ADMIN_API_KEY"
```
