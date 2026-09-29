# SUZY//WORLD

SUZY//AI's local world is private by default.

SUZY//WORLD is the deliberately public knowledge layer:

```text
PRIVATE
~/.suzy-ai/
    │
    │ explicit publish
    ▼
PUBLIC
https://www.suzyeaston.ca/wp-json/suzy-world/v1
```

Source:

```text
https://github.com/suzyeaston/suzy-world
```

## No automatic sync

A private memory is not public merely because it exists.

SUZY//AI should eventually offer a review/publish workflow that converts selected private knowledge into SUZY//WORLD API writes.

Public records should retain:

- stable public IDs,
- version history,
- tags,
- relationships,
- provenance,
- asset credit / rights metadata.

SUZY//AI may cache public records locally, but the public ID and source URL remain canonical references so data is not silently forked.
