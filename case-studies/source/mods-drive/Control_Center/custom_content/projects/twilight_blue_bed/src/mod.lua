-- twilight_blue_bed: generated EML/KFC content project
-- Namespace: twilight_blue_bed
-- This starter is intentionally research-only until donor schemas are validated.
local kfc = require('kfc_content_registry')
local Module = {}

function Module.OnInit(config, context)
    context.Log('twilight_blue_bed: project loaded; no resources registered yet.')
    -- Add donor-specific cloning here only after validating the staged project.
    -- Use kfc.clone_resource and kfc.clone_recipe_set for the known safe paths.
end

return Module
