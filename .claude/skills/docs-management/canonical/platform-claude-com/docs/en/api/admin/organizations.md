---
source_url: https://platform.claude.com/docs/en/api/admin/organizations
source_type: sitemap
content_hash: sha256:f82e43c0d9689f217f54b76fd972d77ad73d5295e6cd2f151a9c6a392d36db4e
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

# Organizations

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

## Domain Types

### Organization

- `Organization = object { id, name, type }`

  - `id: string`

    ID of the Organization.

  - `name: string`

    Name of the Organization.

  - `type: "organization"`

    Object type.

    For Organizations, this is always `"organization"`.

    - `"organization"`
