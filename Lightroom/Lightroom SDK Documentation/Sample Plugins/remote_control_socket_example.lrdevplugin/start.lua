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
local LrBinding = import "LrBinding"

local LrController = import "LrController"
local LrDevelopController = import "LrDevelopController"
local LrSocket = import "LrSocket"

local LrView = import "LrView"
local f = LrView.osFactory()

local connection_properties = nil

local context = nil

local receiver, sender = {}
local observer = {}



--==============================================================================
-- All of the Develop parameters that we will monitor for changes.

local develop_params = {
	--"Temperature",	--other possible parameters to modify
	--"Tint",
	"Exposure",
	"Contrast",
	--"Highlights",
	--"Shadows",
	--"Whites",
	--"Blacks",
	--"Clarity",
	--"Vibrance",
	--"Saturation",
}

local develop_param_set = {}

for _, key in ipairs( develop_params ) do
	develop_param_set[ key ] = true
end

--------------------------------------------------------------------------------
-- Checks to see if observer[ key ] is equal to the given value.  If the value has
-- changed, reports the change to the given sender.
-- Used to notify external processes when settings change in Lr.

local updateValue = function( observer, sender, key, value )

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
	
		local data = key.." = "..value.."\n"
	
		if WIN_ENV then
			data = string.gsub( data, "\n", "\r\n" )
		end
			
		sender:send( data )
	end
end

--------------------------------------------------------------------------------
-- Callback function called when a message is received

local updateDevelopParameters = function( observer)
	for _, param in ipairs( develop_params ) do
		updateValue( observer, sender, param, LrDevelopController.getValue( param ) )
	end
end

--------------------------------------------------------------------------------
-- Calls the appropriate API to adjust a setting in Lr.

local setValue = function( key, value )

	if value == "+" then
		LrDevelopController.increment( key )
		return
	end
	
	if value == "-" then
		LrDevelopController.decrement( key )
		return
	end
	
	if value == "reset" and key ~= "history" then
		LrDevelopController.resetToDefault( key )
		return
	end
	
	if key == "move" then
		if value == "previous" then LrController.previousPhoto() end
		if value == "next" then LrController.nextPhoto() end
		return
	end
	
	if key == "history" then
		if value == "undo" then
			LrController.undo()
		end
		if value == "redo" then
			LrController.redo()
		end
		if value == "reset" then
			LrDevelopController.resetAllDevelopAdjustments()
		end
		return
	end
	
	if key and develop_param_set[ key ] then

		value = tonumber( value )
		if value then
			LrDevelopController.setValue( key, value )
		end
		return
	end

end



--------------------------------------------------------------------------------
-- simple parser for handling messages sent from the external process over the socket

local parseMessage = function( data )

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
--called when the Listen button is clicked in GUI

local receiveConnect = function()

	--check if port is of correct type
	if (tonumber(connection_properties.receivePort, 10) or connection_properties.receivePort == nil) then
		receiver = LrSocket.bind {
				name = "Remote Control Receiver", -- (optional)
				functionContext = context,
				address = connection_properties.receiveAddress or "127.0.0.1",
				port = tonumber(connection_properties.receivePort) or 0,
				mode = "receive",

				onConnecting = function( socket, port )
					connection_properties.receiveStatus = "Connecting on "..socket._address..":"..port
				end,

				onConnected = function( socket, port )
					connection_properties.receiveStatus = "Connected to "..socket._address..":"..port
				end,

				onClosed = function( socket )
					-- exit the run loop below
					connection_properties.receiveStatus = "Inactive"
					--_G.running = false
				end,

				onMessage = function( socket, message )
					if type( message ) == "string" then
						local key, value = parseMessage( message )
						if key and value then
							setValue( key, value )
						end
					end
				end,
				
				onError = function( socket, err )
					connection_properties.receiveStatus = err
					--if err == "timeout" then
						--socket:reconnect()
					--end
				end,
				plugin = _PLUGIN
		}
	else
		connection_properties.receiveStatus = "Incorrect address port number"
	end
end

--------------------------------------------------------------------------------
--called when the Connect button is clicked in the GUI

