--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2014 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

------------------------------------------------------------------------------]]

local LrTasks = import "LrTasks"

--------------------------------------------------------------------------------

return {

	LrShutdownFunction = function( doneFunction, progressFunction )
		LrTasks.startAsyncTask( function()
			
			_G.running = false -- tell the run loop to terminate

			-- tell the app we're done
			progressFunction( 1 )
			doneFunction()
		end )
	end,
}
