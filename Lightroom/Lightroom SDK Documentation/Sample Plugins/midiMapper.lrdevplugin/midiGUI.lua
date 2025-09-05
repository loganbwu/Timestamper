local LrView = import 'LrView'
local LrColor = import 'LrColor'
local LrDialogs = import 'LrDialogs'
local LrBinding = import 'LrBinding'
local LrTasks = import 'LrTasks'
local LrFileUtils = import 'LrFileUtils'
local LrSocket = import 'LrSocket'
local LrDevelopController = import 'LrDevelopController'
local LrController = import 'LrController'

local f = LrView.osFactory()

local properties = nil
local context = nil

local midiGUI = {}

local Controls = {{ title = "LrController.deselectActive" , value = "LrController.deselectActive" },
				{ title = "LrController.deselectOthers",value = "LrController.deselectOthers"},
				{ title = "LrController.extendSelection",value = "LrController.extendSelection"},
				{ title = "LrController.nextPhoto",value = "LrController.nextPhoto"},
				{ title = "LrController.previousPhoto",value = "LrController.previousPhoto"},
				{ title = "LrController.redo",value = "LrController.redo"},
				{ title = "LrController.selectAll",value = "LrController.selectAll"},
				{ title = "LrController.selectInverse",value = "LrController.selectInverse"},
				{ title = "LrController.selectLastPhoto",value = "LrController.selectLastPhoto"},
				{ title = "LrController.selectNone",value = "LrController.selectNone"},
				{ title = "LrController.showDevelopLoupe",value = "LrController.showDevelopLoupe"},
				{ title = "LrController.showGrid",value = "LrController.showGrid"},
				{ title = "LrController.showLoupe",value = "LrController.showLoupe"},
				{ title = "LrController.showSecondaryCompare",value = "LrController.showSecondaryCompare"},
				{ title = "LrController.showSecondaryGrid",value = "LrController.showSecondaryGrid"},
				{ title = "LrController.showSecondaryLiveLoupe",value = "LrController.showSecondaryLiveLoupe"},
				{ title = "LrController.showSecondaryLockedLoupe",value = "LrController.showSecondaryLockedLoupe"},
				{ title = "LrController.showSecondaryLoupe",value = "LrController.showSecondaryLoupe"},
				{ title = "LrController.showSecondarySlideShow",value = "LrController.showSecondarySlideShow"},
				{ title = "LrController.showSecondarySurvey",value = "LrController.showSecondarySurvery"},
				{ title = "LrController.startSlideshow",value = "LrController.startSlideshow"},
				{ title = "LrController.stopSlideshow",value = "LrController.stopSlideshow"},
				{ title = "LrController.toggleSecondaryDisplay",value = "LrController.toggleSecondaryDisplay"},
				{ title = "LrController.toggleSecondaryDisplayFullscreen",value = "LrController.toggleSecondaryDisplayFullscreen"},
				{ title = "LrController.triggerCapture",value = "LrController.triggerCapture"},
				{ title = "LrController.undo",value = "LrController.undo"},
				{ title = "LrDevelopController.decrement",value = "LrDevelopController.decrement"},
				{ title = "LrDevelopController.increment",value = "LrDevelopController.increment"},
				{ title = "LrDevelopController.resetAllDevelopAdjustments",value = "LrDevelopController.resetAllDevelopAdjustments"},
				{ title = "LrDevelopController.resetBrushing",value = "LrDevelopController.resetBrushing"},
				{ title = "LrDevelopController.resetCircularGradient",value = "LrDevelopController.resetCircularGradient"},
				{ title = "LrDevelopController.resetCrop",value = "LrDevelopController.resetCrop"},
				{ title = "LrDevelopController.resetGradient",value = "LrDevelopController.resetGradient"},
				{ title = "LrDevelopController.resetRedeye",value = "LrDevelopController.resetRedeye"},
				{ title = "LrDevelopController.resetSpotRemoval",value = "LrDevelopController.resetSpotRemoval"},
				{ title = "LrDevelopController.resetToDefault",value = "LrDevelopController.resetToDefault"},
				{ title = "LrDevelopController.selectTool",value = "LrDevelopController.selectTool"},
				{ title = "LrDevelopController.setValue",value = "LrDevelopController.setValue"},
				{ title = "LrDevelopController.switchToModule",value = "LrDevelopController.switchToModule"} }
				
