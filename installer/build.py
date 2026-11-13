from pathlib import Path
import subprocess, zipfile, hashlib
root=Path(__file__).resolve().parents[1]
out=root/'dist'
out.mkdir(exist_ok=True)
files=['app.py','app_controls.py','body_check.py','data_source.py','design.py','import_backup.py','launcher.pyw','post_manager.py','requirements.txt','sample_data/posts.json','assets/blog-check.png','assets/blog-check.ico','.streamlit/config.toml','installer/prepare_model.py']
with zipfile.ZipFile(out/'payload.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in files: z.write(root/name,name)
exe=out/'BlogSimilarityChecker-Setup.exe'
subprocess.run([r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/target:winexe','/platform:x64','/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.IO.Compression.dll','/reference:System.IO.Compression.FileSystem.dll','/win32icon:'+str(root/'assets/blog-check.ico'),'/resource:'+str(out/'payload.zip')+',payload.zip','/out:'+str(exe),str(root/'installer/Setup.cs')],check=True)
(out/'SHA256SUMS.txt').write_text(hashlib.sha256(exe.read_bytes()).hexdigest()+'  '+exe.name+'\n',encoding='ascii')
print(exe)
