import os
import subprocess

desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
app_dir = r'C:\Users\maritimo13\Desktop\conexiones'
ico_path = os.path.join(app_dir, 'netguard.ico')
bat_launcher = os.path.join(app_dir, 'Abrir_EinsNet.bat')

ps_code = f"""
$WshShell = New-Object -ComObject WScript.Shell
$lnk = $WshShell.CreateShortcut("{desktop}\\EinsNet.lnk")
$lnk.TargetPath = "{bat_launcher}"
$lnk.WorkingDirectory = "{app_dir}"
$lnk.IconLocation = "{ico_path}, 0"
$lnk.Description = "EinsNet - Monitor y Control Total de Red LAN"
$lnk.Save()
"""

ps_file = os.path.join(app_dir, 'temp_lnk.ps1')
with open(ps_file, 'w', encoding='utf-8') as f:
    f.write(ps_code)

res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file], capture_output=True, text=True)
print("PS result:", res.stdout, res.stderr)

if os.path.exists(ps_file):
    os.remove(ps_file)

# URL shortcut on Desktop
url_file = os.path.join(desktop, 'EinsNet - Monitor de Red.url')
with open(url_file, 'w', encoding='utf-8') as f:
    f.write("[InternetShortcut]\n")
    f.write("URL=http://localhost:8000\n")
    f.write(f"IconFile={ico_path}\n")
    f.write("IconIndex=0\n")

# Iniciar EinsNet.bat on Desktop
bat_desktop = os.path.join(desktop, 'Iniciar EinsNet.bat')
with open(bat_desktop, 'w', encoding='utf-8') as f:
    f.write(f'@echo off\r\ncall "{bat_launcher}"\r\nexit\r\n')

print("EinsNet Shortcuts successfully created on Desktop!")
