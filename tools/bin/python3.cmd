@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem GNU Make on Windows often runs with a minimal PATH. Resolve Python explicitly.
where py >nul 2>nul
if !ERRORLEVEL! equ 0 (
  py -3 %*
  exit /b !ERRORLEVEL!
)

where python >nul 2>nul
if !ERRORLEVEL! equ 0 (
  python %*
  exit /b !ERRORLEVEL!
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" %*
  exit /b !ERRORLEVEL!
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" %*
  exit /b !ERRORLEVEL!
)

if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" %*
  exit /b !ERRORLEVEL!
)

echo python3 shim: no Python installation found 1>&2
exit /b 1
