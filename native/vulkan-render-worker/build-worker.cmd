@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b %errorlevel%
set "CMAKE_EXE=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if not defined VULKAN_SDK set "VULKAN_SDK=C:\VulkanSDK\1.4.350.0"
set "PATH=%VULKAN_SDK%\Bin;%PATH%"
"%CMAKE_EXE%" -S "%~dp0." -B "%~dp0build" -G Ninja -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b %errorlevel%
"%CMAKE_EXE%" --build "%~dp0build" --config Release
exit /b %errorlevel%
