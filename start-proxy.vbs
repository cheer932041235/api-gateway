Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """" & Replace(WScript.ScriptFullName, "start-proxy.vbs", "proxy-loop.bat") & """", 0, False
