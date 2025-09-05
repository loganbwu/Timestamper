--[[----------------------------------------------------------------------------

ADOBE SYSTEMS INCORPORATED
 Copyright 2014 Adobe Systems Incorporated
 All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in accordance
with the terms of the Adobe license agreement accompanying it. If you have received
this file from a source other than Adobe, then your use, modification, or distribution
of it requires the prior written permission of Adobe.

------------------------------------------------------------------------------]]

local LrBinding = import "LrBinding"
local LrDialogs = import "LrDialogs"
local LrFunctionContext = import "LrFunctionContext"
local LrTasks = import "LrTasks"
local LrView = import "LrView"

local LrController = import "LrController"
local LrDevelopController = import "LrDevelopController"

--------------------------------------------------------------------------------

local bind = LrView.bind
local f = LrView.osFactory()

--==============================================================================

local allParams = {}
	-- all of the Develop parameters that have controls in this dialog

local updating_params = false
local updating_attributes = false

--------------------------------------------------------------------------------
-- Updates the property table to match the current Develop parameters of the active photo.

local function loadSettings( properties )

	updating_params = true
	
	for param, _ in pairs( allParams ) do

		local value = LrDevelopController.getValue( param )
		local min, max = LrDevelopController.getRange( param )

		properties[ param .. "_min" ] = min
		properties[ param .. "_max" ] = max
		properties[ param ] = value
	end

	updating_params = false
end

--------------------------------------------------------------------------------

local function loadAttributes( properties )

	updating_attributes = true

		properties.rating = LrController.getRating() or 0
		properties.flag = LrController.getFlag() or 0
		local labels = LrController.getColorLabels()
		properties.colorLabel1 = labels[ 1 ]
		properties.colorLabel2 = labels[ 2 ]
		properties.colorLabel3 = labels[ 3 ]
		properties.colorLabel4 = labels[ 4 ]
		properties.colorLabel5 = labels[ 5 ]

	updating_attributes = false
end

--------------------------------------------------------------------------------
-- Builds a slider row that is bound to a single Develop parameter.

local function makeAdjustmentRowImp( properties, title, param, optPrecision )

	local min, max = LrDevelopController.getRange( param )
	
	if min == nil or max == nil then
		return f:static_text { title = "Unknown param: " .. param, }
	end

	allParams[ param ] = true
	
	local minBinding = bind( param .. "_min" )
	local maxBinding = bind( param .. "_max" )		
	local range = max - min
	local precision = optPrecision or ( (range <= 10) and 2 or 0 )
	
	-- setup initial state of slider
	updating_params = true
	properties[ param .. "_min" ] = min
	properties[ param .. "_max" ] = max
	properties[ param ] = LrDevelopController.getValue( param )
	updating_params = false

	return f:row {
		spacing = 4,
		fill_horizontal = 1,

		f:static_text {
			title = title,
			alignment = "right",
			shared = { width = "label_width" },
		},

		f:push_button {
			title = "-",
			action = function()
				LrDevelopController.decrement( param )
			end,
		},

		f:slider {
			min = minBinding,
			max = maxBinding,
			value = bind( param ),
			width = 150,
			fill_horizontal = 1,
		},

		f:push_button {
			title = "+",
			action = function()
				LrDevelopController.increment( param )
			end,
		},

		f:edit_field {
			min = minBinding,
			max = maxBinding,
			width_in_digits = 6,
			precision = precision,
			size = "small",
			alwaysShowSign = true,
			alignment = "right",
			value = bind( param ),
		},
		
		f:push_button {
			title = "Reset",
			size = "small",
			place_horizontal = 1,
			action = function()
				LrDevelopController.resetToDefault( param )
			end,
		},
	}

end

--------------------------------------------------------------------------------

local function sep()
	return f:separator { fill_horizontal = 1, }
end

--------------------------------------------------------------------------------

