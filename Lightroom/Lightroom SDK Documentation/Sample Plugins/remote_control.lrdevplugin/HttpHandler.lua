--[[----------------------------------------------------------------------------

HttpHandler.lua

--------------------------------------------------------------------------------

ADOBE CONFIDENTIAL
------------------
Copyright 2013 Adobe Systems Incorporated
All Rights Reserved.

NOTICE: All information contained herein is, and remain the property of
Adobe Systems Incorporated and its suppliers, if any. The intellectual and
technical concepts contained herein are proprietary to Adobe Systems
Incorporated and its suppliers and may be covered by U.S. and Foreign
Patents, patents in process, and are protected by trade secret or copyright
law.  Dissemination of this information or reproduction of this material is
strictly forbidden unless prior written permission is obtained from
Adobe Systems Incorporated.

----------------------------------------------------------------------------]]--

local LrApplication = import "LrApplication"
local LrController = import "LrController"
local LrFileUtils = import "LrFileUtils"
local LrPathUtils = import "LrPathUtils"
local AgURI
local prefs = import "LrPrefs".prefsForPlugin()

--------------------------------------------------------------------------------

local function initIfNil( key, default )
	if prefs[ key ] == nil then
		prefs[ key ] = default
	end
end

initIfNil( "allowViewPhotos", true )
initIfNil( "allowSwitchPhotos", false )
initIfNil( "allowSwitchViewModes", false )
initIfNil( "allowTriggerCapture", false )
initIfNil( "allowEditKeywords", false )
initIfNil( "allowControlSlideshow", false )
initIfNil( "showHeader", true )

--==============================================================================

-- folder inside the plugin directory that contains the web content

local contentDir = "webroot"

--------------------------------------------------------------------------------

local function ParseCSVLine( line,sep )
	local res = {}
	local pos = 1
	sep = sep or ','
	while true do
		local c = string.sub(line,pos,pos)
		if (c == "") then break end
		if (c == '"') then
			-- quoted value (ignore separator within)
			local txt = ""
			repeat
				local startp,endp = string.find(line,'^%b""',pos)
				txt = txt..string.sub(line,startp+1,endp-1)
				pos = endp + 1
				c = string.sub(line,pos,pos)
				if (c == '"') then txt = txt..'"' end
				-- check first char AFTER quoted string, if it is another
				-- quoted string without separator, then append it
				-- this is the way to "escape" the quote char in a quote. example:
				--   value1,"blub""blip""boing",value3  will result in blub"blip"boing  for the middle
			until (c ~= '"')
			table.insert(res,txt)
			assert(c == sep or c == "")
			pos = pos + 1
		else
			-- no quotes used, just look for the first separator
			local startp,endp = string.find(line,sep,pos)
			if (startp) then
				table.insert(res,string.sub(line,pos,startp-1))
				pos = endp + 1
			else
				-- no separator found -> use rest of string and terminate
				table.insert(res,string.sub(line,pos))
				break
			end
		end
	end
	return res
end

--------------------------------------------------------------------------------

-- handlers for "command=" parameters

