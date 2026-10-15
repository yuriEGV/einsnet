import os
import subprocess

app_dir = r"C:\Users\maritimo13\Desktop\conexiones"
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
startup = os.path.join(os.environ['APPDATA'], r"Microsoft\Windows\Start Menu\Programs\Startup")
ico_path = os.path.join(app_dir, 'netguard.ico')
bat_launcher = os.path.join(app_dir, 'Levantar_Servidor.bat')
py_script = os.path.join(app_dir, 'supervisor_einsnet.py')
pythonw = r"C:\Python313\pythonw.exe"

ps_code = f"""
$WshShell = New-Object -ComObject WScript.Shell

# 1. Icono principal dentro de la carpeta 'conexiones'
$lnk1 = $WshShell.CreateShortcut("{app_dir}\\Levantar Servidor EinsNet.lnk")
$lnk1.TargetPath = "{bat_launcher}"
$lnk1.WorkingDirectory = "{app_dir}"
$lnk1.IconLocation = "{ico_path}, 0"
$lnk1.Description = "Levanta el Servidor EinsNet y asegura su auto-reinicio si se cae"
$lnk1.Save()

# 2. Icono secundario en 'conexiones' para Abrir EinsNet
$lnk2 = $WshShell.CreateShortcut("{app_dir}\\Abrir EinsNet.lnk")
$lnk2.TargetPath = "{bat_launcher}"
$lnk2.WorkingDirectory = "{app_dir}"
$lnk2.IconLocation = "{ico_path}, 0"
$lnk2.Description = "EinsNet Monitor LAN"
$lnk2.Save()

# 3. Icono en el Escritorio (Desktop)
$lnk3 = $WshShell.CreateShortcut("{desktop}\\EinsNet.lnk")
$lnk3.TargetPath = "{bat_launcher}"
$lnk3.WorkingDirectory = "{app_dir}"
$lnk3.IconLocation = "{ico_path}, 0"
$lnk3.Description = "EinsNet - Monitor y Control Total de Red LAN"
$lnk3.Save()

# 4. Acceso en Inicio de Windows (Startup) para auto-inicio silencioso al encender el PC
$lnk4 = $WshShell.CreateShortcut("{startup}\\EinsNet_Supervisor.lnk")
$lnk4.TargetPath = "{pythonw}"
$lnk4.Arguments = '"{py_script}" --daemon'
$lnk4.WorkingDirectory = "{app_dir}"
$lnk4.IconLocation = "{ico_path}, 0"
$lnk4.Description = "EinsNet Guardián en Segundo Plano"
$lnk4.WindowStyle = 7
$lnk4.Save()

Write-Output "[OK] Accesos directos e iconos generados exitosamente."
"""

ps_file = os.path.join(app_dir, 'create_shortcuts.ps1')
with open(ps_file, 'w', encoding='utf-8') as f:
    f.write(ps_code)

res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file], capture_output=True, text=True)
print("Salida PowerShell:", res.stdout, res.stderr)

if os.path.exists(ps_file):
    os.remove(ps_file)
