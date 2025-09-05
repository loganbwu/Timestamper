--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2007 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

--------------------------------------------------------------------------------

Info.lua
Summary information for Arnold- API Test Plug-in.
  "We're going to... PUMP... YOU UP!"

------------------------------------------------------------------------------]]

return {
	
	LrSdkVersion = 6.0,
	LrPluginName = "Midi Mapper",
	LrSdkMinimumVersion = 6.0, -- minimum SDK version required by this plug-in

	LrToolkitIdentifier = 'com.adobe.lightroom.sdk.midiMapper',
	
	-- Add the menu item to the File menu
	LrExportMenuItems = {
		{
			title = "Open",
			file = "midiMapper.lua",
		},
	},
	VERSION = { major=8, minor=3, revision=0, build=200000, },

}


	
