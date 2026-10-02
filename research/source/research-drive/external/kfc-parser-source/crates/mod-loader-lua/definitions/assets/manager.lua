--- @meta

--- The asset processor is used to access and modify game assets before the game starts.
---
---@class AssetManager
local AssetManager = {}

--- Returns an resource by its guid, type, and part.
---
--- @param guid Guid -- The unique identifier of the asset.
--- @param type string|Type -- The qualified type name of the asset, such as `keen::RenderModel`.
--- @param part u32? -- The part number of the asset, which is used for assets that are split into multiple parts. If not specified, defaults to 0.
--- @return Resource? -- The resource containing information and data about the asset.
function AssetManager.get_resource(guid, type, part) end

--- Returns resource identity without decoding the resource descriptor.
--- This is useful for probing resource families whose data schema is not yet
--- supported by the Lua reflection layer.
--- @param guid Guid
--- @param type string -- qualified type name
--- @param part u32?
--- @return table? -- { guid = string, type = string, part = number }
function AssetManager.get_resource_metadata(guid, type, part) end

--- Enumerates resource identities without decoding resource descriptors.
--- @param type string -- qualified type name
--- @return table[] -- { guid = string, type = string, part = number }
---@param limit? integer Maximum number of metadata rows to return.
function AssetManager.get_resource_metadata_by_type(type, limit) end

--- Resolves all resource identities matching a GUID without decoding payloads.
--- A GUID may be shared by multiple resource types or parts.
--- @param guid Guid
--- @return table[] -- { guid = string, type = string, part = number }
function AssetManager.get_resource_metadata_by_guid(guid) end

--- Returns a list of all resource's parts with the given guid and type.
---
--- @param guid Guid -- The unique identifier of the asset.
--- @param type string|Type -- The qualified type name of the asset, such as `keen::RenderModel`.
--- @return Resource[] -- A sorted list of resources for each part of the asset.
function AssetManager.get_resource_parts(guid, type) end

--- Returns a list of all resources with the given type.
---
--- @param type string|Type -- The qualified type name of the asset, such as `keen::RenderModel`.
--- @return Resource[] -- A list of resources for the specified type.
function AssetManager.get_resources_by_type(type) end

--- Returns a list of all resources in the game.
---
--- @return Resource[] -- A list of all resources in the game.
function AssetManager.get_all_resources() end

--- Returns a list of all resource types in the game.
---
--- @return Type[] -- A list of all resource types in the game.
function AssetManager.get_resource_types() end

--- Creates a new resource with the specified value and type.
---
--- The returned resource will contain a newly generated guid which can be used
--- to reference this resource in other assets.
--- The part number of the new resource will be 0.
---
--- ### Errors
--- - When the specified type is not registered in the game.
--- - When the provided value is not compatible with the specified type.
---
--- @param value any -- The value to be stored in the resource. This must be compatible with the specified type.
--- @param type string|Type -- The qualified type name of the asset, such as `keen::RenderModel`.
--- @return Resource
function AssetManager.create_resource(value, type) end

--- Creates a new resource with the specified value, type, part, and guid.
---
--- This method is primarily used for creating resources which are split into multiple parts.
--- You first create a new resource with `AssetManager.create_resource` to get a new guid,
--- then use that guid to create additional parts of the same resource.
---
--- ### Errors
--- - When the specified type is not registered in the game.
--- - When the provided value is not compatible with the specified type.
--- - When the provided guid and part is not unique and is already used by another asset.
---
--- @param value any -- The value to be stored in the resource. This must be compatible with the specified type.
--- @param type string|Type -- The qualified type name of the asset, such as `keen::RenderModel`.
--- @param guid Guid -- The guid to assign to the new resource.
--- @param part u32 -- The part number of the asset.
--- @return Resource
function AssetManager.create_resource(value, type, guid, part) end

--- Registers a new KFC resource descriptor with an explicit guid and part.
---
--- This is the named registration form for mods that add new content. The
--- resource is written by the patch writer and is also returned by resource
--- discovery functions after registration.
---
--- @param value any -- The descriptor value, compatible with the specified type.
--- @param type string|Type -- The qualified type name, such as `keen::ItemInfo`.
--- @param guid Guid -- A new guid not already used by the archive.
--- @param part u32 -- The resource part number, normally 0.
--- @return Resource
function AssetManager.register_resource(value, type, guid, part) end

--- Returns a content by its guid.
---
--- @param guid Guid|keen.ContentHash -- The unique identifier of the asset.
--- @return Content? -- A content resource containing information about and the raw data of the asset.
function AssetManager.get_content(guid) end

--- Returns a list of all contents.
---
--- @return Content[] -- A list of all content resources in the game.
function AssetManager.get_all_contents() end

--- Creates a new content with the specified data.
---
--- The returned content will contain a newly generated guid which can be used
--- to reference this content in other assets.
---
--- @param data Buffer -- The raw binary data to be stored in the content.
--- @return Content
function AssetManager.create_content(data) end
