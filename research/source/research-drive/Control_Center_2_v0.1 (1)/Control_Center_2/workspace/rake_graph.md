# Static dependency graph: Tool_T0_Rake_Wooden

- Item GUID: `f9abaf9b-060c-470d-a8c3-c7c567ebaa1e`
- Game build: **UNKNOWN**
- EML version: **UNKNOWN**
- Validation: **PASS**

| Node | Status | Source | Field |
|---|---|---|---|
| ItemInfo | PROVEN | ItemInfo/ItemInfo/f9abaf9b-060c-470d-a8c3-c7c567ebaa1e_b5ce8765_0.json | `$guid/itemId` |
| ItemRegistryResource | PROVEN | ItemRegistryResource/ItemRegistryResource/3064d35d-7342-40ca-bdc9-aad58f83bf45_72ab39b6_0.json | `itemRefs[2821]` |
| RecipeRegistryResource | PROVEN | RecipeRegistryResource/RecipeRegistryResource/5e57de0f-280c-4559-8191-f02c1ba656e2_5f5382cf_0.json | `recipes[13]` |
| ItemKnowledgeResource | PROVEN | ItemKnowledgeResource/knowledgeArray | `knowledgeArray[].itemId` |
| WorkshopRegistryResource | PROVEN | WorkshopRegistryResource/WorkshopRegistryResource/3baba1c2-bc82-4ab7-b20e-16dec28208af_a8ea5924_0.json | `workshops[].workshopId` |
| localization | UNSOLVED | / | `` |
| visual | UNSOLVED | / | `` |

## Evidence classification

- **PROVEN:** observed in the indexed KFC snapshot and linked by actual GUID/item ID fields.
- **INFERRED:** a complete custom item likely needs coordinated registration, recipe, knowledge, workshop, localization, and visual dependencies.
- **EXPERIMENTAL:** runtime creation, registration timing, ID allocation, and API signatures.
- **UNSOLVED:** game build and installed EML version; no runtime mutation is authorized.
