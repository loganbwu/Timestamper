--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2014 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

------------------------------------------------------------------------------]]

local LrDialogs = import "LrDialogs"
local LrFunctionContext = import "LrFunctionContext"
local LrTasks = import "LrTasks"

local LrApplication = import "LrApplication"
local LrSelection = import "LrSelection"
local LrDevelopController = import "LrDevelopController"
local LrSocket = import "LrSocket"
local LrTableUtils = import "LrTableUtils"

--==============================================================================
-- All of the Develop parameters that we will monitor for changes.

local develop_params = {
	"Temperature",
	"Tint",
	"Exposure",
	"Contrast",
	"Highlights",
	"Shadows",
	"Whites",
	"Blacks",
	"Clarity",
	"Vibrance",
	"Saturation",
}

local develop_param_set = {}

for _, key in ipairs( develop_params ) do
	develop_param_set[ key ] = true
end

--------------------------------------------------------------------------------
-- Checks to see if observer[ key ] is equal to the given value.  If the value has
-- changed, reports the change to the given sender.
-- Used to notify external processes when settings change in Lr.

local function updateValue( observer, sender, key, value )

	if observer[ key ] ~= value then

		-- for table types, check if any values have changed
		if type( value ) == "table" and type( observer[ key ] ) == "table" then
			local different = false
			for k, v in pairs( value ) do
				if observer[ key ][ k ] ~= v then
					different = true
					break
				end
			end
			for k, v in pairs( observer[ key ] ) do
				if value[ k ]  ~= v then
					different = true
					break
				end
			end
			if not different then
				return
			end
		end

		observer[ key ] = value
	
		local data = LrTableUtils.tableToString {
			key = key,
			value = value,
		}
		
		if WIN_ENV then
			data = string.gsub( data, "\n", "\r\n" )
		end
	
		sender:send( data )
	end
end

--------------------------------------------------------------------------------
-- Calls the appropriate API to adjust a setting in Lr.

local function setValue( key, value )

	if value == "+" then
		LrDevelopController.increment( key )
		return
	end

	if value == "-" then
		LrDevelopController.decrement( key )
		return
	end
	
	if value == "reset" then
		LrDevelopController.resetToDefault( key )
		return
	end

	local numberValue = tonumber( value )
	
	if key == "rating" and numberValue then

		LrSelection.setRating( value )

	elseif key == "flag" and numberValue then

		if numberValue == -1 then
			LrSelection.flagAsReject()
		elseif numberValue == 0 then
			LrSelection.removeFlag()
		elseif numberValue == 1 then
			LrSelection.flagAsPick()
		end
		
	elseif key == "labels" then
	
		--[[ TODO: parse to get bools for each label, thencall:

			LrController.setColorLabels {
				[1] = bool,
				[2] = bool,
				[3] = bool,
				[4] = bool,
				[5] = bool,
			}
		]]--

	elseif key and develop_param_set[ key ] then

		value = tonumber( value )
		if value then
			LrDevelopController.setValue( key, value )
		end
	end

end

--------------------------------------------------------------------------------
-- simple parser for handling messages sent from the external process over the socket

local function parseMessage( data )

	if type( data ) == "string" then

		local _, _, key, value = string.find( data, "([^ ]+)%s*=%s*(.*)" ) -- ex: "rating = 2"
		
		if data and not key then
			data = loadstring( "return " .. data )
			if type( data ) == "table" then
				key = data.key
				value = data.value
			end
		end
	
		return key, value
	end
end

--------------------------------------------------------------------------------
-- checks all supported photo attributes for any changes that happened in Lr, reporting
-- them to the sender socket.

local function updateAttributes( observer )
	local sender = observer._sender
	updateValue( observer, sender, "rating", LrSelection.getRating() or 0 )
	updateValue( observer, sender, "flag", LrSelection.getFlag() or 0 )
	updateValue( observer, sender, "labels", LrSelection.getColorLabel() )
end

--------------------------------------------------------------------------------
-- checks all Develop parameters for any changes that happened in Lr, reporting
-- them to the sender socket.

local function updateDevelopParameters( observer )
	local sender = observer._sender
	for _, param in ipairs( develop_params ) do
		updateValue( observer, sender, param, LrDevelopController.getValue( param ) )
	end
end

--------------------------------------------------------------------------------

local AUTO_PORT = 0 -- port zero indicates that we want the OS to auto-assign the port

local address = "localhost"
local sendPort = AUTO_PORT
local receivePort = AUTO_PORT