local kCommands = {
	nextPhoto = { perform = LrController.nextPhoto, pref = "allowSwitchPhotos" },
	previousPhoto = { perform = LrController.previousPhoto, pref = "allowSwitchPhotos" },
	loupeView = { perform = LrController.showLoupe, pref = "allowSwitchViewModes" },
	gridView = { perform = LrController.showGrid, pref = "allowSwitchViewModes" },
	triggerCapture = { perform = LrController.triggerCapture, pref = "allowTriggerCapture" },
	startSlideshow = { perform = LrController.startSlideshow, pref = "allowControlSlideshow" },
	stopSlideshow = { perform = LrController.stopSlideshow, pref = "allowStopSlideshow" },

	addKeywords = {
		perform = function( queryString )
			local _, _, keywordString = string.find( queryString, "keywords=([%w, %%]+)" )
			keywordString = AgURI.unescape( keywordString )
			local catalog = LrApplication.activeCatalog()
			local photo = catalog:getTargetPhoto()

			if keywordString and keywordString ~= "" then
				local keywords = ParseCSVLine( keywordString )
				if #keywords > 0 then
					catalog:withWriteAccessDo( "CreateKeyword", function()
						for _, keyword in ipairs( keywords ) do
							local kw = catalog:createKeyword( keyword, nil, nil, nil, true )
							if kw then
								photo:addKeyword( kw )
							end
						end
					
						if #keywords > 1 then
							LrController.showBezel( string.format( "Add Keywords: %s", keywordString ) )
						else
							LrController.showBezel( string.format( "Add Keyword: %s", keywordString ) )
						end
					end )
				end
			end
		end,
		pref = "allowEditKeywords",
	},

	removeKeywords = {
		perform = function( queryString )
			local _, _, keywordString = string.find( queryString, "keywords=([%w, ]+)" )
			keywordString = AgURI.unescape( keywordString )
			local catalog = LrApplication.activeCatalog()
			local photo = catalog:getTargetPhoto()
			if keywordString and keywordString ~= "" then
				local keywordsToRemove = ParseCSVLine( keywordString )
				if #keywordsToRemove > 0 then
					catalog:withWriteAccessDo( "RemoveKeywords", function()
						for _, kw in ipairs( keywordsToRemove ) do
							keywordsToRemove[ kw ] = true
						end
						local existingKeywords = photo:getRawMetadata( "keywords" )
						for _, kw in ipairs( existingKeywords ) do
							if keywordsToRemove[ kw:getName() ] then
								photo:removeKeyword( kw )
							end
						end
					
						if #keywordsToRemove > 1 then
							LrController.showBezel( string.format( "Remove Keywords: %s", keywordString ) )
						else
							LrController.showBezel( string.format( "Remove Keyword: %s", keywordString ) )
						end
					end )
				end
			end
		end,
		pref = "allowEditKeywords",
	},
}

--==============================================================================

-- The SDK doesn't appear to contain a URI parser, so copy this from AgURI.

local function _parseURI( base )
	
	local _, _, a, b =  string.find( base, "^(([^:/?#]+):)" )
	if a then base = string.sub( base, string.len( a )+1 ) end

	local _, _, c, d =  string.find( base, "^(//([^/?#]*))" )
	if c then base = string.sub( base, string.len( c )+1 ) end

	local _, _, e=  string.find( base, "^([^?#]*)" )
	if e then base = string.sub( base, string.len( e )+1 ) end

	local _, _, f, g =  string.find( base, "^(\?([^#]*))" )
	if f then base = string.sub( base, string.len( f )+1 ) end

	local _, _, h, i =  string.find( base, "^(#(.*))" )
	if h then base = string.sub( base, string.len( h )+1 ) end

	return a, b, c, d, e, f, g, h, i
end

--------------------------------------------------------------------------------

AgURI = {

	unescape = function( s )
		if not s then return s end
	    return string.gsub(s, "%%(%x%x)", function( hex )
			return string.char( tonumber( hex, 16 ) )
	    end )
	end,

	parse = function( uristr )
		local _, bscheme, _, bauthority, bpath, _, bquery, _, bfragment = _parseURI( uristr )
		
		-- fix + type of URI encoding
		local decodedpath = string.gsub( bpath, '+', ' ' )
		-- fix %20 type of URI encoding
		decodedpath = string.gsub( decodedpath, '%%(%x%x)', function( hex ) return string.char( tonumber( hex, 16 ) ) end )

		return {
			scheme = bscheme,
			authority = bauthority,
			path = decodedpath,
			rawPath = bpath,
			query = bquery,
			uri = uristr,
			fragment = bfragment
		}
	end,
}

--==============================================================================

-- evaluates a Lua server page to produce HTML

