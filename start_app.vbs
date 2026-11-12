Option Explicit
Dim shell, fso, root, python, entry
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
entry = root & "\launcher.pyw"
If Not fso.FileExists(python) Then
  MsgBox "Please follow the setup steps in README.md first.", 48, "Blog checker"
  WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & entry & Chr(34), 0, False