--------------------------------------------------------------------------------
-- Start everything in a task so we can sleep in a loop until we are shut down.

LrTasks.startAsyncTask( function()

	-- a function context is required for the socket API below. When this context is exited the
	-- socket connection will be closed.

	LrFunctionContext.callWithContext( 'socket_remote', function( context )

		local senderPort, senderConnected, receiverPort, receiverConnected
		
		local function maybeStartService()
			-- once we've established port numbers for both the sender and receiver sockets, tell the
			-- user what they are so they can connect to them via Telnet for the demo.
			if senderPort and receiverPort then

				LrTasks.startAsyncTask( function()

					for countDown = 10, 1, -1 do

						if not _G.running then
							break
						end
						
						if senderConnected and receiverConnected then
							break
						end
												
						local msg = "Connect to port:\n"
						if not receiverConnected then
							msg = msg..string.format( "Receiver = %d\n", receiverPort)
						end
						
						if not senderConnected then
							msg = msg..string.format( "Sender = %d\n", senderPort)
						end
						
						msg = msg..string.format("%d", countDown)

						LrDialogs.showBezel( msg, 1 )
						LrTasks.sleep( 1 )
					end
				end )
			end
		end

		-- socket connection used to send messages from the plugin to the external process

		local sender = LrSocket.bind {
			name = "Remote Control Sender", -- (optional)
			functionContext = context,
			address = address,
			port = sendPort,
			mode = "send",

			onConnecting = function( socket, port )
				--LrDialogs.message("Sender port connecting...")
				senderPort = port
				maybeStartService()
			end,
			
			onConnected = function( socket, port )
				--LrDialogs.message("Sender port connected...")
				senderConnected = true
			end,

			onMessage = function( socket, message )
				LrDialogs.message("We should never see this...")
				-- nothing, we don't expect to get any messages back
			end,

			onClosed = function( socket )
				--LrDialogs.message("Sender connection closed...")
				-- exit the run loop below
				_G.running = false
			end,

			onError = function( socket, err )
				--LrDialogs.message("Sender socket error: "..err)
				if err == "timeout" then
					--LrDialogs.message("Sender socket attempting re-connect...")
					socket:reconnect()
				end
			end,
			plugin = _PLUGIN
		}

		-- socket connection used to recieve messages from the external process

		local receiver = LrSocket.bind {
			name = "Remote Control Receiver", -- (optional)
			functionContext = context,
			address = address,
			port = receivePort,
			mode = "receive",

			onConnecting = function( socket, port )
				--LrDialogs.message("Receiver port connecting...")			
				receiverPort = port
				maybeStartService()
			end,

			onConnected = function( socket, port )
				--LrDialogs.message("Receiver port connected...")			
				receiverConnected = true
			end,

			onClosed = function( socket )
				--LrDialogs.message("Receiver port closed...")			
				-- exit the run loop below
				_G.running = false
			end,

			onMessage = function( socket, message )
				--LrDialogs.message("Receiver port message recieved...")
				if type( message ) == "string" then
					local key, value = parseMessage( message )
					if key and value then
						setValue( key, value )
						LrDialogs.showBezel(key .. " " .. value, 4)
					end
				end
			end,
			
			onError = function( socket, err )
				--LrDialogs.message("Receiver port error. Attempting reconnect...")			
				if err == "timeout" then
					socket:reconnect()
				end
			end,
			plugin = _PLUGIN
		}
		
		-- object used to observe both selection changes and Develop parameter changes and
		-- report them all to the sender socket.
		
		local observer = {
			_sender = sender,
		}
		
		LrApplication.addActivePhotoChangeObserver( context, observer, updateAttributes )
		LrDevelopController.addAdjustmentChangeObserver( context, observer, updateDevelopParameters )

		LrDevelopController.revealAdjustedControls( true ) -- doesn't exist in API reference
	
		-- do intial update

		updateAttributes( observer )
		updateDevelopParameters( observer )

		-- loop until this plug-in global is set to false, either by a "close" command issued by the external
		-- process or when the user selects "Stop" from the "Plug-in Extras" menu.

		_G.running = true

		while _G.running do
			LrTasks.sleep( 1/2 ) -- seconds
		end
		
		--LrDialogs.message("Sender type ='"..sender:type().."'")
		
		_G.shutdown = true

		if senderConnected then
			sender:close()
		end
		
		if receiverConnected then
			receiver:close()
		end
				
		LrDialogs.showBezel( "Remote Connections Closed", 4 )
			
	end )

end )
