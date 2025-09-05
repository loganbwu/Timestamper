local LrDialogs = import 'LrDialogs'
local LrFunctionContext = import 'LrFunctionContext'
local LrTasks = import 'LrTasks'
local LrView = import 'LrView'
local LrColor = import 'LrColor'
local LrBinding = import 'LrBinding'
local LrSocket = import 'LrSocket'
local f = LrView.osFactory()

local midiGUI = require 'midiGUI'

LrTasks.startAsyncTask(function()

	LrFunctionContext.callWithContext("midiMapper", function(context)
	
		local properties = LrBinding.makePropertyTable(context)
		
		properties.slash = WIN_ENV and "\\" or "/"
		
		local rows = midiGUI.setupView(properties, context)
		local contentCol = f:column(rows)
		local content = f:scrolled_view({contentCol, width=500, height=800, visible=true, enabled=true, size='mini'})
		
		LrDialogs.presentFloatingDialog(_PLUGIN,
			{
				title = "MIDI Mapper",
				contents = content,
				blockTask = true,
				background_color = LrColor(0.75, 0.75, 0.75)
			})
		
	end)

end)