local controlLookup = {	[1] = nil,	--to be filled with midi control indicators
						[2] = nil,	--LrChange->
						[3] = nil,
						[4] = nil,
						[5] = nil,
						[6] = nil,
						[7] = nil,
						[8] = nil,
						[9] = nil,
						[10] = nil }
						
local functionLookup = {			--midi signal->functionLookup->paramLookup



							}
							
local paramLookup = {	["LrController.deselectActive"] = nil,
						["LrController.deselectOthers"] = nil,
						["LrController.extendSelection"] = nil,
						["LrController.nextPhoto"] = nil,
						["LrController.previousPhoto"] = nil,
						["LrController.redo"] = nil,
						["LrController.undo"] = nil,
						["LrController.selectAll"] = nil,
						["LrController.selectInverse"] = nil,
						["LrController.selectLastPhoto"] = nil,
						["LrController.selectNone"] = nil,
						["LrController.showDevelopLoupe"] = nil,
						["LrController.showGrid"] = nil,
						["LrController.showLoupe"] = nil,
						["LrController.showSecondaryCompare"] = nil,
						["LrController.showSecondaryGrid"] = nil,
						["LrController.showSecondaryLiveLoupe"] = nil,
						["LrController.showSecondaryLockedLoupe"] = nil,
						["LrController.showSecondaryLoupe"] = nil,
						["LrController.showSecondarySlideshow"] = nil,
						["LrController.showSecondarySurvey"] = nil,
						["LrController.startSlideshow"] = nil,
						["LrController.stopSlideshow"] = nil,
						["LrController.toggleSecondaryDisplay"] = nil,
						["LrController.toggleSecondaryDisplayFullscreen"] = nil,
						["LrController.triggerCapture"] = nil,
						["LrDevelopController.decrement"] = "param",
						["LrDevelopController.increment"] = "param",
						["LrDevelopController.resetAllDevelopAdjustments"] = nil,
						["LrDevelopController.resetBrushing"] = nil,
						["LrDevelopController.resetCircularGradient"] = nil,
						["LrDevelopController.resetCrop"] = nil,
						["LrDevelopController.resetGradient"] = nil,
						["LrDevelopController.resetRedeye"] = nil,
						["LrDevelopController.resetSpotRemoval"] = nil,
						["LrDevelopController.resetToDefault"] = "param",
						["LrDevelopController.selectTool"] = "tool",
						["LrDevelopController.setValue"] = "param,value",
						["LrDevelopController.switchToModule"] = nil, }
						
local developParams = {{title = "Exposure", value = "Exposure"},
						{title = "Contrast", value = "Contrast"},
						{title = "Highlights", value = "Highlights"},
						{title = "Shadows", value = "Shadows"},
						{title = "Whites", value = "Whites"},
						{title = "Blacks", value = "Blacks"},
						{title = "Clarity", value = "Clarity"},
						{title = "Vibrance", value = "Vibrance"},
						{title = "Saturation", value = "Saturation"}}
							
midiGUI.executeCommand = function(midiMessage)

	--m1,m2 are the control indicators, m3 is the value
	local m1 = string.byte(midiMessage,1)
	local m2 = string.byte(midiMessage,2)
	local m3 = string.byte(midiMessage,3)
	
	if(paramLookup[functionLookup[m1..m2]] == nil) then
		loadstring("LrDevelopController = import 'LrDevelopController'")()
		loadstring("LrController = import 'LrController'")()
		loadstring(properties.controlViews[controlLookup[m1..m2]].action.."()")()
	elseif(paramLookup[functionLookup[m1..m2]] == "param,value") then
		local devParam = properties.controlViews[controlLookup[m1..m2]].param
		local outParam = midiGUI.scaleParameter(m3, devParam)
		loadstring("LrDevelopController = import 'LrDevelopController'")()
		loadstring("LrController = import 'LrController'")()
		--local developParam =
		loadstring(properties.controlViews[controlLookup[m1..m2]].action.."(\""..devParam.."\""..","..outParam..")")()
	elseif(paramLookup[functionLookup[m1..m2]] == "param") then
		local devParam = properties.controlViews[controlLookup[m1..m2]].param
		loadstring("LrDevelopController = import 'LrDevelopController'")()
		loadstring("LrController = import 'LrController'")()
		loadstring(properties.controlViews[controlLookup[m1..m2]].action.."(\""..devParam.."\")")()
	end
	
