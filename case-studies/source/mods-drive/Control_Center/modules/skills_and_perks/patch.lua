-- ============================================================================
-- Module: Skill Tree & Character Perks (skills_and_perks)
-- Target: keen::SkillTreeResource, keen::Perk
-- ============================================================================

local Module = {}

function Module.OnInit(config, context)
    context.Log("Applying Skill Tree & Perk sliding scale modifications...")

    local discountPct = config.skill_point_discount_pct or 0
    local perkMult = config.perk_damage_multiplier or 1.0

    -- 1. Skill Point Cost Discount (0% to 100%)
    if discountPct > 0 then
        local trees = context.GetResources("keen::SkillTreeResource")
        if trees and #trees > 0 then
            local nodeCount = 0
            local factor = 1.0 - (discountPct / 100.0)
            for _, treeRes in ipairs(trees) do
                local tree = treeRes and treeRes.data
                if tree and tree.nodes and type(tree.nodes) == "table" then
                    for _, node in ipairs(tree.nodes) do
                        if node.cost and node.cost > 0 then
                            if discountPct >= 100 then
                                node.cost = 0
                            else
                                node.cost = math.max(1, math.floor(node.cost * factor))
                            end
                            nodeCount = nodeCount + 1
                        end
                        if node.skillPointCost and node.skillPointCost > 0 then
                            if discountPct >= 100 then
                                node.skillPointCost = 0
                            else
                                node.skillPointCost = math.max(1, math.floor(node.skillPointCost * factor))
                            end
                        end
                    end
                end
            end
            context.Log("Discounted skill point costs on " .. tostring(nodeCount) .. " nodes by " .. tostring(discountPct) .. "%!")
        end
    end

    -- 2. Perk Scaling (1.0x to 5.0x)
    if perkMult > 1.0 then
        local perks = context.GetResources("keen::Perk")
        if perks and #perks > 0 then
            local count = 0
            for _, perkRes in ipairs(perks) do
                local perk = perkRes and perkRes.data
                if perk then
                    if perk.damageModifier and perk.damageModifier > 0 then
                        perk.damageModifier = perk.damageModifier * perkMult
                        count = count + 1
                    end
                end
            end
            context.Log("Scaled " .. tostring(count) .. " combat perks by " .. tostring(perkMult) .. "x!")
        end
    end
end

return Module