LrTasks.startAsyncTask(function()

	LrFunctionContext.callWithContext( 'demo', function( context )

			-- The develop controller only works if the Develop module is active.
		local LrApplicationView = import "LrApplicationView"
		LrApplicationView.switchToModule( "develop" )

			-- Whenever tracking is on, the Develop module behaves as if the user is dragging on a slider.  All adjustments done
			-- during that time will be combined into a single history state the next time tracking is switched back off.
			-- The Develop module also renders photos more quickly at a lower quality while tracking is on, to improve the
			-- framerate during interactive adjustment.
			--
			-- By default, all of the LrDevelopController APIs will enable tracking whenever an adjustment is made and
			-- automatically turn it back off again after a short period of inactivity (or immediately if a different
			-- parameter is adjusted). By default this delay is set to 2 seconds, but it can be changed as shown below.
			--
			-- If you set this delay to zero, you must manage the tracking state yourself. Every adjustment that is made while
			-- tracking is off will generate a new history state and cause a high-quality (slow) render. To avoid this you will
			-- have to call LrDevelopController.startTracking( param ) before your first adjustment and stopTracking() after your
			-- adjustments are complete. This approach is more complex and error-prone than the automatic timer-based and is
			-- not recommended.
		LrDevelopController.setTrackingDelay( 1 )

		local develop_properties = LrBinding.makePropertyTable( context )
		local attribute_properties = LrBinding.makePropertyTable( context )
		
		local makeAdjustmentRow = function( ... )
			return makeAdjustmentRowImp( develop_properties, ... )
		end

			-- Whenever a slider is moved, update the associated Develop adjustment.
		develop_properties:addObserver( 'ALL', function( properties, key, value )
			if not updating_params then
				LrDevelopController.setValue( key, value )
			end
		end )

			-- Whenever the Develop adjustments change, updates the slider values to match.
		LrDevelopController.addAdjustmentChangeObserver( context, develop_properties, function( properties )
			loadSettings( properties )
		end )
		
		attribute_properties:addObserver( "ALL", function( properties, key, value )
			if not updating_attributes then

				if key == "rating" then

					LrController.setRating( properties.rating )

				elseif key == "flag" then

					if value == -1 then
						LrController.flagAsReject()
					elseif value == 0 then
						LrController.removeFlag()
					elseif value == 1 then
						LrController.flagAsPick()
					end
				end

				if key == "colorLabel1" or key == "colorLabel2"or key == "colorLabel3"
					or key == "colorLabel4" or key == "colorLabel5" then

					LrController.setColorLabels {
						[1] = properties.colorLabel1,
						[2] = properties.colorLabel2,
						[3] = properties.colorLabel3,
						[4] = properties.colorLabel4,
						[5] = properties.colorLabel5,
					}
				end
			end
		end )
		
		LrController.addActivePhotoChangeObserver( context, attribute_properties, function( properties )
			loadAttributes( properties )
		end )
		
		LrDevelopController.revealAdjustedControls( true )
		
		local function makeDevelopToolButton( title, tool )
			return f:push_button {
				title = title,
				action = function()
					LrDevelopController.selectTool( tool )
				end,
				shared = { width = "develop_button_width" },
			}
		end

		local function makeDevelopCommandButton( title, action )

			if not title then -- blank space
				return f:push_button {
					title = "",
					visible = false,
					shared = { width = "develop_button_width" },
				}
			end
		
			return f:push_button {
				title = title,
				action = action,
				size = "small",
				shared = { width = "develop_button_width" },
			}
		end
		
		LrDialogs.presentFloatingDialog( _PLUGIN, {
			title = "Demo",
			save_frame = "Slider_Control_Demo",
			blockTask = true,
			
			contents = f:column {
				fill = 1,
				spacing = 20,
				margin = 10,

				f:group_box {
					title = "Zoom",
					fill_horizontal = 1,
					spacing = 20,

					f:row {
						f:push_button { title = "Zoom In", action = LrController.zoomIn },
						f:push_button { title = "Zoom Out", action = LrController.zoomOut },
						f:push_button { title = "Zoom In Some", action = LrController.zoomInSome },
						f:push_button { title = "Zoom Out Some", action = LrController.zoomOutSome },
						f:push_button { title = "Toggle Zoom", action = LrController.toggleZoom },
					},
				},

				f:group_box {
					title = "Attributes",
					fill_horizontal = 1,
					spacing = 20,
					bind_to_object = attribute_properties,

					f:row {
						spacing = 10,

						f:static_text {
							title = "Rating",
							alignment = "right",
							shared = { width = "label_width" },
						},
						
						f:slider {
							width = 120,
							min = 0,
							max = 5,
							integral = true,
							value = bind "rating",
						},
						
						f:static_text {
							width_in_digits = 2,
							title = bind "rating",
						},
					},

					f:row {
						spacing = 10,

						f:static_text {
							title = "Flag",
							alignment = "right",
							shared = { width = "label_width" },
						},
						
						f:radio_button {
							title = "Reject",
							checked_value = -1,
							value = bind "flag",
						},
						f:radio_button {
							title = "Unflagged",
							checked_value = 0,
							value = bind "flag",
						},
						f:radio_button {
							title = "Pick",
							checked_value = 1,
							value = bind "flag",
						},
					},

					f:row {
						spacing = 10,

						f:static_text {
							title = "Color Label",
							alignment = "right",
							shared = { width = "label_width" },
						},
												
						f:push_button {
							title = "Red",
							action = LrController.toggleRedLabel,
						},
						f:push_button {
							title = "Yellow",
							action = LrController.toggleYellowLabel,
						},
						f:push_button {
							title = "Green",
							action = LrController.toggleGreenLabel,
						},
						f:push_button {
							title = "Blue",
							action = LrController.toggleBlueLabel,
						},
						f:push_button {
							title = "Purple",
							action = LrController.togglePurpleLabel,
						},
						f:push_button {
							title = "Clear All",
							action = LrController.clearLabels,
						},
					},
				},
				
				f:group_box {
					title = "Develop Tools",
					fill_horizontal = 1,
					place = "vertical",
					
					f:row {
						spacing = 10,
						
						makeDevelopToolButton( "Loupe", "loupe" ),
						makeDevelopToolButton( "Crop", "crop" ),
						makeDevelopToolButton( "Dust", "dust" ),
						makeDevelopToolButton( "Redeye", "redeye" ),
						makeDevelopToolButton( "Grad.", "gradient" ),
						makeDevelopToolButton( "Radial", "circularGradient" ),
						makeDevelopToolButton( "Brush", "localized" ),
					},

					f:row {
						spacing = 10,
					
						makeDevelopCommandButton(),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetCrop ),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetSpotRemoval ),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetRedeye ),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetGradient ),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetCircularGradient ),
						makeDevelopCommandButton( "Reset", LrDevelopController.resetBrushing ),
					},
				},

				f:scrolled_view {
					fill = 1,
					height = 400,
					width = 520,
					
					document_ivew = f:group_box {
						auto_resize = "width",
						auto_layout = true,
						title = "Develop Adjustments",
						fill_horizontal = 1,
						spacing = 10,
						bind_to_object = develop_properties,

						makeAdjustmentRow( "Crop Angle", "straightenAngle", 2 ),

						sep(),

						f:static_text {
							title = "Localized Adjustments",
							alignment = "right",
							shared = { width = "label_width" },
						},

						makeAdjustmentRow( "Exposure", "local_Exposure", 2 ),
						makeAdjustmentRow( "Contrast", "local_Contrast" ),
						makeAdjustmentRow( "Highlights", "local_Highlights" ),
						makeAdjustmentRow( "Shadows", "local_Shadows" ),
						makeAdjustmentRow( "Clarity", "local_Clarity" ),
						makeAdjustmentRow( "Saturation", "local_Saturation" ),

						sep(),

						makeAdjustmentRow( "Temp", "Temperature" ),
						makeAdjustmentRow( "Tint", "Tint" ),

						sep(),

						makeAdjustmentRow( "Exposure", "Exposure" ),
						makeAdjustmentRow( "Contrast", "Contrast" ),
						
						sep(),
			
						makeAdjustmentRow( "Highlights", "Highlights" ),
						makeAdjustmentRow( "Shadows", "Shadows" ),

						sep(),

						makeAdjustmentRow( "Whites", "Whites" ),
						makeAdjustmentRow( "Blacks", "Blacks" ),

						sep(),

						makeAdjustmentRow( "Clarity", "Clarity" ),
						makeAdjustmentRow( "Vibrance", "Vibrance" ),
						makeAdjustmentRow( "Saturation", "Saturation" ),

						sep(),

						f:static_text {
							title = "Mixer",
							alignment = "right",
							shared = { width = "label_width" },
						},

						makeAdjustmentRow( "Red Hue", "HueAdjustmentRed" ),
						makeAdjustmentRow( "Red Luminance", "LuminanceAdjustmentRed" ),
						makeAdjustmentRow( "Red Saturation", "SaturationAdjustmentRed" ),

						makeAdjustmentRow( "Orange Hue", "HueAdjustmentOrange" ),
						makeAdjustmentRow( "Orange Luminance", "LuminanceAdjustmentOrange" ),
						makeAdjustmentRow( "Orange Saturation", "SaturationAdjustmentOrange" ),

						sep(),

						makeAdjustmentRow( "Gray Red", "GrayMixerRed" ),
						makeAdjustmentRow( "Gray Orange", "GrayMixerOrange" ),

						sep(),

						f:static_text {
							title = "Tone Curve",
							alignment = "right",
							shared = { width = "label_width" },
						},

						makeAdjustmentRow( "Highlights", "ParametricHighlights" ),
						makeAdjustmentRow( "Lights", "ParametricLights" ),
						makeAdjustmentRow( "Darks", "ParametricDarks" ),
						makeAdjustmentRow( "Shadows", "ParametricShadows" ),

						f:row {}, -- spacer

						makeAdjustmentRow( "Highlight Split", "ParametricHighlightSplit" ),
						makeAdjustmentRow( "Midtone Split", "ParametricMidtoneSplit" ),
						makeAdjustmentRow( "Shadow Split", "ParametricShadowSplit" ),

					},
				},

				f:column {
					place_horizontal = 0.5,

					f:row {

						f:push_button {
							title = "Undo",
							size = "small",
							action = LrController.undo,
							shared = { width = "button_width" },
						},
						f:push_button {
							title = "Redo",
							size = "small",
							action = LrController.redo,
							shared = { width = "button_width" },
						},
						f:push_button {
							title = "Reset All",
							size = "small",
							action = LrDevelopController.resetAllDevelopAdjustments,
							shared = { width = "button_width" },
							place_horizontal = 1,
						},
					},
				},

				f:column {
					place_horizontal = 0.5,

					f:row {

						f:push_button {
							title = "< Previous Photo",
							size = "small",
							action = LrController.previousPhoto,
							shared = { width = "button_width" },
							place_horizontal = 0.5,
						},
						f:push_button {
							title = "Next Photo >",
							size = "small",
							action = LrController.nextPhoto,
							shared = { width = "button_width" },
							place_horizontal = 0.5,
						},
					},
				},
			},

			onShow = function()
				-- initial setup (wait until the view is constructed so allParams can be populated)
				loadSettings( develop_properties )
				loadAttributes( attribute_properties )
			end,
			
			windowWillClose = function()
				-- (TODO: anything that needs to be done when the window closes)
			end,
		} )
		
	end )

end )
