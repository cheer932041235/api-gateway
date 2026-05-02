Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """" & Replace(WScript.ScriptFullName, "start-proxy.vbs", "proxy-loop.bat") & """", 0, False
' Note: start-proxy.vbs and proxy-loop.bat must be in the same directory (scripts/)
