--- @meta

--- Represents a specific raw binary asset in the game, identified by its guid.
---
--- @class Content
--- @field guid Guid -- A 32 character hexadecimal string representing the asset's unique identifier.
--- @field size u32 -- The size of the asset in bytes.
--- @field hash0 u32
--- @field hash1 u32
--- @field hash2 u32
local Content = {}

--- Reads the raw binary data of the asset.
---
--- @return Buffer -- A read-only buffer containing the raw binary data of the asset.
function Content:read_data() end

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

-- TODO: implement `Resource::original_data`

--- Represents a specific resource in the game, identified by its guid, type, and part.
---
--- @class Resource
--- @field guid Guid
--- @field type Type
--- @field part u32 -- The part number of the asset, which is used for assets that are split into multiple parts.
--- @field data unknown -- The data of the asset whose structure is defined by the `type` field.
--- @field original_data unknown -- A read-only reference to the original data of the asset.
local Resource = {}

--- @alias ImageFormat
--- | "png"
--- | "jpg" -- same as jpeg
--- | "jpeg" -- same as jpg
--- | "gif"
--- | "webp"
--- | "pnm"
--- | "tiff"
--- | "tga"
--- | "dds"
--- | "bmp"
--- | "ico"
--- | "hdr"
--- | "openexr"
--- | "farbfeld"
--- | "avif"
--- | "qoi"
--- | "pcx"

--- Provides utility functions for working with images.
---
--- @class ImageHelper
image = {}

--- Creates a new image with the specified width and height.
--- The image is initialized with #00000000 (transparent black) pixels.
---
--- @param width u32 -- The width of the image in pixels.
--- @param height u32 -- The height of the image in pixels.
--- @return Image -- The newly created image.
function image.create(width, height) end

--- Decodes a buffer to an image using the specified `ImageFormat`.
---
--- If no format is provided, the function will attempt to guess the format based on the buffer content.
--- This incldues all images in `ImageFormat`, except TGA.
---
--- @param buffer Buffer -- The buffer containing the image data.
--- @param format ImageFormat? -- The format of the input buffer, otherwise it will be guessed.
--- @return Image -- The decoded image.
function image.decode(buffer, format) end

--- Decodes a buffer to an image using the specified `PixelFormat`.
---
--- @param buffer Buffer -- The buffer containing the texture data.
--- @param format keen.PixelFormat -- The format of the input buffer.
--- @param width u32 -- The width of the image in pixels.
--- @param height u32 -- The height of the image in pixels.
--- @param mipmap_level u32? -- The mipmap level to decode, defaults to 0.
--- @return Image -- The decoded image.
function image.decode_texture(buffer, format, width, height, mipmap_level) end

--- Encodes an image to a buffer in the specified format.
---
--- @param image Image -- The image to encode.
--- @param format ImageFormat? -- The format to encode the image to, defaults to "png".
--- @return Buffer -- The encoded image data as a buffer.
function image.encode(image, format) end

--- Encode an image to a buffer in the specified `PixelFormat`.
---
--- @param image Image -- The image to encode.
--- @param format keen.PixelFormat -- The pixel format to encode the image to.
--- @return Buffer -- The encoded image data as a buffer.
function image.encode_texture(image, format) end

--- @class Image
--- @field width u32 -- The width of the image in pixels.
--- @field height u32 -- The height of the image in pixels.
local Image = {}

--- Returns the pixel color at the specified coordinates or `nil` if out of bounds.
---
--- @param x u32 -- The x-coordinate of the pixel.
--- @param y u32 -- The y-coordinate of the pixel.
--- @return u8, u8, u8, u8 -- The RGBA components of the pixel color, each in the range 0-255.
function Image:get_pixel(x, y) end

--- Sets the pixel color at the specified coordinates.
---
--- ### Errors
--- - If the coordinates are out of bounds.
---
--- @param x u32 -- The x-coordinate of the pixel.
--- @param y u32 -- The y-coordinate of the pixel.
--- @param r u8 -- The red component of the pixel color, in the range 0-255.
--- @param g u8 -- The green component of the pixel color, in the range 0-255.
--- @param b u8 -- The blue component of the pixel color, in the range 0-255.
--- @param a u8 -- The alpha component of the pixel color, in the range 0-255.
function Image:set_pixel(x, y, r, g, b, a) end

--- Returns the pixel color at the specified coordinates as a packed 32 bit integer in RGBA format, or `nil` if out of bounds.
--- The integer is packed as follows: `0xRRGGBBAA`.
---
--- @param x u32 -- The x-coordinate of the pixel.
--- @param y u32 -- The y-coordinate of the pixel.
--- @return u32 -- The packed RGBA color of the pixel.
function Image:get_pixel_packed(x, y) end

--- Sets the pixel color at the specified coordinates using a packed 32 bit integer in RGBA format.
--- The integer is packed as follows: `0xRRGGBBAA`.
---
--- ### Errors
--- - If the coordinates are out of bounds.
---
--- @param x u32 -- The x-coordinate of the pixel.
--- @param y u32 -- The y-coordinate of the pixel.
--- @param color u32 -- The packed RGBA color of the pixel.
function Image:set_pixel_packed(x, y, color) end

-- TODO: extensions such as reading/writing vectors, matrices, objects, guids and other common types.