local function evalLsp( lsp, request, response )

	lsp = string.gsub( lsp, "%%{(.-)}", "]] ) out( %1 ) out( [[" ) -- %{variable}
	lsp = string.gsub( lsp, "<%%=(.-)%%>", "]] ) out( %1 ) out( [[" ) -- <%= variable %>
	lsp = string.gsub( lsp, "<%%(.-)%%>", "]] ) %1 out( [[" ) -- <% (Lua code) %>

	lsp = string.format( [===[
		local out = _G.out
		local result = _G.result
		out( [[ %s ]] )
		return table.concat( result ) ]===], lsp )

	local f, err = loadstring( lsp )

	if not f then
		err = "parse error: " .. err
		return err
	else
		_G.result = {}

		_G.response = {
			write = function( str )
				table.insert( _G.result, str )
			end,
		}

		_G.out = function( v )
			table.insert( _G.result, tostring( v ) )
		end

		local success, html = pcall( f )

		if not success then
			local runError = "execution error: " .. tostring( html )
			return runError
		end
		
		return tostring( html )
	end
end

--------------------------------------------------------------------------------

local commonMimeTypes = {
	pdf = "application/pdf",
	sig = "application/pgp-signature",
	spl = "application/futuresplash",
	class = "application/octet-stream",
	ps = "application/postscript",
	torrent = "application/x-bittorrent",
	dvi = "application/x-dvi",
	gz = "application/x-gzip",
	pac = "application/x-ns-proxy-autoconfig",
	swf = "application/x-shockwave-flash",
	[ 'tar.gz' ] = "application/x-tgz",
	tgz = "application/x-tgz",
	tar = "application/x-tar",
	zip = "application/zip",
	mp3 = "audio/mpeg",
	m3u = "audio/x-mpegurl",
	wma = "audio/x-ms-wma",
	wax = "audio/x-ms-wax",
	ogg = "audio/x-wav",
	wav = "audio/x-wav",
	gif = "image/gif",
	jpg = "image/jpeg",
	jpeg = "image/jpeg",
	png = "image/png",
	xbm = "image/x-xbitmap",
	xpm = "image/x-xpixmap",
	xwd = "image/x-xwindowdump",
	css = "text/css",
	asp = "text/html",
	php = "text/html",
	jsp = "text/html",
	html = "text/html",
	htm = "text/html",
	js = "text/javascript",
	asc = "text/plain",
	c = "text/plain",
	conf = "text/plain",
	text = "text/plain",
	txt = "text/plain",
	dtd = "text/xml",
	xml = "text/xml",
	mpeg = "video/mpeg",
	mpg = "video/mpeg",
	mov = "video/quicktime",
	qt = "video/quicktime",
	avi = "video/x-msvideo",
	asf = "video/x-ms-asf",
	asx = "video/x-ms-asf",
	wmv = "video/x-ms-wmv",
}

--------------------------------------------------------------------------------

local function mimeTypeFromExtension( ext )
	return ext and commonMimeTypes[ ext ] or nil
end

--------------------------------------------------------------------------------

-- holds references to thumbnail requests until they are completed
local _pendingThumbnailRequests = {}

--------------------------------------------------------------------------------

local function sendThumbnail( imageId, width, height, response )

	local catalog = LrApplication.activeCatalog()
	local photo = catalog:getPhotoByLocalId( tonumber( imageId ) )

	local request
	request = photo:requestJpegThumbnail( width, height, function( pixels, errMsg )
		if pixels then
			response.data = pixels
			response.headers = {
				{ name = 'Content-Type', value = "image/jpeg" },
				{ name = 'Content-Length', value = tostring( string.len( pixels ) ), }
			}
		else
			response.data = "error loading thumb"
		end
		response:transmit()
		if request then
			_pendingThumbnailRequests[ request ] = nil
		end
	end )
	
	if request then
		_pendingThumbnailRequests[ request ] = true
	end
end

--------------------------------------------------------------------------------