end

midiGUI.scaleParameter = function(inValue, param)
	
	local outValue
	local minParam, maxParam = LrDevelopController.getRange(param)
	
	outValue = (inValue/127)*(maxParam-minParam)+minParam
	
	return outValue

end

midiGUI.mapMidiControl = function(controlNumber)
	local pastMessage = properties.currentMessage
	LrTasks.startAsyncTask(function()
		while(pastMessage == properties.currentMessage) do
			--wait until change
			LrTasks.yield()
		end
		local currentMessage = properties.currentMessage
		
		controlLookup[controlNumber] = string.byte(currentMessage,1)..string.byte(currentMessage,2)
		controlLookup[string.byte(currentMessage,1)..string.byte(currentMessage,2)] = controlNumber --reverse lookup
		local m1 = string.byte(currentMessage,1)
		properties.controlViews[controlNumber].b1 = m1
		local m2 = string.byte(currentMessage,2)
		properties.controlViews[controlNumber].b2 = m2
		functionLookup[m1..m2] = properties.controlViews[controlNumber].action
	end)
	
end

midiGUI.setupView = function(props, cntxt)

	properties = props
	context = cntxt
	properties.controlViews = midiGUI.createBinds()
	properties.sendSocket = {}
	properties.receiveSocket = {}
	
	local view = {}
	
	view[1] = midiGUI.getReceiveRow()
	view[#view+1] = f:spacer({height=10})
	view[#view+1] = midiGUI.getSendRow()
	view[#view+1] = f:spacer({height=10})
	for i=1,10 do
		view[#view+1] = f:group_box({title = "Control " .. i, midiGUI.getControlRow(i)})
		view[#view+1] = f:spacer({height=5})
	end
	
	return view
	

end

midiGUI.sendConnect = function(ipAddress, portNo)

	if ipAddress and portNo then
		properties.sendSocket = LrSocket.bind({
			functionContext = context,
			address = ipAddress,
			port = tonumber(portNo),
			mode = "send",
			onConnecting = function(socket, port) properties.controlViews.send.connected = "Connecting..." end,
			onConnected = function(socket, port) properties.controlViews.send.connected = "Connected" end,
			onError = function(socket, errorMsg) properties.controlViews.send.connected = errorMsg end,
			onMessage = function(socket, message) properties.controlViews.send.connected = "Message" end,
			onClosed = function(socket) properties.controlViews.send.connected = "Closed" end,
			plugin = _PLUGIN
		})
	end

end

midiGUI.receiveConnect = function(ipAddress, portNo)

	if portNo then
		properties.receiveSocket = LrSocket.bind({
			functionContext = context,
			address = ipAddress,
			port = tonumber(portNo),
			mode = "receive",
			onConnecting = function(socket, port) properties.controlViews.receive.connected = "Connecting..." end,
			onConnected = function(socket, port) properties.controlViews.receive.connected = "Connected" end,
			onError = function(socket, errorMsg) properties.controlViews.receive.connected = errorMsg end,
			onMessage = function(socket, message)
				properties.currentMessage = message
				LrTasks.startAsyncTaskWithoutErrorHandler(function()midiGUI.executeCommand(message) end)
				--properties.controlViews.receive.connected = string.byte(message,1) .." "..string.byte(message,2) .." "..string.byte(message,3)
			end,
			onClosed = function(socket) end,
			plugin = _PLUGIN
		})
	end
	
end

midiGUI.createBinds = function()
	
	local binds = {}
	midiGUI.createReceiveBind(binds)
	midiGUI.createSendBind(binds)
	midiGUI.createControlBinds(binds)
	
	return binds

end

midiGUI.createReceiveBind = function(binds)

	local receiveBind = LrBinding.makePropertyTable(context)
	
	receiveBind.connected = "Not Connected"
	receiveBind.ip = nil
	receiveBind.port = 0
	
	binds["receive"] = receiveBind

end

midiGUI.createSendBind = function(binds)

	local sendBind = LrBinding.makePropertyTable(context)
	
	sendBind.connected = "Not Connected"
	sendBind.ip = nil
	sendBind.port = 0
	
	binds["send"] = sendBind
	
end

midiGUI.createControlBinds = function(binds)

	for i=1,10 do
		
		local controlBind = LrBinding.makePropertyTable(context)
		
		controlBind.status = nil
		controlBind.data = nil
		controlBind.action = nil
		controlBind.mapped = false
		controlBind.param = nil
		controlBind.b1 = nil
		controlBind.b2 = nil
		
		binds[i] = controlBind
		
	end
end

midiGUI.getReceiveRow = function()

	local receiveRow = f:group_box({
	title = "Receive",
	f:row({
	
		f:static_text({
			title ="IP Address: ",
		
		}),
		f:edit_field({
			bind_to_object = properties.controlViews.receive,
			width = 100,
			immediate = true,
			value = LrView.bind('ip')
		}),
		f:static_text({
			title ="Port: ",
		
		}),
		f:edit_field({
			bind_to_object = properties.controlViews.receive,
			width = 100,
			immediate = true,
			value = LrView.bind('port')
		}),
		f:push_button({
			title = "Listen",
			action = function() midiGUI.receiveConnect(properties.controlViews.receive.ip, properties.controlViews.receive.port) end
		}),
		
	}),
	f:row({
	
		f:static_text({
			title ="Status: ",
			width = 50,
		
		}),
		f:static_text({
			bind_to_object = properties.controlViews.receive,
			title = LrView.bind("connected"),
			width = 100,
		
		}),
		
	})
	})
	
	return receiveRow
	
end

midiGUI.getSendRow = function()

	local sendRow = f:group_box({
	title = "Send",
	f:row({
		
		f:static_text({
			title ="IP Address: ",
		
		}),
		f:edit_field({
			bind_to_object = properties.controlViews.send,
			width = 100,
			immediate = true,
			value = LrView.bind('ip')
		}),
		f:static_text({
			title ="Port: ",
		
		}),
		f:edit_field({
			bind_to_object = properties.controlViews.send,
			width = 100,
			immediate = true,
			value = LrView.bind('port')
		}),
		f:push_button({
			title = "Connect",
			action = function() midiGUI.sendConnect(properties.controlViews.send.ip, properties.controlViews.send.port) end
		}),
		
	}),
	f:row({
	
		f:static_text({
			title ="Status: ",
			width = 50,
		
		}),
		f:static_text({
			bind_to_object = properties.controlViews.send,
			title = LrView.bind("connected"),
			width = 100,
		
		}),
		
	})
	})
	
	return sendRow

end

midiGUI.getControlRow = function(i)

	local controlRow = f:row({
	f:popup_menu({
		bind_to_object = properties.controlViews[i],
		width_in_chars = 20,
		value = LrView.bind('action'),
		items = Controls
	}),
	f:popup_menu({
		bind_to_object = properties.controlViews[i],
		width_in_chars = 10,
		value = LrView.bind('param'),
		items = developParams
	
	}),
	f:push_button({
		title = "Map",
		action = function() midiGUI.mapMidiControl(i) end
	}),
	f:static_text({
		title ="Byte 1: ",
	}),
	f:static_text({
		bind_to_object = properties.controlViews[i],
		title = LrView.bind('b1'),
	}),
	f:static_text({
		title ="Byte 2: ",
	}),
	f:static_text({
		bind_to_object = properties.controlViews[i],
		title = LrView.bind('b2'),
	}),
	})
	
	return controlRow

end

return midiGUI