--- Factory for creating and wrapping [Buffer](lua://Buffer) objects.
---
--- @class BufferFactory
buffer = {}

--- Creates a new [Buffer](lua://Buffer) with an optional initial capacity.
--- The **capacity** is not to be confused with the actual size; it is simply the amount of space the buffer can work with before needing to resize.
---
--- An initial capacity can help avoid unnecessary reallocations if the expected size is known in advance thus improving performance.
---
--- @param initial_capacity integer? -- initial capacity in bytes (defaults to 0)
--- @return Buffer
function buffer.create(initial_capacity) end

--- Creates a new [Buffer](lua://Buffer) containing the bytes of the given string.
--- The **capacity** and **tail** are set to the length of the string, and the **head** is set to 0.
---
--- @param str string
--- @return Buffer
function buffer.wrap(str) end

--- A [Buffer](lua://Buffer) is a (mutable or immutable) sequence of bytes for reading and writing binary data.
---
--- Buffers act like a FIFO (first-in, first-out) queue of bytes, with 0-based byte offsets:
--- - **head** is the read position (next byte to read).
--- - **tail** is the write position (next byte to write).
---
--- That means that bytes are read in the order they were written, unless you modify the **head** or **tail** manually.
---
--- Reading or writing bytes advances the respective position.
--- If **head** exceeds **tail**, a read error occurs.
---
--- The **capacity** is the total allocated size of the buffer. It will be automatically increased as needed when writing but the amount of growth may vary.
--- It is not to be confused with the actual size; it is simply the amount of space the buffer can work with before needing to resize.
--- The actual size is determined by the difference between **tail** and **head**.
---
--- ### Example
---
--- Write example:
---
--- ```lua
--- local buf = buffer.create()  -- Create a new empty buffer
---
--- buf:write_u8(42)             -- Write a byte (0x2A)
--- buf:write_string("Hello")    -- Write a string ("Hello")
---
--- assert(buf:tail() == 6)      -- Tail is now at position 6
--- assert(buf:head() == 0)      -- Head is still at position 0
--- ```
---
--- Read example:
---
--- ```lua
--- local a = buf:read_u8()        -- Read a byte (0x2A)
--- local str = buf:read_string(5) -- Read a string ("Hello")
---
--- assert(a == 42)                -- a is 42
--- assert(str == "Hello")         -- str is "Hello"
---
--- assert(buf:head() == 6)        -- Head is now at position 6
--- assert(buf:tail() == 6)        -- Tail is still at position 6
--- ```
---
--- @see BufferFactory
--- @class Buffer
local Buffer = {}

--- Returns this buffer's current **head**.
---
--- ### Errors
--- - When this buffer is closed.
---
--- @return u64
function Buffer:head() end

--- Sets this buffer's current **head** to the specified value.
---
--- ### Errors
--- - When `position` is less than 0 or greater than this buffer's **tail**.
--- - When this buffer is closed.
---
--- @param position u64
function Buffer:head(position) end

--- Returns this buffer's **tail**.
---
--- ### Errors
--- - When this buffer is closed.
---
--- @return u64
function Buffer:tail() end

--- Sets this buffer's **tail** to the specified value.
---
--- ### Errors
--- - When `position` is less than 0 or greater than this buffer's **capacity**.
--- - When this buffer is closed.
---
--- @param position u64
function Buffer:tail(position) end

--- Returns the number of bytes remaining in this buffer, which is the difference between the **tail** and the current **head**.
---
--- ### Errors
--- - When this buffer is closed.
---
--- @return u64
function Buffer:remaining() end

--- Returns this buffer's **capacity**.
---
--- ### Errors
--- - When this buffer is closed.
---
--- @return u64
function Buffer:capacity() end

--- Resets this buffer, setting both the **head** and **tail** to 0.
--- The **capacity** remains unchanged.
---
--- ### Errors
--- - When this buffer is closed.
function Buffer:reset() end

--- Reserves at least `length` more bytes in this buffer at the current **tail**.
--- This will only increase the **capacity** of this buffer if it is not sufficient.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param length integer
function Buffer:reserve(length) end

--- The [ByteOrder](lua://ByteOrder) determines how multi-byte values are laid out in a buffer.
---
--- This affects methods that read or write multiple bytes at once, such as `read_i16`, `read_f32`, etc.
---
--- ### Values
--- - `little`: The least significant byte is stored at the lowest address (first).
--- - `big`: The most significant byte is stored at the lowest address (first).
--- - `default`: Currently refers to `little`, which is what the game primarily uses.
---
--- ### Example
--- Given a buffer containing the bytes `0x01 0x02`:
--- - If the byte order is `little`, reading a 16-bit integer would yield `0x0201` (513 in decimal).
--- - If the byte order is `big`, reading a 16-bit integer would yield `0x0102` (258 in decimal).
---
--- @alias ByteOrder "default" | "little" | "big"

--- Returns this buffer's [ByteOrder](lua://ByteOrder).
---
--- ### Errors
--- - When this buffer is closed.
---
--- @return "little" | "big"
function Buffer:order() end

--- Sets this buffer's [ByteOrder](lua://ByteOrder) to the specified value.
---
--- ### Errors
--- - When this buffer is closed.
---
--- @param order "little" | "big" | "default"
function Buffer:order(order) end

--- Skips the next `length` bytes in this buffer without reading them.
---
--- ### Errors
--- - When `length` is less than 0 or greater than the buffer's remaining bytes.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @param length u64 -- The number of bytes to skip.
function Buffer:skip(length) end

--- Copies the contents of `src` at the specified `offset` and `length` into `self` at the current **tail**.
--- If `src` is `self`, it instead moves the data within `self`.
---
--- This does not change the **head** of `src`.
---
--- ### Errors
--- - When `offset` and `length` are either negative or out of bounds for `src`.
--- - When `self` is not writable.
--- - When `src` is not readable.
--- - When either `self` or `src` is closed.
---
--- @param src Buffer
--- @param offset u64? -- The offset in `src` relative to its **head** to start copying from. If not specified, it will start from the **head** of `src`.
--- @param length u64? -- The number of bytes to copy from `src`. If not specified, it will copy all remaining bytes from `src`.
function Buffer:copy(src, offset, length) end

--- Closes this buffer, releasing any resources associated with it.
--- After closing, this buffer can no longer be used.
--- This function may be called multiple times without raising an error.
function Buffer:close() end

--- Reads the byte at this buffer's current **head** and then increments the **head** by `1`.
--- If the byte is non-zero, it will return `true`, otherwise it will return `false`.
---
--- ### Errors
--- - When there are no bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return boolean -- The boolean value read.
function Buffer:read_bool() end

--- Reads the byte at this buffer's current **head**, interpreting it as an 8-bit signed integer, and then increments the **head** by `1`.
---
--- ### Errors
--- - When there are no bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return i8 -- The signed 8-bit integer read.
function Buffer:read_i8() end

--- Reads the byte at this buffer's current **head**, interpreting it as an 8-bit unsigned integer, and then increments the **head** by `1`.
---
--- ### Errors
--- - When there are no bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return u8 -- The unsigned 8-bit integer read.
function Buffer:read_u8() end

--- Reads the next two bytes at this buffer's current **head**, interpreting them as a 16-bit signed integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `2`.
---
--- ### Errors
--- - When there are fewer than two bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return i16 -- The signed 16-bit integer read.
function Buffer:read_i16() end

--- Reads the next two bytes at this buffer's current **head**, interpreting them as a 16-bit unsigned integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `2`.
---
--- ### Errors
--- - When there are fewer than two bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return u16 -- The unsigned 16-bit integer read.
function Buffer:read_u16() end

--- Reads the next four bytes at this buffer's current **head**, interpreting them as a 32-bit signed integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `4`.
---
--- ### Errors
--- - When there are fewer than four bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return i32 -- The signed 32-bit integer read.
function Buffer:read_i32() end

--- Reads the next four bytes at this buffer's current **head**, interpreting them as a 32-bit unsigned integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `4`.
---
--- ### Errors
--- - When there are fewer than four bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return u32 -- The unsigned 32-bit integer read.
function Buffer:read_u32() end

--- Reads the next eight bytes at this buffer's current **head**, interpreting them as a 64-bit signed integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `8`.
---
--- ### Errors
--- - When there are fewer than eight bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return i64 -- The signed 64-bit integer read.
function Buffer:read_i64() end

--- Reads the next eight bytes at this buffer's current **head**, interpreting them as a 64-bit unsigned integer according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `8`.
---
--- ### Errors
--- - When there are fewer than eight bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return u64 -- An integer with the same binary representation as the 64-bit unsigned integer read.
function Buffer:read_u64() end

--- Reads the next two bytes at this buffer's current **head**, interpreting them as a 16-bit floating point number according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `2`.
---
--- ### Errors
--- - When there are fewer than two bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return f16 -- The 16-bit floating point number read.
function Buffer:read_f16() end

--- Reads the next four bytes at this buffer's current **head**, interpreting them as a 32-bit floating point number according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `4`.
---
--- ### Errors
--- - When there are fewer than four bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return f32 -- The 32-bit floating point number read.
function Buffer:read_f32() end

--- Reads the next eight bytes at this buffer's current **head**, interpreting them as a 64-bit floating point number according to the current [ByteOrder](lua://ByteOrder), and then increments the **head** by `8`.
---
--- ### Errors
--- - When there are fewer than eight bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return f64 -- The 64-bit floating point number read.
function Buffer:read_f64() end

--- Reads a sequence of characters from this buffer, starting at the current **head**.
--- Each character is read as a byte, and the **head** is incremented by `length`.
---
--- ### Errors
--- - When there are fewer than `length` bytes remaining in this buffer.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @param length u64 -- The number of characters to read.
--- @return string -- The string read.
function Buffer:read_string(length) end

--- Reads a resource of the specified `type` from this buffer at the current **head**.
---
--- **TODO:** Currently this function will not increment the head after reading.
---
--- ### Errors
--- - When `type` is not valid.
--- - When the bytes do not match the expected format.
--- - When there are not enough bytes remaining in this buffer to read the resource.
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
---@param type string|Type -- The qualified type name of the resource to read, such as `keen::RenderModel`
---@return unknown -- The resource read
function Buffer:read_resource(type) end

--- Writes a single byte at this buffer's current **tail** representing the given boolean value, and then increments the **tail** by `1`.
--- If the value is true, it writes 1; otherwise, it writes 0.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value boolean -- The boolean value to write.
function Buffer:write_bool(value) end

--- Writes an 8-bit signed integer at this buffer's current **tail**, and then increments the **tail** by `1`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value i8 -- The signed 8-bit integer to write.
function Buffer:write_i8(value) end

--- Writes an 8-bit unsigned integer at this buffer's current **tail**, and then increments the **tail** by `1`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value u8 -- The unsigned 8-bit integer to write.
function Buffer:write_u8(value) end

--- Writes a 16-bit signed integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `2`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value i16 -- The signed 16-bit integer to write.
function Buffer:write_i16(value) end

--- Writes a 16-bit unsigned integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `2`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value u16 -- The unsigned 16-bit integer to write.
function Buffer:write_u16(value) end

--- Writes a 32-bit signed integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `4`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value i32 -- The signed 32-bit integer to write.
function Buffer:write_i32(value) end

--- Writes a 32-bit unsigned integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `4`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value u32 -- The unsigned 32-bit integer to write.
function Buffer:write_u32(value) end

--- Writes a 64-bit signed integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `8`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value i64 -- The signed 64-bit integer to write.
function Buffer:write_i64(value) end

--- Writes a 64-bit unsigned integer at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `8`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value u64 -- The unsigned 64-bit integer to write.
function Buffer:write_u64(value) end

--- Writes a 16-bit floating point number at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `2`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value f16 -- The 16-bit floating point number to write.
function Buffer:write_f16(value) end

--- Writes a 32-bit floating point number at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `4`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value f32 -- The 32-bit floating point number to write.
function Buffer:write_f32(value) end

--- Writes a 64-bit floating point number at this buffer's current **tail** according to the current [ByteOrder](lua://ByteOrder), and then increments the **tail** by `8`.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param value f64 -- The 64-bit floating point number to write.
function Buffer:write_f64(value) end

--- Writes the bytes of the given string at this buffer's current **tail**, and then increments the **tail** by the length of the string.
--- No null terminator or length prefix is written.
---
--- ### Errors
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param str string -- The string to write.
function Buffer:write_string(str) end

--- Writes resource of the specified `type` at this buffer's current **tail**.
---
--- ### Errors
--- - When `type` is not valid.
--- - When the value does not match the expected format for `type`.
--- - When this buffer is not writable.
--- - When this buffer is closed.
---
--- @param type string|Type -- The qualified type name of the resource to write, such as `keen::RenderModel`
--- @param value unknown -- The resource to write.
function Buffer:write_resource(type, value) end

--- Returns a string containing the bytes from this buffer between the current **head** and the **tail**.
---
--- ### Errors
--- - When this buffer is not readable.
--- - When this buffer is closed.
---
--- @return string
function Buffer:to_string() end

--- This is the primary object for accessing or modifying anything in the game.
---
--- @class Game
---
--- @field version string -- Represents the version of this game which does not follow any specific format and is purely extracted from the game's kfc file.
--- @field assets AssetManager -- A reference to the mod loader's asset manager.
--- @field guid GuidHelper -- A helper for creating GUIDs from content hashes.
--- @field types TypeRegistry
game = {}

--- @alias bool boolean

--- 8-bit unsigned integer (0 to 255)
--- @alias u8 integer

--- 8-bit signed integer (-128 to 127)
--- @alias i8 integer

--- 16-bit unsigned integer (0 to 65535)
--- @alias u16 integer

--- 16-bit signed integer (-32768 to 32767)
--- @alias i16 integer

--- 32-bit unsigned integer (0 to 4294967295)
--- @alias u32 integer

--- 32-bit signed integer (-2147483648 to 2147483647)
--- @alias i32 integer

--- 64-bit unsigned integer (0 to 18446744073709551615)
--- Treats lua's 64-bit signed integers as 64-bit unsigned values by reinterpreting the raw bits.
--- Negative `integer` values will appear as large `u64` values (e.g. -1 becomes 18446744073709551615).
--- @alias u64 integer

--- 64-bit signed integer (-9223372036854775808 to 9223372036854775807)
--- @alias i64 integer

--- 16-bit floating point number (half-precision)
--- @alias f16 number

--- 32-bit floating point number (single-precision)
--- @alias f32 number

--- 64-bit floating point number (double-precision)
--- @alias f64 number

--- A set of flags of type `T`, represented as an array of `T` values.
--- @generic T
--- @alias Bitmask<T> T[]

--- A static array of type `T` with a fixed length of `N`.
--- @generic T, N
--- @alias StaticArray<T, N> T[]

--- An array of type `T`.
--- @generic T
--- @alias Array<T> T[]

--- A variant type that can hold a value of any sub-type `T`.
--- `type` is a string representing the qualified type name of the value stored in `value`.
--- @generic T
--- @alias Variant<T> { type: string, value: T }

--- Represents a globally unique identifier (GUID) used to uniquely identify assets in the game.
--- The GUID is a 36 character long string in the format of `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` where each `X` is a hexadecimal digit.
--- Accepts `Resource` and `Content` objects as well, automatically extracting their `guid` field.
--- @alias Guid string

--- A reference to an object of type `T`, represented by its GUID.
--- Accepts `Resource` objects as well, automatically extracting their `guid` field.
--- @generic T
--- @alias ObjectReference<T> Guid

--- Returns the type of the given value as a string.
--- In comparison to `type`, this function returns a more explicit name for userdata types.
--- Otherwise, it behaves like `type`.
---
--- @param value any -- The value to get the type of.
--- @return string -- The type of the value as a string.
function typeof(value) end

--- Loads the given module and returns its value. If the module is not found, it will error with a message describing the issue.
---
--- The path should be a dotted path to the module, such as `my_module.sub_module` or `mods.my_mod.my_module`.
---
--- To load a module from other mods, you can use the `mods` prefix followed by the mod id, such as `mods.id.path`.
--- When omitting the path after `mods.id`, it will load the mod's main module, which is typically `mod.lua`. (This is equivalent to `mods.id.mod`.)
---
--- @param path string -- A dotted path to the module, such as `my_module.sub_module` or `mods.my_mod.my_module`.
--- @return unknown
function require(path) end

--- The built-in modules available in the Lua environment.
--- All of these are globally accessible, but are also available under the `builtin` table.
builtin = {
	io = io,
	integer = integer,
	game = game,
	buffer = buffer,
	hasher = hasher,
	loader = loader,
	image = image,
}

--- Provides utility functions for working with GUIDs.
---
--- @class GuidHelper
--- @field NONE Guid
local GuidHelper = {}

--- Creates a GUID from the given ContentHash.
--- @param content_hash keen.ContentHash
--- @return Guid
function GuidHelper.from_content_hash(content_hash) end

--- Creates a ContentHash from the given GUID.
---
--- @param guid Guid
--- @return keen.ContentHash
function GuidHelper.to_content_hash(guid) end

--- Hashes the given GUID to produce a Hash32 (fnv1a32) value.
---
--- @param guid Guid
--- @return u32
function GuidHelper.hash(guid) end

--- Provides functions to compute various hash values.
---
--- @class Hasher
hasher = {}

--- Computes a 32-bit FNV-1a hash of the given value.
---
--- @param value string|Buffer
--- @return u32
function hasher.fnv1a32(value) end

--- Computes the CRC32/ISO-HDLC checksum of the given value.
---
--- @param value string|Buffer
--- @return u32
function hasher.crc32(value) end

--- Computes the CRC64/ECMA-182 checksum of the given value.
---
--- @param value string|Buffer
--- @return u64
function hasher.crc64(value) end

--- TODO: add documentation

--- @class integer
integer = {}

--- @class integer.u8
--- @field MIN u8
--- @field MAX u8
--- @field BITS u32
integer.u8 = {}

--- @param value string
--- @param radix? u32
--- @return u8|nil
function integer.u8.parse(value, radix) end

--- @param value integer|number
--- @return u8
function integer.u8.truncate(value) end

--- @param value integer|number
--- @return u8
function integer.u8.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.u8.is_valid(value) end

--- @param value u8
--- @return string
function integer.u8.to_string(value) end

--- @param value u8
--- @return u32
function integer.u8.count_ones(value) end

--- @param value u8
--- @return u32
function integer.u8.count_zeros(value) end

--- @param value u8
--- @return u32
function integer.u8.leading_zeros(value) end

--- @param value u8
--- @return u32
function integer.u8.trailing_zeros(value) end

--- @param value u8
--- @return u32
function integer.u8.leading_ones(value) end

--- @param value u8
--- @return u32
function integer.u8.trailing_ones(value) end

--- @param value u8
--- @param count u32
--- @return u8
function integer.u8.rotate_left(value, count) end

--- @param value u8
--- @param count u32
--- @return u8
function integer.u8.rotate_right(value, count) end

--- @param value u8
--- @return u8
function integer.u8.swap_bytes(value) end

--- @param value u8
--- @return u8
function integer.u8.reverse_bits(value) end

--- @param value u8
--- @return u8
function integer.u8.from_be(value) end

--- @param value u8
--- @return u8
function integer.u8.from_le(value) end

--- @param value u8
--- @return u8
function integer.u8.to_be(value) end

--- @param value u8
--- @return u8
function integer.u8.to_le(value) end

--- @param lhs u8
--- @param rhs u8
--- @return u8|nil
function integer.u8.checked_add(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8|nil
function integer.u8.checked_sub(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8|nil
function integer.u8.checked_mul(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8|nil
function integer.u8.checked_div(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8|nil
function integer.u8.checked_rem(lhs, rhs) end

--- @param value u8
--- @return u8|nil
function integer.u8.checked_neg(value) end

--- @param lhs u8
--- @param rhs u32
--- @return u8|nil
function integer.u8.checked_shl(lhs, rhs) end

--- @param lhs u8
--- @param rhs u32
--- @return u8|nil
function integer.u8.checked_shr(lhs, rhs) end

--- @param lhs u8
--- @param exp u32
--- @return u8|nil
function integer.u8.checked_pow(lhs, exp) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.saturating_add(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.saturating_sub(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.saturating_mul(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.saturating_div(lhs, rhs) end

--- @param lhs u8
--- @param exp u32
--- @return u8
function integer.u8.saturating_pow(lhs, exp) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.wrapping_add(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.wrapping_sub(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.wrapping_mul(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.wrapping_div(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.wrapping_rem(lhs, rhs) end

--- @param value u8
--- @return u8
function integer.u8.wrapping_neg(value) end

--- @param lhs u8
--- @param rhs u32
--- @return u8
function integer.u8.wrapping_shl(lhs, rhs) end

--- @param lhs u8
--- @param rhs u32
--- @return u8
function integer.u8.wrapping_shr(lhs, rhs) end

--- @param lhs u8
--- @param exp u32
--- @return u8
function integer.u8.wrapping_pow(lhs, exp) end

--- @param lhs u8
--- @param rhs u8
--- @return u8, bool
function integer.u8.overflowing_add(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8, bool
function integer.u8.overflowing_sub(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8, bool
function integer.u8.overflowing_mul(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8, bool
function integer.u8.overflowing_div(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8, bool
function integer.u8.overflowing_rem(lhs, rhs) end

--- @param value u8
--- @return u8, bool
function integer.u8.overflowing_neg(value) end

--- @param lhs u8
--- @param rhs u32
--- @return u8, bool
function integer.u8.overflowing_shl(lhs, rhs) end

--- @param lhs u8
--- @param rhs u32
--- @return u8, bool
function integer.u8.overflowing_shr(lhs, rhs) end

--- @param lhs u8
--- @param exp u32
--- @return u8, bool
function integer.u8.overflowing_pow(lhs, exp) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.add(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.sub(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.mul(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.div(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.rem(lhs, rhs) end

--- @param value u8
--- @return u8
function integer.u8.neg(value) end

--- @param lhs u8
--- @param rhs u32
--- @return u8
function integer.u8.shl(lhs, rhs) end

--- @param lhs u8
--- @param rhs u32
--- @return u8
function integer.u8.shr(lhs, rhs) end

--- @param lhs u8
--- @param exp u32
--- @return u8
function integer.u8.pow(lhs, exp) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.bit_and(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.bit_or(lhs, rhs) end

--- @param lhs u8
--- @param rhs u8
--- @return u8
function integer.u8.bit_xor(lhs, rhs) end

--- @param value u8
--- @return u8
function integer.u8.bit_not(value) end

--- @class integer.u16
--- @field MIN u16
--- @field MAX u16
--- @field BITS u32
integer.u16 = {}

--- @param value string
--- @param radix? u32
--- @return u16|nil
function integer.u16.parse(value, radix) end

--- @param value integer|number
--- @return u16
function integer.u16.truncate(value) end

--- @param value integer|number
--- @return u16
function integer.u16.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.u16.is_valid(value) end

--- @param value u16
--- @return string
function integer.u16.to_string(value) end

--- @param value u16
--- @return u32
function integer.u16.count_ones(value) end

--- @param value u16
--- @return u32
function integer.u16.count_zeros(value) end

--- @param value u16
--- @return u32
function integer.u16.leading_zeros(value) end

--- @param value u16
--- @return u32
function integer.u16.trailing_zeros(value) end

--- @param value u16
--- @return u32
function integer.u16.leading_ones(value) end

--- @param value u16
--- @return u32
function integer.u16.trailing_ones(value) end

--- @param value u16
--- @param count u32
--- @return u16
function integer.u16.rotate_left(value, count) end

--- @param value u16
--- @param count u32
--- @return u16
function integer.u16.rotate_right(value, count) end

--- @param value u16
--- @return u16
function integer.u16.swap_bytes(value) end

--- @param value u16
--- @return u16
function integer.u16.reverse_bits(value) end

--- @param value u16
--- @return u16
function integer.u16.from_be(value) end

--- @param value u16
--- @return u16
function integer.u16.from_le(value) end

--- @param value u16
--- @return u16
function integer.u16.to_be(value) end

--- @param value u16
--- @return u16
function integer.u16.to_le(value) end

--- @param lhs u16
--- @param rhs u16
--- @return u16|nil
function integer.u16.checked_add(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16|nil
function integer.u16.checked_sub(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16|nil
function integer.u16.checked_mul(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16|nil
function integer.u16.checked_div(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16|nil
function integer.u16.checked_rem(lhs, rhs) end

--- @param value u16
--- @return u16|nil
function integer.u16.checked_neg(value) end

--- @param lhs u16
--- @param rhs u32
--- @return u16|nil
function integer.u16.checked_shl(lhs, rhs) end

--- @param lhs u16
--- @param rhs u32
--- @return u16|nil
function integer.u16.checked_shr(lhs, rhs) end

--- @param lhs u16
--- @param exp u32
--- @return u16|nil
function integer.u16.checked_pow(lhs, exp) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.saturating_add(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.saturating_sub(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.saturating_mul(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.saturating_div(lhs, rhs) end

--- @param lhs u16
--- @param exp u32
--- @return u16
function integer.u16.saturating_pow(lhs, exp) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.wrapping_add(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.wrapping_sub(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.wrapping_mul(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.wrapping_div(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.wrapping_rem(lhs, rhs) end

--- @param value u16
--- @return u16
function integer.u16.wrapping_neg(value) end

--- @param lhs u16
--- @param rhs u32
--- @return u16
function integer.u16.wrapping_shl(lhs, rhs) end

--- @param lhs u16
--- @param rhs u32
--- @return u16
function integer.u16.wrapping_shr(lhs, rhs) end

--- @param lhs u16
--- @param exp u32
--- @return u16
function integer.u16.wrapping_pow(lhs, exp) end

--- @param lhs u16
--- @param rhs u16
--- @return u16, bool
function integer.u16.overflowing_add(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16, bool
function integer.u16.overflowing_sub(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16, bool
function integer.u16.overflowing_mul(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16, bool
function integer.u16.overflowing_div(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16, bool
function integer.u16.overflowing_rem(lhs, rhs) end

--- @param value u16
--- @return u16, bool
function integer.u16.overflowing_neg(value) end

--- @param lhs u16
--- @param rhs u32
--- @return u16, bool
function integer.u16.overflowing_shl(lhs, rhs) end

--- @param lhs u16
--- @param rhs u32
--- @return u16, bool
function integer.u16.overflowing_shr(lhs, rhs) end

--- @param lhs u16
--- @param exp u32
--- @return u16, bool
function integer.u16.overflowing_pow(lhs, exp) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.add(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.sub(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.mul(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.div(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.rem(lhs, rhs) end

--- @param value u16
--- @return u16
function integer.u16.neg(value) end

--- @param lhs u16
--- @param rhs u32
--- @return u16
function integer.u16.shl(lhs, rhs) end

--- @param lhs u16
--- @param rhs u32
--- @return u16
function integer.u16.shr(lhs, rhs) end

--- @param lhs u16
--- @param exp u32
--- @return u16
function integer.u16.pow(lhs, exp) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.bit_and(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.bit_or(lhs, rhs) end

--- @param lhs u16
--- @param rhs u16
--- @return u16
function integer.u16.bit_xor(lhs, rhs) end

--- @param value u16
--- @return u16
function integer.u16.bit_not(value) end

--- @class integer.u32
--- @field MIN u32
--- @field MAX u32
--- @field BITS u32
integer.u32 = {}

--- @param value string
--- @param radix? u32
--- @return u32|nil
function integer.u32.parse(value, radix) end

--- @param value integer|number
--- @return u32
function integer.u32.truncate(value) end

--- @param value integer|number
--- @return u32
function integer.u32.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.u32.is_valid(value) end

--- @param value u32
--- @return string
function integer.u32.to_string(value) end

--- @param value u32
--- @return u32
function integer.u32.count_ones(value) end

--- @param value u32
--- @return u32
function integer.u32.count_zeros(value) end

--- @param value u32
--- @return u32
function integer.u32.leading_zeros(value) end

--- @param value u32
--- @return u32
function integer.u32.trailing_zeros(value) end

--- @param value u32
--- @return u32
function integer.u32.leading_ones(value) end

--- @param value u32
--- @return u32
function integer.u32.trailing_ones(value) end

--- @param value u32
--- @param count u32
--- @return u32
function integer.u32.rotate_left(value, count) end

--- @param value u32
--- @param count u32
--- @return u32
function integer.u32.rotate_right(value, count) end

--- @param value u32
--- @return u32
function integer.u32.swap_bytes(value) end

--- @param value u32
--- @return u32
function integer.u32.reverse_bits(value) end

--- @param value u32
--- @return u32
function integer.u32.from_be(value) end

--- @param value u32
--- @return u32
function integer.u32.from_le(value) end

--- @param value u32
--- @return u32
function integer.u32.to_be(value) end

--- @param value u32
--- @return u32
function integer.u32.to_le(value) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_add(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_sub(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_mul(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_div(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_rem(lhs, rhs) end

--- @param value u32
--- @return u32|nil
function integer.u32.checked_neg(value) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_shl(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32|nil
function integer.u32.checked_shr(lhs, rhs) end

--- @param lhs u32
--- @param exp u32
--- @return u32|nil
function integer.u32.checked_pow(lhs, exp) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.saturating_add(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.saturating_sub(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.saturating_mul(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.saturating_div(lhs, rhs) end

--- @param lhs u32
--- @param exp u32
--- @return u32
function integer.u32.saturating_pow(lhs, exp) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_add(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_sub(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_mul(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_div(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_rem(lhs, rhs) end

--- @param value u32
--- @return u32
function integer.u32.wrapping_neg(value) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_shl(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.wrapping_shr(lhs, rhs) end

--- @param lhs u32
--- @param exp u32
--- @return u32
function integer.u32.wrapping_pow(lhs, exp) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_add(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_sub(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_mul(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_div(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_rem(lhs, rhs) end

--- @param value u32
--- @return u32, bool
function integer.u32.overflowing_neg(value) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_shl(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32, bool
function integer.u32.overflowing_shr(lhs, rhs) end

--- @param lhs u32
--- @param exp u32
--- @return u32, bool
function integer.u32.overflowing_pow(lhs, exp) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.add(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.sub(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.mul(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.div(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.rem(lhs, rhs) end

--- @param value u32
--- @return u32
function integer.u32.neg(value) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.shl(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.shr(lhs, rhs) end

--- @param lhs u32
--- @param exp u32
--- @return u32
function integer.u32.pow(lhs, exp) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.bit_and(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.bit_or(lhs, rhs) end

--- @param lhs u32
--- @param rhs u32
--- @return u32
function integer.u32.bit_xor(lhs, rhs) end

--- @param value u32
--- @return u32
function integer.u32.bit_not(value) end

--- @class integer.u64
--- @field MIN u64
--- @field MAX u64
--- @field BITS u32
integer.u64 = {}

--- @param value string
--- @param radix? u32
--- @return u64|nil
function integer.u64.parse(value, radix) end

--- @param value integer|number
--- @return u64
function integer.u64.truncate(value) end

--- @param value integer|number
--- @return u64
function integer.u64.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.u64.is_valid(value) end

--- @param value u64
--- @return string
function integer.u64.to_string(value) end

--- @param value u64
--- @return u32
function integer.u64.count_ones(value) end

--- @param value u64
--- @return u32
function integer.u64.count_zeros(value) end

--- @param value u64
--- @return u32
function integer.u64.leading_zeros(value) end

--- @param value u64
--- @return u32
function integer.u64.trailing_zeros(value) end

--- @param value u64
--- @return u32
function integer.u64.leading_ones(value) end

--- @param value u64
--- @return u32
function integer.u64.trailing_ones(value) end

--- @param value u64
--- @param count u32
--- @return u64
function integer.u64.rotate_left(value, count) end

--- @param value u64
--- @param count u32
--- @return u64
function integer.u64.rotate_right(value, count) end

--- @param value u64
--- @return u64
function integer.u64.swap_bytes(value) end

--- @param value u64
--- @return u64
function integer.u64.reverse_bits(value) end

--- @param value u64
--- @return u64
function integer.u64.from_be(value) end

--- @param value u64
--- @return u64
function integer.u64.from_le(value) end

--- @param value u64
--- @return u64
function integer.u64.to_be(value) end

--- @param value u64
--- @return u64
function integer.u64.to_le(value) end

--- @param lhs u64
--- @param rhs u64
--- @return u64|nil
function integer.u64.checked_add(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64|nil
function integer.u64.checked_sub(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64|nil
function integer.u64.checked_mul(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64|nil
function integer.u64.checked_div(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64|nil
function integer.u64.checked_rem(lhs, rhs) end

--- @param value u64
--- @return u64|nil
function integer.u64.checked_neg(value) end

--- @param lhs u64
--- @param rhs u32
--- @return u64|nil
function integer.u64.checked_shl(lhs, rhs) end

--- @param lhs u64
--- @param rhs u32
--- @return u64|nil
function integer.u64.checked_shr(lhs, rhs) end

--- @param lhs u64
--- @param exp u32
--- @return u64|nil
function integer.u64.checked_pow(lhs, exp) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.saturating_add(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.saturating_sub(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.saturating_mul(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.saturating_div(lhs, rhs) end

--- @param lhs u64
--- @param exp u32
--- @return u64
function integer.u64.saturating_pow(lhs, exp) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.wrapping_add(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.wrapping_sub(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.wrapping_mul(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.wrapping_div(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.wrapping_rem(lhs, rhs) end

--- @param value u64
--- @return u64
function integer.u64.wrapping_neg(value) end

--- @param lhs u64
--- @param rhs u32
--- @return u64
function integer.u64.wrapping_shl(lhs, rhs) end

--- @param lhs u64
--- @param rhs u32
--- @return u64
function integer.u64.wrapping_shr(lhs, rhs) end

--- @param lhs u64
--- @param exp u32
--- @return u64
function integer.u64.wrapping_pow(lhs, exp) end

--- @param lhs u64
--- @param rhs u64
--- @return u64, bool
function integer.u64.overflowing_add(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64, bool
function integer.u64.overflowing_sub(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64, bool
function integer.u64.overflowing_mul(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64, bool
function integer.u64.overflowing_div(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64, bool
function integer.u64.overflowing_rem(lhs, rhs) end

--- @param value u64
--- @return u64, bool
function integer.u64.overflowing_neg(value) end

--- @param lhs u64
--- @param rhs u32
--- @return u64, bool
function integer.u64.overflowing_shl(lhs, rhs) end

--- @param lhs u64
--- @param rhs u32
--- @return u64, bool
function integer.u64.overflowing_shr(lhs, rhs) end

--- @param lhs u64
--- @param exp u32
--- @return u64, bool
function integer.u64.overflowing_pow(lhs, exp) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.add(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.sub(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.mul(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.div(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.rem(lhs, rhs) end

--- @param value u64
--- @return u64
function integer.u64.neg(value) end

--- @param lhs u64
--- @param rhs u32
--- @return u64
function integer.u64.shl(lhs, rhs) end

--- @param lhs u64
--- @param rhs u32
--- @return u64
function integer.u64.shr(lhs, rhs) end

--- @param lhs u64
--- @param exp u32
--- @return u64
function integer.u64.pow(lhs, exp) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.bit_and(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.bit_or(lhs, rhs) end

--- @param lhs u64
--- @param rhs u64
--- @return u64
function integer.u64.bit_xor(lhs, rhs) end

--- @param value u64
--- @return u64
function integer.u64.bit_not(value) end

--- @class integer.i8
--- @field MIN i8
--- @field MAX i8
--- @field BITS u32
integer.i8 = {}

--- @param value string
--- @param radix? u32
--- @return i8|nil
function integer.i8.parse(value, radix) end

--- @param value integer|number
--- @return i8
function integer.i8.truncate(value) end

--- @param value integer|number
--- @return i8
function integer.i8.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.i8.is_valid(value) end

--- @param value i8
--- @return string
function integer.i8.to_string(value) end

--- @param value i8
--- @return u32
function integer.i8.count_ones(value) end

--- @param value i8
--- @return u32
function integer.i8.count_zeros(value) end

--- @param value i8
--- @return u32
function integer.i8.leading_zeros(value) end

--- @param value i8
--- @return u32
function integer.i8.trailing_zeros(value) end

--- @param value i8
--- @return u32
function integer.i8.leading_ones(value) end

--- @param value i8
--- @return u32
function integer.i8.trailing_ones(value) end

--- @param value i8
--- @param count u32
--- @return i8
function integer.i8.rotate_left(value, count) end

--- @param value i8
--- @param count u32
--- @return i8
function integer.i8.rotate_right(value, count) end

--- @param value i8
--- @return i8
function integer.i8.swap_bytes(value) end

--- @param value i8
--- @return i8
function integer.i8.reverse_bits(value) end

--- @param value i8
--- @return i8
function integer.i8.from_be(value) end

--- @param value i8
--- @return i8
function integer.i8.from_le(value) end

--- @param value i8
--- @return i8
function integer.i8.to_be(value) end

--- @param value i8
--- @return i8
function integer.i8.to_le(value) end

--- @param lhs i8
--- @param rhs i8
--- @return i8|nil
function integer.i8.checked_add(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8|nil
function integer.i8.checked_sub(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8|nil
function integer.i8.checked_mul(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8|nil
function integer.i8.checked_div(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8|nil
function integer.i8.checked_rem(lhs, rhs) end

--- @param value i8
--- @return i8|nil
function integer.i8.checked_neg(value) end

--- @param lhs i8
--- @param rhs u32
--- @return i8|nil
function integer.i8.checked_shl(lhs, rhs) end

--- @param lhs i8
--- @param rhs u32
--- @return i8|nil
function integer.i8.checked_shr(lhs, rhs) end

--- @param lhs i8
--- @param exp u32
--- @return i8|nil
function integer.i8.checked_pow(lhs, exp) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.saturating_add(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.saturating_sub(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.saturating_mul(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.saturating_div(lhs, rhs) end

--- @param lhs i8
--- @param exp u32
--- @return i8
function integer.i8.saturating_pow(lhs, exp) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.wrapping_add(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.wrapping_sub(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.wrapping_mul(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.wrapping_div(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.wrapping_rem(lhs, rhs) end

--- @param value i8
--- @return i8
function integer.i8.wrapping_neg(value) end

--- @param lhs i8
--- @param rhs u32
--- @return i8
function integer.i8.wrapping_shl(lhs, rhs) end

--- @param lhs i8
--- @param rhs u32
--- @return i8
function integer.i8.wrapping_shr(lhs, rhs) end

--- @param lhs i8
--- @param exp u32
--- @return i8
function integer.i8.wrapping_pow(lhs, exp) end

--- @param lhs i8
--- @param rhs i8
--- @return i8, bool
function integer.i8.overflowing_add(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8, bool
function integer.i8.overflowing_sub(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8, bool
function integer.i8.overflowing_mul(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8, bool
function integer.i8.overflowing_div(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8, bool
function integer.i8.overflowing_rem(lhs, rhs) end

--- @param value i8
--- @return i8, bool
function integer.i8.overflowing_neg(value) end

--- @param lhs i8
--- @param rhs u32
--- @return i8, bool
function integer.i8.overflowing_shl(lhs, rhs) end

--- @param lhs i8
--- @param rhs u32
--- @return i8, bool
function integer.i8.overflowing_shr(lhs, rhs) end

--- @param lhs i8
--- @param exp u32
--- @return i8, bool
function integer.i8.overflowing_pow(lhs, exp) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.add(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.sub(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.mul(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.div(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.rem(lhs, rhs) end

--- @param value i8
--- @return i8
function integer.i8.neg(value) end

--- @param lhs i8
--- @param rhs u32
--- @return i8
function integer.i8.shl(lhs, rhs) end

--- @param lhs i8
--- @param rhs u32
--- @return i8
function integer.i8.shr(lhs, rhs) end

--- @param lhs i8
--- @param exp u32
--- @return i8
function integer.i8.pow(lhs, exp) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.bit_and(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.bit_or(lhs, rhs) end

--- @param lhs i8
--- @param rhs i8
--- @return i8
function integer.i8.bit_xor(lhs, rhs) end

--- @param value i8
--- @return i8
function integer.i8.bit_not(value) end

--- @class integer.i16
--- @field MIN i16
--- @field MAX i16
--- @field BITS u32
integer.i16 = {}

--- @param value string
--- @param radix? u32
--- @return i16|nil
function integer.i16.parse(value, radix) end

--- @param value integer|number
--- @return i16
function integer.i16.truncate(value) end

--- @param value integer|number
--- @return i16
function integer.i16.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.i16.is_valid(value) end

--- @param value i16
--- @return string
function integer.i16.to_string(value) end

--- @param value i16
--- @return u32
function integer.i16.count_ones(value) end

--- @param value i16
--- @return u32
function integer.i16.count_zeros(value) end

--- @param value i16
--- @return u32
function integer.i16.leading_zeros(value) end

--- @param value i16
--- @return u32
function integer.i16.trailing_zeros(value) end

--- @param value i16
--- @return u32
function integer.i16.leading_ones(value) end

--- @param value i16
--- @return u32
function integer.i16.trailing_ones(value) end

--- @param value i16
--- @param count u32
--- @return i16
function integer.i16.rotate_left(value, count) end

--- @param value i16
--- @param count u32
--- @return i16
function integer.i16.rotate_right(value, count) end

--- @param value i16
--- @return i16
function integer.i16.swap_bytes(value) end

--- @param value i16
--- @return i16
function integer.i16.reverse_bits(value) end

--- @param value i16
--- @return i16
function integer.i16.from_be(value) end

--- @param value i16
--- @return i16
function integer.i16.from_le(value) end

--- @param value i16
--- @return i16
function integer.i16.to_be(value) end

--- @param value i16
--- @return i16
function integer.i16.to_le(value) end

--- @param lhs i16
--- @param rhs i16
--- @return i16|nil
function integer.i16.checked_add(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16|nil
function integer.i16.checked_sub(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16|nil
function integer.i16.checked_mul(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16|nil
function integer.i16.checked_div(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16|nil
function integer.i16.checked_rem(lhs, rhs) end

--- @param value i16
--- @return i16|nil
function integer.i16.checked_neg(value) end

--- @param lhs i16
--- @param rhs u32
--- @return i16|nil
function integer.i16.checked_shl(lhs, rhs) end

--- @param lhs i16
--- @param rhs u32
--- @return i16|nil
function integer.i16.checked_shr(lhs, rhs) end

--- @param lhs i16
--- @param exp u32
--- @return i16|nil
function integer.i16.checked_pow(lhs, exp) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.saturating_add(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.saturating_sub(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.saturating_mul(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.saturating_div(lhs, rhs) end

--- @param lhs i16
--- @param exp u32
--- @return i16
function integer.i16.saturating_pow(lhs, exp) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.wrapping_add(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.wrapping_sub(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.wrapping_mul(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.wrapping_div(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.wrapping_rem(lhs, rhs) end

--- @param value i16
--- @return i16
function integer.i16.wrapping_neg(value) end

--- @param lhs i16
--- @param rhs u32
--- @return i16
function integer.i16.wrapping_shl(lhs, rhs) end

--- @param lhs i16
--- @param rhs u32
--- @return i16
function integer.i16.wrapping_shr(lhs, rhs) end

--- @param lhs i16
--- @param exp u32
--- @return i16
function integer.i16.wrapping_pow(lhs, exp) end

--- @param lhs i16
--- @param rhs i16
--- @return i16, bool
function integer.i16.overflowing_add(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16, bool
function integer.i16.overflowing_sub(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16, bool
function integer.i16.overflowing_mul(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16, bool
function integer.i16.overflowing_div(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16, bool
function integer.i16.overflowing_rem(lhs, rhs) end

--- @param value i16
--- @return i16, bool
function integer.i16.overflowing_neg(value) end

--- @param lhs i16
--- @param rhs u32
--- @return i16, bool
function integer.i16.overflowing_shl(lhs, rhs) end

--- @param lhs i16
--- @param rhs u32
--- @return i16, bool
function integer.i16.overflowing_shr(lhs, rhs) end

--- @param lhs i16
--- @param exp u32
--- @return i16, bool
function integer.i16.overflowing_pow(lhs, exp) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.add(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.sub(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.mul(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.div(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.rem(lhs, rhs) end

--- @param value i16
--- @return i16
function integer.i16.neg(value) end

--- @param lhs i16
--- @param rhs u32
--- @return i16
function integer.i16.shl(lhs, rhs) end

--- @param lhs i16
--- @param rhs u32
--- @return i16
function integer.i16.shr(lhs, rhs) end

--- @param lhs i16
--- @param exp u32
--- @return i16
function integer.i16.pow(lhs, exp) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.bit_and(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.bit_or(lhs, rhs) end

--- @param lhs i16
--- @param rhs i16
--- @return i16
function integer.i16.bit_xor(lhs, rhs) end

--- @param value i16
--- @return i16
function integer.i16.bit_not(value) end

--- @class integer.i32
--- @field MIN i32
--- @field MAX i32
--- @field BITS u32
integer.i32 = {}

--- @param value string
--- @param radix? u32
--- @return i32|nil
function integer.i32.parse(value, radix) end

--- @param value integer|number
--- @return i32
function integer.i32.truncate(value) end

--- @param value integer|number
--- @return i32
function integer.i32.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.i32.is_valid(value) end

--- @param value i32
--- @return string
function integer.i32.to_string(value) end

--- @param value i32
--- @return u32
function integer.i32.count_ones(value) end

--- @param value i32
--- @return u32
function integer.i32.count_zeros(value) end

--- @param value i32
--- @return u32
function integer.i32.leading_zeros(value) end

--- @param value i32
--- @return u32
function integer.i32.trailing_zeros(value) end

--- @param value i32
--- @return u32
function integer.i32.leading_ones(value) end

--- @param value i32
--- @return u32
function integer.i32.trailing_ones(value) end

--- @param value i32
--- @param count u32
--- @return i32
function integer.i32.rotate_left(value, count) end

--- @param value i32
--- @param count u32
--- @return i32
function integer.i32.rotate_right(value, count) end

--- @param value i32
--- @return i32
function integer.i32.swap_bytes(value) end

--- @param value i32
--- @return i32
function integer.i32.reverse_bits(value) end

--- @param value i32
--- @return i32
function integer.i32.from_be(value) end

--- @param value i32
--- @return i32
function integer.i32.from_le(value) end

--- @param value i32
--- @return i32
function integer.i32.to_be(value) end

--- @param value i32
--- @return i32
function integer.i32.to_le(value) end

--- @param lhs i32
--- @param rhs i32
--- @return i32|nil
function integer.i32.checked_add(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32|nil
function integer.i32.checked_sub(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32|nil
function integer.i32.checked_mul(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32|nil
function integer.i32.checked_div(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32|nil
function integer.i32.checked_rem(lhs, rhs) end

--- @param value i32
--- @return i32|nil
function integer.i32.checked_neg(value) end

--- @param lhs i32
--- @param rhs u32
--- @return i32|nil
function integer.i32.checked_shl(lhs, rhs) end

--- @param lhs i32
--- @param rhs u32
--- @return i32|nil
function integer.i32.checked_shr(lhs, rhs) end

--- @param lhs i32
--- @param exp u32
--- @return i32|nil
function integer.i32.checked_pow(lhs, exp) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.saturating_add(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.saturating_sub(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.saturating_mul(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.saturating_div(lhs, rhs) end

--- @param lhs i32
--- @param exp u32
--- @return i32
function integer.i32.saturating_pow(lhs, exp) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.wrapping_add(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.wrapping_sub(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.wrapping_mul(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.wrapping_div(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.wrapping_rem(lhs, rhs) end

--- @param value i32
--- @return i32
function integer.i32.wrapping_neg(value) end

--- @param lhs i32
--- @param rhs u32
--- @return i32
function integer.i32.wrapping_shl(lhs, rhs) end

--- @param lhs i32
--- @param rhs u32
--- @return i32
function integer.i32.wrapping_shr(lhs, rhs) end

--- @param lhs i32
--- @param exp u32
--- @return i32
function integer.i32.wrapping_pow(lhs, exp) end

--- @param lhs i32
--- @param rhs i32
--- @return i32, bool
function integer.i32.overflowing_add(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32, bool
function integer.i32.overflowing_sub(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32, bool
function integer.i32.overflowing_mul(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32, bool
function integer.i32.overflowing_div(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32, bool
function integer.i32.overflowing_rem(lhs, rhs) end

--- @param value i32
--- @return i32, bool
function integer.i32.overflowing_neg(value) end

--- @param lhs i32
--- @param rhs u32
--- @return i32, bool
function integer.i32.overflowing_shl(lhs, rhs) end

--- @param lhs i32
--- @param rhs u32
--- @return i32, bool
function integer.i32.overflowing_shr(lhs, rhs) end

--- @param lhs i32
--- @param exp u32
--- @return i32, bool
function integer.i32.overflowing_pow(lhs, exp) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.add(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.sub(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.mul(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.div(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.rem(lhs, rhs) end

--- @param value i32
--- @return i32
function integer.i32.neg(value) end

--- @param lhs i32
--- @param rhs u32
--- @return i32
function integer.i32.shl(lhs, rhs) end

--- @param lhs i32
--- @param rhs u32
--- @return i32
function integer.i32.shr(lhs, rhs) end

--- @param lhs i32
--- @param exp u32
--- @return i32
function integer.i32.pow(lhs, exp) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.bit_and(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.bit_or(lhs, rhs) end

--- @param lhs i32
--- @param rhs i32
--- @return i32
function integer.i32.bit_xor(lhs, rhs) end

--- @param value i32
--- @return i32
function integer.i32.bit_not(value) end

--- @class integer.i64
--- @field MIN i64
--- @field MAX i64
--- @field BITS u32
integer.i64 = {}

--- @param value string
--- @param radix? u32
--- @return i64|nil
function integer.i64.parse(value, radix) end

--- @param value integer|number
--- @return i64
function integer.i64.truncate(value) end

--- @param value integer|number
--- @return i64
function integer.i64.clamp(value) end

--- @param value integer|number
--- @return bool
function integer.i64.is_valid(value) end

--- @param value i64
--- @return string
function integer.i64.to_string(value) end

--- @param value i64
--- @return u32
function integer.i64.count_ones(value) end

--- @param value i64
--- @return u32
function integer.i64.count_zeros(value) end

--- @param value i64
--- @return u32
function integer.i64.leading_zeros(value) end

--- @param value i64
--- @return u32
function integer.i64.trailing_zeros(value) end

--- @param value i64
--- @return u32
function integer.i64.leading_ones(value) end

--- @param value i64
--- @return u32
function integer.i64.trailing_ones(value) end

--- @param value i64
--- @param count u32
--- @return i64
function integer.i64.rotate_left(value, count) end

--- @param value i64
--- @param count u32
--- @return i64
function integer.i64.rotate_right(value, count) end

--- @param value i64
--- @return i64
function integer.i64.swap_bytes(value) end

--- @param value i64
--- @return i64
function integer.i64.reverse_bits(value) end

--- @param value i64
--- @return i64
function integer.i64.from_be(value) end

--- @param value i64
--- @return i64
function integer.i64.from_le(value) end

--- @param value i64
--- @return i64
function integer.i64.to_be(value) end

--- @param value i64
--- @return i64
function integer.i64.to_le(value) end

--- @param lhs i64
--- @param rhs i64
--- @return i64|nil
function integer.i64.checked_add(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64|nil
function integer.i64.checked_sub(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64|nil
function integer.i64.checked_mul(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64|nil
function integer.i64.checked_div(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64|nil
function integer.i64.checked_rem(lhs, rhs) end

--- @param value i64
--- @return i64|nil
function integer.i64.checked_neg(value) end

--- @param lhs i64
--- @param rhs u32
--- @return i64|nil
function integer.i64.checked_shl(lhs, rhs) end

--- @param lhs i64
--- @param rhs u32
--- @return i64|nil
function integer.i64.checked_shr(lhs, rhs) end

--- @param lhs i64
--- @param exp u32
--- @return i64|nil
function integer.i64.checked_pow(lhs, exp) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.saturating_add(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.saturating_sub(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.saturating_mul(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.saturating_div(lhs, rhs) end

--- @param lhs i64
--- @param exp u32
--- @return i64
function integer.i64.saturating_pow(lhs, exp) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.wrapping_add(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.wrapping_sub(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.wrapping_mul(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.wrapping_div(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.wrapping_rem(lhs, rhs) end

--- @param value i64
--- @return i64
function integer.i64.wrapping_neg(value) end

--- @param lhs i64
--- @param rhs u32
--- @return i64
function integer.i64.wrapping_shl(lhs, rhs) end

--- @param lhs i64
--- @param rhs u32
--- @return i64
function integer.i64.wrapping_shr(lhs, rhs) end

--- @param lhs i64
--- @param exp u32
--- @return i64
function integer.i64.wrapping_pow(lhs, exp) end

--- @param lhs i64
--- @param rhs i64
--- @return i64, bool
function integer.i64.overflowing_add(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64, bool
function integer.i64.overflowing_sub(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64, bool
function integer.i64.overflowing_mul(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64, bool
function integer.i64.overflowing_div(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64, bool
function integer.i64.overflowing_rem(lhs, rhs) end

--- @param value i64
--- @return i64, bool
function integer.i64.overflowing_neg(value) end

--- @param lhs i64
--- @param rhs u32
--- @return i64, bool
function integer.i64.overflowing_shl(lhs, rhs) end

--- @param lhs i64
--- @param rhs u32
--- @return i64, bool
function integer.i64.overflowing_shr(lhs, rhs) end

--- @param lhs i64
--- @param exp u32
--- @return i64, bool
function integer.i64.overflowing_pow(lhs, exp) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.add(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.sub(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.mul(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.div(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.rem(lhs, rhs) end

--- @param value i64
--- @return i64
function integer.i64.neg(value) end

--- @param lhs i64
--- @param rhs u32
--- @return i64
function integer.i64.shl(lhs, rhs) end

--- @param lhs i64
--- @param rhs u32
--- @return i64
function integer.i64.shr(lhs, rhs) end

--- @param lhs i64
--- @param exp u32
--- @return i64
function integer.i64.pow(lhs, exp) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.bit_and(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.bit_or(lhs, rhs) end

--- @param lhs i64
--- @param rhs i64
--- @return i64
function integer.i64.bit_xor(lhs, rhs) end

--- @param value i64
--- @return i64
function integer.i64.bit_not(value) end

--- @class IO
io = {}

--- Provides the contents of a file as a `Buffer`.
---
--- # Errors
--- - If the file does not exist or cannot be read.
---
--- # Example
--- ```lua
--- local buffer = io.read("path/to/file.txt")
---
--- -- Outputs the content of the file as a string.
--- print(buffer:to_string())
--- ```
---
--- @param path string
--- @return Buffer
function io.read(path) end

--- Reads the entire content of a file and returns it as a string.
---
--- This is a convenience function that combines `io.read` and `Buffer:to_string()`.
---
--- # Errors
--- - If the file does not exist or cannot be read.
---
--- # Example
--- ```lua
--- local content = io.read_to_string("path/to/file.txt")
---
--- print(content)
--- ```
---
--- @param path string
--- @return string
function io.read_to_string(path) end

--- Returns an array of paths within the specified directory.
---
--- # Errors
--- - If the directory does not exist or cannot be read.
---
--- # Example
--- ```lua
--- local files = io.list_files("path/to/directory")
---
--- for _, file in ipairs(files) do
---     print(file.name)
--- end
--- ```
---
--- @param path string
--- @return string[]
function io.list_files(path) end

--- Returns `true` if the file or directory at the given path exists.
---
--- If an error occurs while checking (e.g., due to permission issues), it will return `false`.
---
--- # Example
--- ```lua
--- if io.file_exists("path/to/file.txt") then
---     print("File exists!")
--- end
--- ```
---
--- @param path string
--- @return boolean
function io.exists(path) end

--- Returns `true` if the path is a file.
---
--- If an error occurs while checking (e.g., due to permission issues), it will return `false`.
---
--- # Example
--- ```lua
--- if io.is_file("path/to/file.txt") then
---     print("It's a file!")
--- end
--- ```
---
--- @param path string
--- @return boolean
function io.is_file(path) end

--- Returns `true` if the path is a directory.
---
--- If an error occurs while checking (e.g., due to permission issues), it will return `false`.
---
--- # Example
--- ```lua
--- if io.is_directory("path/to/directory") then
---     print("It's a directory!")
--- end
--- ```
---
--- @param path string
--- @return boolean
function io.is_directory(path) end

--- Returns the name (including the extension) from a given path.
---
--- If the path is a file, it returns the file name.
--- If the path is a directory, it returns the directory name.
---
--- Returns an empty string if the path terminates in `..`.
---
--- # Example
--- ```lua
--- local file_name = io.name("path/to/file.txt")
---
--- assert(file_name == "file.txt")
--- ```
---
--- @param path string
--- @return string
function io.name(path) end

--- Returns the name of the file without its extension.
---
--- If the path has no name, it returns an empty string.
---
--- # Example
--- ```lua
--- local name_without_ext = io.name_without_extension("path/to/file.txt")
---
--- assert(name_without_ext == "file")
--- ```
---
--- @param path string
--- @return string
function io.name_without_extension(path) end

--- Returns the extension (without the dot) of the file name.
---
--- If the path has no name or no extension, it returns an empty string.
---
--- # Example
--- ```lua
--- local ext = io.extension("path/to/file.txt")
---
--- assert(ext == "txt")
--- ```
---
--- @param path string
--- @return string
function io.extension(path) end

--- Returns the parent directory of the given path.
---
--- If the path has no parent (e.g., it's a root directory), it returns `nil`.
---
--- # Example
--- ```lua
--- local parent_dir = io.parent_directory("path/to/file.txt")
---
--- assert(parent_dir == "path/to")
--- ```
---
--- @param path string
--- @return string|nil
function io.parent(path) end

--- Joins multiple path segments into a single path.
---
--- # Example
--- ```lua
--- local full_path = io.join("path", "to", "file.txt")
---
--- assert(full_path == "path/to/file.txt")
--- ```
---
--- @param ... string
--- @return string
--- @nodiscard
function io.join(...) end

--- Writes the contents of a string or `Buffer` to a file at the specified path relative to the configured export directory.
---
--- [loader.features.export](lua://loader.features.export) must be enabled for this function to work, otherwise it will throw an error.
---
--- # Behavior
--- If the file already exists, it will be overwritten.
--- If the file does not exist, it will be created along with any necessary parent directories.
---
--- # Errors
--- - If the [loader.features.export](lua://loader.features.export) feature is not enabled.
--- - If the file cannot be written (e.g., due to permission issues).
--- - If the path points to a directory.
--- - If the path points outside the configured export directory.
---
--- # Example
--- ```lua
--- -- Exports "Hello, World!" to "<export-dir>/greetings/hello.txt"
--- io.export("greetings/hello.txt", "Hello, World!")
--- ```
---
--- @param path string
--- @param bytes string|Buffer
--- @return Buffer
function io.export(path, bytes) end

--- Provides information about the current mod loader environment.
---
--- @class Loader
--- @field is_client boolean -- Whether the current environment is the client.
--- @field is_server boolean -- Whether the current environment is the server.
--- @field features LoaderFeatures -- The features available in the current environment.
--- @field runtime LoaderRuntime -- Manages everything related to the runtime environment.
loader = {}

--- @class LoaderFeatures
---
--- Whether the patching feature is available.
--- When this is `true`, changes to game data will be applied to the game files.
--- @field patch boolean
---
--- Whether the import feature is available.
--- When this is `true`, mods can use `io.export` to export arbitrary data.
--- @field export boolean
---
--- All runtime-related features.
--- When this is `nil`, no runtime features are available.
--- @field runtime RuntimeFeatures?

--- @class RuntimeFeatures
---
--- When this is `true`, mods can use `loader.runtime.register_dll` to register dll files to be loaded by the mod loader when the game starts.
--- @field dll boolean

--- Returns true if the given mod is loaded.
---
--- @param mod_id string -- The id of the mod to check.
--- @return boolean -- True if the mod is loaded, false otherwise.
function loader.has_mod(mod_id) end

--- Manages everything related to the runtime environment.
---
--- @class LoaderRuntime
local runtime = {}

--- NOTE: This function is currently not implemented and won't do anything.
---
--- Registers a dll file to be loaded by the mod loader when the game starts.
---
--- [loader.features.runtime.dll](lua://loader.features.runtime)
--- must be enabled for this function to work, otherwise it will throw an error.
---
--- # Errors
--- - If the file does not exist or cannot be read.
---
--- @param path string -- The path to the dll file to load, relative to the mod's root directory.
function runtime.register_dll(path) end

--- TODO: add documentation
--- TODO: implement `Type::flags`
--- TODO: implement `Type::default_value`

---@class TypeRegistry
local TypeRegistry = {}

--- @param qualified_hash u32
--- @return Type
function TypeRegistry.get(qualified_hash) end

--- @param qualified_name string
--- @return Type
function TypeRegistry.get(qualified_name) end

--- @param qualified_hash u32
--- @return Type
function TypeRegistry.get_by_qualified_hash(qualified_hash) end

--- @param impact_hash u32
--- @return Type
function TypeRegistry.get_by_impact_hash(impact_hash) end

--- @param qualified_name string
--- @return Type
function TypeRegistry.get_by_qualified_name(qualified_name) end

--- @param impact_name string
--- @return Type
function TypeRegistry.get_by_impact_name(impact_name) end

--- @return Type[]
function TypeRegistry.get_all() end

--- @param value any
--- @return Type
function TypeRegistry.of(value) end

--- @class Type
---
--- @field name string
--- @field impact_name string
--- @field qualified_name string
---
--- @field name_hash u32
--- @field impact_hash u32
--- @field qualified_hash u32
--- @field internal_hash u32
---
--- @field namespace string[]
--- @field inner_type Type?
--- @field size u32
--- @field alignment u32
--- @field element_alignment u32
--- @field field_count u32
--- @field primitive_type PrimitiveType
--- @field flags TypeFlag[]
---
--- @field struct_fields table<string, StructField>
--- @field enum_fields table<string, EnumField>
--- @field attributes table<string, Attribute>
---
--- @field default_value unknown -- TODO: This needs a custom implementation and must be an ObjectValue
local Type = {}

--- @class StructField
--- @field name string
--- @field type Type
--- @field data_offset u32
--- @field attributes table<string, Attribute>

--- @class EnumField
--- @field name string
--- @field value u64

--- @class Attribute
--- @field name string
--- @field namespace string[]
--- @field type Type?
--- @field value string

---@alias PrimitiveType
---| "None"
---| "Bool"
---| "UInt8"
---| "SInt8"
---| "UInt16"
---| "SInt16"
---| "UInt32"
---| "SInt32"
---| "UInt64"
---| "SInt64"
---| "Float32"
---| "Float64"
---| "Enum"
---| "Bitmask8"
---| "Bitmask16"
---| "Bitmask32"
---| "Bitmask64"
---| "Typedef"
---| "Struct"
---| "StaticArray"
---| "DsArray"
---| "DsString"
---| "DsOptional"
---| "DsVariant"
---| "BlobArray"
---| "BlobString"
---| "BlobOptional"
---| "BlobVariant"
---| "ObjectReference"
---| "Guid"

---@alias TypeFlag
---| "None"
---| "IsDs"
---| "HasBlobArray"
---| "HasBlobString"
---| "HasBlobOptional"
---| "HasBlobVariant"
---| "IsGpuUniform"
---| "IsGpuStorage"
---| "IsGpuConstant"
