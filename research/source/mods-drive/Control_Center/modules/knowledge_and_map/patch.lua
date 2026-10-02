-- ============================================================================
-- Module: Game Knowledge, Lore & Quests (knowledge_and_map)
-- Target: keen::GameKnowledgeResource, keen::ItemKnowledgeResource
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Game Knowledge & Quest sliding scale modifications...")

    local spMult = config.knowledge_sp_multiplier or 1.0

    if spMult > 1.0 then
        local knowledgeList = context.GetResources("keen::GameKnowledgeResource")
        if knowledgeList and #knowledgeList > 0 then
            for _, res in ipairs(knowledgeList) do
                local d = res and res.data
                if d and d.skillPoints and type(d.skillPoints) == "table" then
                    for i = 1, #d.skillPoints do
                        d.skillPoints[i] = math.floor(d.skillPoints[i] * spMult)
                    end
                end
            end
            context.Log("Scaled knowledge discovery skill points by " .. tostring(spMult) .. "x!")
        end
    end

    -- Auto-unlock all recipes & item knowledge in UI
    local unlockKnowledge = config.unlock_all_recipe_knowledge ~= false
    if unlockKnowledge then
        local itemKnowledgeList = context.GetResources("keen::ItemKnowledgeResource") or {}
        local count = 0
        for _, res in ipairs(itemKnowledgeList) do
            local d = res and res.data
            if d and d.knowledgeArray then
                for _, k in ipairs(d.knowledgeArray) do
                    k.lockedKnowledgeMask = {}
                    count = count + 1
                end
            end
        end
        context.Log("Cleared lockedKnowledgeMask for " .. tostring(count) .. " items across keen::ItemKnowledgeResource!")
    end
end

return Module
