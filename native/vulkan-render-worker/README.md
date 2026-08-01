# Sovereign X Vulkan Worker

Windows native Vulkan execution worker for the Sovereign X JSON job/receipt protocol.
It selects a compute-capable physical device, creates one device and compute pipeline per
movie job, reuses them for every frame, and emits a SHA-256-bound multi-frame receipt.

The worker consumes the hashed Scene4D mesh contract and retains color, atomic-depth, vertex,
and triangle-index storage buffers in the resident Vulkan process. `frame.comp` performs SO(4)
transformation, 4D→3D→2D projection, barycentric triangle coverage, atomic depth testing, and
lit W-depth shading on the GPU. It checks governed cancellation between frames and emits one
PPM plus a live daemon frame event per completed frame.

Build with a C++20 compiler and Vulkan SDK:

```powershell
./build-worker.cmd

# Or manually:
cmake -S . -B build
cmake --build build --config Release
```

Configure the resulting executable as the `SovereignXNativeWorkerOptions.executable`.

Pass `--daemon` to keep the Vulkan instance, device, pipeline, descriptors, command pool,
and reusable 8K frame buffer resident across newline-delimited `{jobPath,receiptPath}` commands.
The router's `SovereignXNativeRenderDaemon` owns this protocol and serializes jobs safely.

Run `./validate-native.ps1` to render all five surfaces on the selected Vulkan device, verify
distinct frame hashes and complete multi-frame receipts, and cancel a live render process.
Run `./validate-resident.ps1` to prove two unrelated jobs complete through one native PID.

`sovereignx-adl-telemetry.exe` reads temperature, utilization, clocks, and voltage directly
from AMD ADL. Configure its path as `amdAdlExecutable` when calling `routeWithLiveGpuTelemetry`;
malformed, unbounded, incomplete, or explicitly untrusted samples are rejected fail-closed.

The router's `encodeNativeFrames` sends the numbered PPM sequence to FFmpeg through a bounded
argument array and selects `h264_amf`, `hevc_amf`, or `av1_amf`. H.264 AMF output is validated
on the local Radeon R9 380 in `smoke-output/vulkan-mesh-amf.mp4`.

Set a job's `sharedFramePath` to enable the double-buffered SXFR v1 presentation ring. Each
slot contains tightly packed RGBA8 pixels and the 32-byte header publishes dimensions, stride,
frame sequence, active slot, and slot length only after the slot is flushed. Resident frame
events include this path. Standard browsers consume the compact active-slot endpoint through
`SharedFramePreview`; a native/Electron host may replace its reader with memory mapping.

## Hardware encoding

FFmpeg 8.1.2 with AMD AMF was validated on this host. A 640x480 Vulkan-generated PPM frame
was encoded through `h264_amf` into `smoke-output/vulkan-frame-amf.mp4`. Encoder discovery
must still be followed by a real encode probe; listing an encoder does not prove driver support.
