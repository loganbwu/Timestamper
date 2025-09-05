--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2013 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

------------------------------------------------------------------------------]]

local tbl = {

	LrSdkVersion = 3.0,
	
	LrPluginName = "Remote Slider Control",
	
	LrToolkitIdentifier = 'com.adobe.lightroom.demo.remote_slider_control',
	
	LrExportMenuItems = {
		{
			title = "Run Demo",
			file = "RunDemo.lua",
		},
	},


	VERSION = { major=8, minor=3, revision=0, build=200000, },

}

return tbl