local sendConnect = function()

	--check if port is of correct type
	if (tonumber(connection_properties.sendPort, 10) or connection_properties.sendPort == nil)
		and connection_properties.sendAddress ~= nil then
		sender = LrSocket.bind {
				name = "Remote Control Sender", -- (optional)
				functionContext = context,
				address = connection_properties.sendAddress,
				port = tonumber(connection_properties.sendPort) or 0,
				mode = "send",

				onConnecting = function( socket, port )
					connection_properties.sendStatus = "Connecting on "..socket._address..":"..port
				end,

				onConnected = function( socket, port )
					connection_properties.sendStatus = "Connected to "..socket._address..":"..port
				end,

				onClosed = function( socket )
					connection_properties.sendStatus = "Inactive"
				end,

				onMessage = function( socket, message )
					if type( message ) == "string" then
						local key, value = parseMessage( message )
						if key and value then
							setValue( key, value )
						end
					end
				end,
				
				onError = function( socket, err )
					connection_properties.sendStatus = err
					--if err == "timeout" then
						--socket:reconnect()
					--end
				end,
				plugin = _PLUGIN
		}
	else
		connection_properties.sendStatus = "Incorrect address or port number"
	end
	observer._sender = sender
		
	LrDevelopController.addAdjustmentChangeObserver( context, observer, updateDevelopParameters)
end

--------------------------------------------------------------------------------
--Builds the plugin GUI

local buildGUI = function()

	LrTasks.startAsyncTask( function()

		LrDialogs.presentFloatingDialog( _PLUGIN, {
			title = "Socket Demo",
			save_frame = "Slider_Control_Demo",
			blockTask = true,
			windowWillClose = (function() _G.running = false end), 

			
			contents = f:column {
				
				f:group_box {
					title = "Receive",
					
					f:row {
						f:static_text {
							title = "Port:"
						
						},
						f:edit_field{
							bind_to_object = connection_properties,
							immediate = true,
							value = LrView.bind('receivePort')
						},
						f:push_button {
							title = "Listen",
							action = receiveConnect
						},
					},
					f:row {
						f:static_text {
							title = "Status:"
						
						},
						f:static_text {
							bind_to_object = connection_properties,
							title = LrView.bind("receiveStatus"),
							width_in_chars = 30,
						}
					}
				},
				f:group_box {
					title = "Send",
					
					f:row {
						f:static_text {
							title = "Hostname:"
						
						},
						f:edit_field{
							bind_to_object = connection_properties,
							immediate = true,
							value = LrView.bind('sendAddress')
						},
						f:static_text {
							title = "Port:"
						
						},
						f:edit_field{
							bind_to_object = connection_properties,
							immediate = true,
							value = LrView.bind('sendPort')
						},
						f:push_button {
							title = "Connect",
							action = sendConnect
						},
					},
					f:row {
						f:static_text {
							title = "Status:"
						
						},
						f:static_text {
							bind_to_object = connection_properties,
							title = LrView.bind("sendStatus"),
							width_in_chars = 30,
						}
					},
				},				
				
			}
		} )
	end )
end

--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
-- Start everything in a task so we can sleep in a loop until we are shut down.

LrTasks.startAsyncTask( function()

	-- a function context is required for the socket API below. When this context is exited the
	-- socket connection will be closed.

	LrFunctionContext.callWithContext( 'socket_remote', function( cntxt )


		_G.running = true
		context = cntxt
		
		connection_properties = LrBinding.makePropertyTable( context )
		connection_properties.receivePort = nil
		connection_properties.receiveAddress = "localhost"	--we can only listen for connections locally
		connection_properties.receiveStatus = "Inactive"
		connection_properties.sendPort = nil
		connection_properties.sendAddress = nil
		connection_properties.sendStatus = "Inactive"
		
		--LrTasks.startAsyncTask( function () buildGUI() end)
		buildGUI()

		
		
		
		while _G.running do
			LrTasks.sleep( 1/2 ) -- seconds
		end
		
		
		--redundancy in case of errors when exiting the context
		--so that we do not have hanging sockets
		if (receiver~=nil and receiver.close) then
			receiver:close()
		end
		
		if (sender~=nil and sender.close) then
			sender:close()
		end
		
		_G.shutdown = true
		

	end )

end )

