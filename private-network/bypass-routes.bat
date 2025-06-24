@echo off
setlocal EnableDelayedExpansion

:: Check for admin privileges
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: This script requires administrative privileges. Please run as Administrator.
    pause
    exit /b 1
)

:: Define the IPs to exclude from the routes
:: You can modify this list as needed
set "EXCLUDE_IPS=216.58.206.0 142.250.0.0 185.192.0.0 142.250.186.110 87.107.144.0 74.125.128.0"

:: Ask user for action (a for add, d for delete, default is add)
echo Enter 'a' to ADD routes or 'd' to DELETE routes (default is ADD):
set /p ACTION=""
if /i "!ACTION!"=="a" goto :add_routes
if /i "!ACTION!"=="d" goto :delete_routes
:: If no input or invalid input, default to add
goto :add_routes

:add_routes
:: Find main gateway
set "MAIN_GATEWAY="
for /f "tokens=2 delims=:" %%a in ('ipconfig /all ^| findstr /I "DHCP Server"') do (
    set "GATEWAY=%%a"
    set "GATEWAY=!GATEWAY: =!"
    if "!GATEWAY:~0,8!"=="192.168." (
        set "MAIN_GATEWAY=!GATEWAY!"
        goto :found_gateway
    )
    if "!GATEWAY:~0,7!"=="172.16." (
        set "MAIN_GATEWAY=!GATEWAY!"
        goto :found_gateway
    )
    if "!GATEWAY:~0,3!"=="10." (
        set "MAIN_GATEWAY=!GATEWAY!"
        goto :found_gateway
    )
)

if "!MAIN_GATEWAY!"=="" (
    echo Error: No gateway provided. Exiting.
    pause
    exit /b 1
)

:found_gateway
echo Using Main Gateway: !MAIN_GATEWAY!

:: Delete existing routes before adding new ones
for %%i in (%EXCLUDE_IPS%) do (
    route DELETE %%i >nul 2>&1
)

:: Add routes
for %%i in (%EXCLUDE_IPS%) do (
    echo Processing %%i
    echo Adding route: route -p ADD %%i MASK 255.255.255.0 !MAIN_GATEWAY!
    route -p ADD %%i MASK 255.255.255.0 !MAIN_GATEWAY! | findstr /C:"OK!" >nul
    if errorlevel 1 (
        echo Failed to add route for %%i
    ) else (
        echo Successfully added route for %%i
    )
)
goto :end

:delete_routes
:: Delete routes
for %%i in (%EXCLUDE_IPS%) do (
    echo Processing %%i
    echo Deleting route: route DELETE %%i MASK 255.255.255.0
    route DELETE %%i MASK 255.255.255.0 | findstr /C:"OK!" >nul
    if errorlevel 1 (
        echo Failed to delete route for %%i
    ) else (
        echo Successfully deleted route for %%i
    )
)

:end
echo Routes processing completed.
pause
endlocal