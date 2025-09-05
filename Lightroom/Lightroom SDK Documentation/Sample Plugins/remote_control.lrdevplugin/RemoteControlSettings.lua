
local LrDialogs = import "LrDialogs"
local LrView = import "LrView"
local LrPrefs = import 'LrPrefs'
local bind = LrView.bind
local f = LrView.osFactory()
local prefs = LrPrefs and LrPrefs.prefsForPlugin()

--------------------------------------------------------------------------------

local kPermissions = {
	allowViewPhotos = true,
	allowSwitchPhotos = false,
	allowControlSlideshow = false,
	allowSwitchViewModes = false,
	allowTriggerCapture = false,
	allowEditKeywords = false,
}

--------------------------------------------------------------------------------

local function initIfNil( key, default )
	if prefs[ key ] == nil then
		prefs[ key ] = default
	end
end

local kPermissionKeys = {}

for key, default in pairs( kPermissions ) do
	table.insert( kPermissionKeys, key )
	initIfNil( key, default )
end
initIfNil( "showHeader", true )

--------------------------------------------------------------------------------

local kPresets = {
	{ title = "View Only", value = { "allowViewPhotos" }, },
	{ title = "Review Photos", value = { "allowViewPhotos", "allowSwitchPhotos" }, },
	{ title = "Slideshow Remote", value = { "allowViewPhotos", "allowSwitchPhotos", "allowControlSlideshow", } },
	{ title = "Tether Trigger", value = { "allowViewPhotos", "allowSwitchPhotos", "allowTriggerCapture" } },
	{ title = "Keyword Grid", value = { "allowEditKeywords", "allowSwitchPhotos" } },
	{ title = "Full Control", value = kPermissionKeys },
}

--------------------------------------------------------------------------------

local function presetsEqual( value1, value2 )

	if value1 == "<custom>" and value2 == "<custom>" then
		return true
	end
	if type( value1 ) ~= type( value2 ) or type( value1 ) ~= "table" then
		return false
	end
	if #value1 ~= #value2 then
		return false
	end
	local set1 = {}
	for _, key in ipairs( value1 ) do
		set1[ key ] = true
	end
	for _, key in ipairs( value2 ) do
		if not set1[ key ] then
			return false
		end
		set1[ key ] = nil
	end
	if next( set1 ) then
		return false
	end
	return true
end

local presetItems = {}

for _, item in ipairs( kPresets ) do
	table.insert( presetItems, item )
end

table.insert( presetItems, { separator = true } )
table.insert( presetItems, { title = "Custom", value = "<custom>" } )

--------------------------------------------------------------------------------

LrDialogs.presentModalDialog {
	title = "Remote Control Settings",

	contents = f:view {
		bind_to_object = prefs,
		spacing = f:dialog_spacing(),

		f:group_box {
			title = "Client Permissions",
	
			f:row {
				spacing = f:label_spacing(),

				--f:static_text { title = "Preset:"},
				
				f:popup_menu {
					fill_horizontal = 1,
					value = bind {
						keys = kPermissionKeys,
						operation = function( binder, values, fromModel )
							if fromModel then
								local value = {}
								for _, key in ipairs( kPermissionKeys ) do
									if values[ key ] then
										table.insert( value, key )
									end
								end
								local matchesPreset = false
								for _, preset in ipairs( kPresets ) do
									if presetsEqual( value, preset.value ) then
										matchesPreset = true
										break
									end
								end
								return matchesPreset and value or "<custom>"
							else
								local unset = table.shallowcopy( kPermissions )
								for _, key in ipairs( values.value or {} ) do
									values[ key ] = true
									unset[ key ] = nil
								end
								for key, _ in pairs( unset ) do
									values[ key ] = false
								end
							end
						end,
					},
					value_equal = presetsEqual,
					items = presetItems,
				},
			},

			f:view {
				title = "Permissions",
				margin_left = 24,
				spacing = f:label_spacing(),

				f:checkbox {
					title = "View Photos",
					value = bind "allowViewPhotos",
				},

				f:checkbox {
					title = "Switch Photos",
					value = bind "allowSwitchPhotos",
				},

				f:checkbox {
					title = "Switch View Modes",
					value = bind "allowSwitchViewModes",
				},

				f:checkbox {
					title = "Trigger Tethered Captures",
					value = bind "allowTriggerCapture",
				},

				f:checkbox {
					title = "Start Slideshow",
					value = bind "allowControlSlideshow",
				},
				
				f:checkbox {
					title = "Edit Keywords",
					value = bind "allowEditKeywords",
				},
			},
		},

		f:row {
			margin_left = 10,
			f:checkbox {
				title = "Show Header",
				value = bind "showHeader",
			},
		},
	},
}
