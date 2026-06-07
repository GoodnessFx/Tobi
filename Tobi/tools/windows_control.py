"""Tobi Windows Control Tools: PowerShell-based automation for Windows apps and system."""
import asyncio
import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger("Tobi.tools.windows_control")

# Blocked phrases for safety (prevent accidental shutdown/reboot)
_BLOCKED_POWERSHELL_PHRASES = [
    "stop-computer", "restart-computer", "shutdown /s", "shutdown /r",
]

async def run_powershell(script: str) -> str:
    """Execute a PowerShell command and return the output."""
    script_lower = script.lower()
    for phrase in _BLOCKED_POWERSHELL_PHRASES:
        if phrase in script_lower:
            return f"Error: Command blocked for safety: {phrase}"

    try:
        process = await asyncio.create_subprocess_exec(
            "powershell", "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
        
        if process.returncode != 0:
            return f"Error: {stderr.decode().strip()}"
        return stdout.decode().strip()
    except Exception as e:
        return f"Error: {e}"

async def open_application(app_name: str) -> str:
    """Open a Windows application by name."""
    logger.info("Opening Windows application: %s", app_name)
    # Common mappings
    mapping = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "vscode": "code",
        "visual studio code": "code",
        "notepad": "notepad",
        "calculator": "calc",
        "edge": "msedge",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
    }
    exe_name = mapping.get(app_name.lower(), app_name)
    
    # Try start command
    result = await run_powershell(f"start {exe_name}")
    if result.startswith("Error"):
        # Fallback to direct execution
        return await run_powershell(f"& {exe_name}")
    return f"Attempted to open {app_name}."

async def close_application(app_name: str) -> str:
    """Close a Windows application by name."""
    logger.info("Closing Windows application: %s", app_name)
    # Extract name without .exe
    if app_name.lower().endswith(".exe"):
        app_name = app_name[:-4]
    
    return await run_powershell(f"stop-process -name {app_name} -force -ErrorAction SilentlyContinue")

async def get_running_applications() -> str:
    """List running processes with a window title."""
    script = 'get-process | where {$_.mainWindowTitle} | select-object name, mainWindowTitle | format-table -hidetableheaders | out-string'
    result = await run_powershell(script)
    if result.startswith("Error"):
        return result
    return f"Running applications:\n{result.strip()}"

async def get_frontmost_application() -> str:
    """Get the name of the currently focused window's process."""
    script = """
    $code = @'
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
'@
    Add-Type -TypeDefinition $code -Namespace Win32 -Name User32
    $hwnd = [Win32.User32]::GetForegroundWindow()
    $pid = 0
    [Win32.User32]::GetWindowThreadProcessId($hwnd, [ref]$pid)
    (Get-Process -Id $pid).Name
    """
    return await run_powershell(script)

async def set_volume(level: int) -> str:
    """Set system volume (0-100)."""
    level = max(0, min(100, level))
    # level is 0-100. SendKeys is a hack but works without extra deps.
    # [char]174 is volume down, [char]175 is volume up.
    # Each press changes by 2.
    ps_script = f"""
    $obj = New-Object -ComObject WScript.Shell
    # Mute/Zero first (approximate)
    for($i=0; $i -lt 50; $i++) {{ $obj.SendKeys([char]174) }}
    # Set to desired level
    for($i=0; $i -lt {level/2}; $i++) {{ $obj.SendKeys([char]175) }}
    """
    await run_powershell(ps_script)
    return f"Volume set to approximately {level}%."

async def set_brightness(level: int) -> str:
    """Set screen brightness (0-100)."""
    level = max(0, min(100, level))
    script = f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
    return await run_powershell(script)

async def get_system_info() -> str:
    """Get Windows system information."""
    script = "Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsArchitecture, CsProcessors | Out-String"
    return await run_powershell(script)

async def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    return await run_powershell(f"start '{url}'")

async def open_url_in_browser(url: str, browser: str = "Google Chrome") -> str:
    """Open a URL in a specific browser."""
    # Mapping for common browsers
    mapping = {
        "google chrome": "chrome",
        "firefox": "firefox",
        "microsoft edge": "msedge",
    }
    exe = mapping.get(browser.lower(), browser)
    return await run_powershell(f"start {exe} '{url}'")

async def search_in_browser(query: str, browser: str = "Google Chrome") -> str:
    """Search for a query in the browser."""
    import urllib.parse
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    return await open_url_in_browser(url, browser)

async def open_file(file_path: str) -> str:
    """Open a file with its default application."""
    return await run_powershell(f"start '{file_path}'")

async def get_battery_status() -> str:
    """Get battery percentage and charging status."""
    script = "Get-CimInstance -ClassName Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | Out-String"
    return await run_powershell(script)

async def send_notification(title: str, message: str) -> str:
    """Send a Windows notification."""
    # Escape quotes
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    ps_script = f"""
    [reflection.assembly]::loadwithpartialname('System.Windows.Forms')
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.Visible = $true
    $notify.ShowBalloonTip(5000, '{safe_title}', '{safe_message}', [System.Windows.Forms.ToolTipIcon]::Info)
    """
    await run_powershell(ps_script)
    return f"Notification sent: {title}"

async def get_clipboard() -> str:
    """Get the current clipboard contents."""
    return await run_powershell("Get-Clipboard")

async def set_clipboard(text: str) -> str:
    """Set the clipboard contents."""
    safe_text = text.replace("'", "''")
    return await run_powershell(f"Set-Clipboard -Value '{safe_text}'")

async def paste_to_app() -> str:
    """Simulate Ctrl+V."""
    ps_script = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys('^v')"
    await run_powershell(ps_script)
    return "Pasted content."

async def write_to_app(text: str) -> str:
    """Simulate typing text."""
    safe_text = text.replace("'", "''")
    ps_script = f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys('{safe_text}')"
    await run_powershell(ps_script)
    return f"Typed: {text}"

async def sleep_system() -> str:
    """Put the system to sleep."""
    return await run_powershell("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
