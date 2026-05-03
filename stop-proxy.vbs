' API Gateway Proxy 停止脚本
Set WshShell = CreateObject("WScript.Shell")

' 查找并终止 proxy.py 相关进程
Set oExec = WshShell.Exec("cmd /c netstat -ano | findstr ""LISTENING"" | findstr "":8082 """)
strOutput = ""
Do While Not oExec.StdOut.AtEndOfStream
    strOutput = strOutput & oExec.StdOut.ReadLine()
Loop

If Len(strOutput) = 0 Then
    MsgBox "API Gateway 代理当前未运行。", vbInformation, "API Gateway"
    WScript.Quit
End If

' 终止 proxy-loop.bat 和 python proxy.py 进程
WshShell.Run "cmd /c taskkill /f /fi ""WINDOWTITLE eq API Gateway*"" >nul 2>&1 & " & _
             "for /f ""tokens=5"" %a in ('netstat -ano ^| findstr ""LISTENING"" ^| findstr "":8082 ""') do taskkill /f /pid %a >nul 2>&1 & " & _
             "for /f ""tokens=5"" %a in ('netstat -ano ^| findstr ""LISTENING"" ^| findstr "":8083 ""') do taskkill /f /pid %a >nul 2>&1", 0, True

MsgBox "API Gateway 代理已停止。", vbInformation, "API Gateway"
