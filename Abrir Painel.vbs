Set WshShell = CreateObject("WScript.Shell")
' O parametro 0 no final esconde a janela completamente
' Executa usando o pythonw do ambiente virtual para garantir dependencias
WshShell.Run ".venv\Scripts\pythonw.exe launcher.pyw", 0, False
Set WshShell = Nothing
