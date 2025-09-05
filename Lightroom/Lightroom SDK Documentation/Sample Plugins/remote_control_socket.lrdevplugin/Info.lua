--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2014 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

------------------------------------------------------------------------------]]

local tbl = {

	LrSdkVersion = 6.0,
	
	LrPluginName = "Socket Remote",
	
	LrToolkitIdentifier = 'com.adobe.lightroom.demo.remote_control_socket',
	
	LrExportMenuItems = {
		{
			title = "Start",
			file = "start.lua",
		},
		{
			title = "Stop",
			file = "stop.lua",
		},
	},
	
	LrInitPlugin = "start.lua",
	LrForceInitPlugin  = true,
	LrDisablePlugin = "stop.lua",
	LrShutdownPlugin = "shutdown.lua",	
	LrShutdownApp = "shutdown.lua",

	VERSION = { major=8, minor=3, revision=0, build=200000, },

}

return tbl