local function sendString( response, str, contentType )
	str = str or ""
	response.data = str
	response.headers = {
		{ name = 'Content-Type', value = contentType or "text/html" },
		{ name = 'Content-Length', value = #str, }
	}
	response:transmit()
end

--------------------------------------------------------------------------------

local function isChildFolder( parentPath, childPath )
	parentPath = string.lower( parentPath )
	childPath = string.lower( childPath )
	
	while childPath do
		if parentPath == childPath then
			return true
		end
		childPath = LrPathUtils.parent( childPath )
	end
	
	return false
end

--------------------------------------------------------------------------------

local function sendFile( response, path, request, plugin )

	if not path then
		sendString( response, "no path given" )
		return
	end

	local baseDir = LrPathUtils.child( plugin.path, contentDir )
	--path = LrPathUtils.makeAbsolute( path, baseDir )
	path = LrPathUtils.child( baseDir, path )
	
	if not isChildFolder( baseDir, path ) then
		sendString( response, "invalid path" )
		return
	end

	local f = io.open( path, "rb" )

	if f then
    
	    local data = f:read( "*all" )
	    f:close()

	    local fileInfo = LrFileUtils.fileAttributes( path )
	    local length = fileInfo.fileSize
	    local extension = LrPathUtils.extension( path )

		if string.lower( extension ) == "lsp" then
			data = evalLsp( data, request, response )
			length = #data
		end

	    response.data = data
	    response.headers = {
			{ name = 'Content-Type', value = mimeTypeFromExtension( extension ) },
			{ name = 'Content-Length', value = tostring( length ), }
		}
		response:transmit()
	else
		sendString( response, string.format( "file not found: %s", path ) )
	end
end

--------------------------------------------------------------------------------

local function mapUriToPath( uri )

	if not uri or uri == "" or uri == "/" then
		return "index.lsp"
	end

	-- others?

	return uri
end

--------------------------------------------------------------------------------

local function runCommand( commandName, queryString )

	local command = kCommands[ commandName ]
	
	if command and prefs[ command.pref ] then
		command.perform( queryString )
		return true, "OK"
	end
	
	return true, string.format( "unknown command: %s", commandName )
end

--------------------------------------------------------------------------------

local function sendKeywords( response )

	local catalog = LrApplication.activeCatalog()
	local photo = catalog:getTargetPhoto()

	catalog:withReadAccessDo( function()
		local keywords = photo:getRawMetadata( "keywords" )
		local names = {}
		for _, keyword in ipairs( keywords or {} ) do
			table.insert( names, keyword:getName()	)
		end
		keywords = table.concat( names, "," )
		sendString( response, keywords )
	end )
end

--------------------------------------------------------------------------------

local function handleGET( request, response, plugin )

	local uri = request.uri
	local uriParts = AgURI.parse( uri )
	local query = uriParts.query or request.query_string or ""
	local path = mapUriToPath( uri )

	-- messy, should generalize this
	local _, _, commandName = string.find( query, "command=(%w+)" )
	local getThumbnail = string.find( query, "command=getThumbnail" )
	local getCurrentPhotoId = string.find( query, "command=getCurrentPhotoId" )
	local getKeywords = string.find( query, "command=getKeywords" )
	local _, _, imageId = string.find( query, "imageId=(%d+)" )
	local _, _, width = string.find( query, "width=(%d+)" )
	local _, _, height = string.find( query, "height=(%d+)" )
		
	if getThumbnail and imageId then
		sendThumbnail( imageId, width, height, response )
		return
	elseif getKeywords then
		sendKeywords( response )
		return
	elseif getCurrentPhotoId then
		local catalog = LrApplication.activeCatalog()
		local photo = catalog:getTargetPhoto()
		if photo then
			local localId = photo.localIdentifier
			if localId then
				sendString( response, tostring( localId ) )
				return
			end
		end
		sendString( response, "" )
	elseif commandName then
		runCommand( commandName, query )
		-- redirect back to the index page after running commands
		path = mapUriToPath( "/" )
	end

	sendFile( response, path, request, plugin )
end

--------------------------------------------------------------------------------

local function handlePOST( request, response, plugin )

	local parts = {}

	if request.query_string and request.query_string ~= "" then
		table.insert( parts, request.query_string )
	end
	
	if request.content and request.content ~= "" then
		table.insert( parts, request.content )
	end
	
	request.query_string = table.concat( parts, "&" )
	
	handleGET( request, response, plugin )
end

--==============================================================================

return {
	GET = handleGET,
	POST = handlePOST,
}

