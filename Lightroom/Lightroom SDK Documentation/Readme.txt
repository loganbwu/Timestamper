Welcome to the Adobe Lightroom Classic 14.3 Software Development Kit
(Build: "202504141032-10373aad")
_____________________________________________________________________________

This file contains the latest information for the Adobe Lightroom Classic SDK (14.3 Release).
The information applies to Adobe Lightroom Classic and includes the following sections:

1. Introduction
2. SDK content overview
3. Development environment
4. Sample plug-ins
5. Running the plug-ins
6. Adobe Add-ons

**********************************************
1. Introduction
**********************************************

The SDK provides information and examples for the scripting interface to Adobe
Lightroom Classic. The SDK defines a scripting interface for the Lua language.

A number of new features have been added in the 14.3 SDK release.
Please see the API Reference for more information.

**********************************************
2. SDK content overview
**********************************************

The SDK contents include the following:

- <sdkInstall>/Manual/Lightroom Classic SDK Guide.pdf:
	Describes the SDK and how to extend the functionality of
	Adobe Lightroom Classic.

- <sdkInstall>/API Reference/:
	The Scripting API reference in HTML format. Start at index.html.

- <sdkInstall>/Sample Plugins:
	Sample plug-ins and demonstration code (see section 4).

**********************************************
3. Development environment
**********************************************

You can use any text editor to write your Lua scripts, and you can
use the LrLogger namespace to write debugging information to a console.
See the section on "Debugging your Plug-in" in the Lightroom Classic SDK Guide.

**********************************************
4. Sample Plugins
**********************************************

The SDK provides the following samples:

- <sdkInstall>/Sample Plugins/flickr.lrdevplugin/:
	Sample plug-in that demonstrates creating a plug-in which allows
	images to be directly exported to a Flickr account.

- <sdkInstall>/Sample Plugins/ftp_upload.lrdevplugin/:
	Sample plug-in that demonstrates how to export images to an FTP server.

- <sdkInstall>/Sample Plugins/helloworld.lrdevplugin/:
	Sample code that accompanies the Getting Started section of the
	Lightroom Classic SDK Guide.

  <sdkInstall>/Sample Plugins/custommetadatasample.lrdevplugin/:
	Sample code that accompanies the custommetadatasample plug-in that
	demonstrates custom metadata.

- <sdkInstall>/Sample Plugins/metaexportfilter.lrdevplugin/:
	Sample code that demonstrates using the metadata stored in a file
	to filter the files exported via the export dialog.

- <sdkInstall>/Sample Plugins/websample.lrwebengine/:
	Sample code that creates a new style of web gallery template
	using the Web SDK.

**********************************************
5. Running the plug-ins
**********************************************

To run the sample code, load the plug-ins using the Plug-in Manager
available within Lightroom. See the Lightroom Classic SDK Guide for more information.

*********************************************************
6. Adobe Add-ons
*********************************************************

To learn more about Adobe Add-ons, point your browser to:

  https://creative.adobe.com/addons

_____________________________________________________________________________

© 2007-2025 Adobe. All rights reserved.

Adobe, the Adobe logo, Lightroom, and Photoshop are registered trademarks or trademarks of
Adobe in the United States and/or other countries.
Windows is either a registered trademark or a trademark of Microsoft Corporation
in the United States and/or other countries. Macintosh is a trademark of
Apple Inc., registered in the United States and  other countries.

_____________________________________________________________________________
