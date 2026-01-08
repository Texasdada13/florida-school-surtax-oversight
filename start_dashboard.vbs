Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\dada_\OneDrive\Documents\florida-school-surtax-oversight"
WshShell.Run "pythonw app.py", 0, False
