' API Gateway Proxy 启动脚本（防重复启动）
Set WshShell = CreateObject("WScript.Shell")

' 检查 8082 端口是否已被占用
Set oExec = WshShell.Exec("cmd /c netstat -ano | findstr ""LISTENING"" | findstr "":8082 """)
strOutput = ""
Do While Not oExec.StdOut.AtEndOfStream
    strOutput = strOutput & oExec.StdOut.ReadLine()
Loop

If Len(strOutput) > 0 Then
    MsgBox "API Gateway 代理已在运行中，无需重复启动。", vbInformation, "API Gateway"
    WScript.Quit
End If

' 自动获取脚本所在目录（通用，不硬编码路径）
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 校验 secrets.json 是否存在
If Not fso.FileExists(strDir & "\secrets.json") Then
    MsgBox "找不到 secrets.json 密钥文件！" & vbCrLf & vbCrLf & _
           "请从 secrets.example.json 复制并填入你的 API Key：" & vbCrLf & _
           strDir & "\secrets.json", vbCritical, "API Gateway"
    WScript.Quit
End If

' 启动代理（静默后台运行，带崩溃自动重启 + 日志）
WshShell.CurrentDirectory = strDir
WshShell.Run "cmd /c proxy-loop.bat", 0, False
