Broadcast Launcher is a Windows application that automates the startup, monitoring, and operation of a church broadcast system, including vMix, X32, PTZ cameras, ATEM, and operator checklists.

## vMix Zoom and streaming

The launcher finds the Zoom input from the vMix API by input type, so its position can change without updating the configuration. If the vMix project has more than one Zoom input, set `vmix_input_title` on the Zoom app configuration to the exact input title shown by the vMix API. If there is no unique match, the Zoom connection step fails rather than joining through an arbitrary input.

Startup proceeds by opening the configured Zoom meeting, requesting `ZoomJoinMeeting` for the discovered vMix Zoom input, and granting Zoom's livestream permission. After that permission workflow succeeds, the launcher calls vMix's `StartStreaming` API function for all configured streams and waits for the API to report streaming active. Configure the streaming destinations and credentials in vMix before running the launcher. If streaming is already active, the launcher leaves it running.

The Zoom connection and streaming checks are startup checks only. The launcher does not run a background monitor, automatically rejoin Zoom, or restart streaming if either session disconnects after startup. The `vMix streaming started` log means the vMix API reported streaming active at that point; it does not guarantee that the stream or Zoom meeting remains connected later.