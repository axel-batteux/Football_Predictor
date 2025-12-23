Set WshShell = CreateObject("WScript.Shell")
' Change ce chemin si necessaire
WshShell.CurrentDirectory = "C:\Users\axelp\.gemini\antigravity\playground\axial-cosmic"
WshShell.Run "python auto_update.py", 0, False
Set WshShell = Nothing
