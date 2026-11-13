using System;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Text;
using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using System.Threading;
using System.Windows.Forms;
using System.Drawing;

class Setup : Form {
    const string PyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip";
    const string PyHash = "009d6bf7e3b2ddca3d784fa09f90fe54336d5b60f0e0f305c37f400bf83cfd3b";
    const string PipUrl = "https://files.pythonhosted.org/packages/44/3c/d717024885424591d5376220b5e836c2d5293ce2011523c9de23ff7bf068/pip-25.3-py3-none-any.whl";
    const string PipHash = "9655943313a94722b7774661c21049070f6bbb0a1516bf02f7c8d5d9201514cd";
    string root; bool busy, done; TextBox output; Button install; StreamWriter log;
    static string Q(string s) { return "\"" + s + "\""; }
    public Setup(string target) {
        root = Path.GetFullPath(target);
        Text = "Blog Similarity Checker 설치"; ClientSize = new Size(660, 440);
        Font = new Font("맑은 고딕", 10); StartPosition = FormStartPosition.CenterScreen;
        var intro = new Label { Left=20, Top=20, Width=620, Height=95,
            Text="블로그 유사도 검사 자동 설치\n전용 Python · 라이브러리 · AI 모델 준비 후 바탕화면 아이콘 생성\n첫 설치: 인터넷 필요 / 수 GB 여유 공간 권장 / 다운로드에 수 분 이상 소요" };
        output = new TextBox { Left=20, Top=120, Width=620, Height=240, Multiline=true, ReadOnly=true, ScrollBars=ScrollBars.Vertical };
        output.Text="설치 위치: " + root + "\r\n개인 자료는 유지되며, 기존 Python 설정은 변경하지 않습니다.";
        install = new Button { Left=440, Top=380, Width=200, Height=40, Text="설치 시작" };
        install.Click += delegate {
            if(done) { Process.Start(new ProcessStartInfo(Path.Combine(root,"runtime","pythonw.exe"), Q(Path.Combine(root,"launcher.pyw"))) { WorkingDirectory=root, UseShellExecute=false, CreateNoWindow=true }); Close(); return; }
            busy=true; install.Enabled=false;
            new Thread(delegate() { try { Install(true); Invoke((Action)delegate { done=true; busy=false; install.Enabled=true; install.Text="검사기 실행"; }); }
                catch(Exception ex) { Say("설치 실패: " + ex.Message); Invoke((Action)delegate { busy=false; install.Enabled=true; install.Text="다시 시도"; }); }
            }) { IsBackground=true }.Start();
        };
        FormClosing += delegate(object sender, FormClosingEventArgs e) { if(busy) { e.Cancel=true; MessageBox.Show("설치가 진행 중입니다. 완료 또는 오류 안내 후 닫아 주세요."); } };
        Controls.AddRange(new Control[] {intro,output,install});
    }
    void Say(string s) {
        if(String.IsNullOrWhiteSpace(s)) return;
        lock(this) { if(log!=null) { log.WriteLine(s); log.Flush(); } }
        if(IsHandleCreated) BeginInvoke((Action)delegate { if(output.TextLength>40000) output.Text=output.Text.Substring(output.TextLength-20000); output.AppendText("\r\n"+s); });
    }
    void Run(string file, string args) {
        var info=new ProcessStartInfo(file,args) { WorkingDirectory=root, UseShellExecute=false, CreateNoWindow=true, RedirectStandardOutput=true, RedirectStandardError=true };
        info.EnvironmentVariables["PYTHONUTF8"]="1";
        info.EnvironmentVariables["HF_HOME"]=Path.Combine(root,"data","models");
        info.EnvironmentVariables["PIP_DISABLE_PIP_VERSION_CHECK"]="1";
        using(var p=new Process { StartInfo=info }) {
            p.OutputDataReceived += (s,e)=>Say(e.Data); p.ErrorDataReceived += (s,e)=>Say(e.Data);
            p.Start(); p.BeginOutputReadLine(); p.BeginErrorReadLine(); p.WaitForExit();
            if(p.ExitCode!=0) throw new Exception("준비 단계 실패 (코드 " + p.ExitCode + "). 인터넷 연결과 data/install.log를 확인해 주세요.");
        }
    }
    static void Extract(Stream stream, string target) {
        string prefix=Path.GetFullPath(target).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        Directory.CreateDirectory(target);
        using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)) foreach(var entry in zip.Entries) {
            string path=Path.GetFullPath(Path.Combine(target,entry.FullName));
            if(!path.StartsWith(prefix,StringComparison.OrdinalIgnoreCase)) throw new Exception("잘못된 압축 경로");
            if(entry.Name.Length==0) { Directory.CreateDirectory(path); continue; }
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            using(var src=entry.Open()) using(var dst=File.Create(path)) src.CopyTo(dst);
        }
    }
    void Download(string url,string hash,string destination) {
        Say("공식 배포처 다운로드: " + new Uri(url).Host);
        using(var client=new WebClient()) client.DownloadFile(url,destination);
        using(var sha=SHA256.Create()) using(var f=File.OpenRead(destination)) {
            string actual=BitConverter.ToString(sha.ComputeHash(f)).Replace("-","").ToLowerInvariant();
            if(actual!=hash) throw new Exception("다운로드 검증 실패. 다시 설치해 주세요.");
        }
    }
    void Shortcut(string directory) {
        Directory.CreateDirectory(directory);
        Type type=Type.GetTypeFromProgID("WScript.Shell"); object shell=Activator.CreateInstance(type);
        object link=type.InvokeMember("CreateShortcut",BindingFlags.InvokeMethod,null,shell,new object[]{Path.Combine(directory,"Blog Similarity Checker.lnk")});
        Type t=link.GetType();
        foreach(var pair in new string[][] {new[]{"TargetPath",Path.Combine(root,"runtime","pythonw.exe")},new[]{"Arguments",Q(Path.Combine(root,"launcher.pyw"))},new[]{"WorkingDirectory",root},new[]{"IconLocation",Path.Combine(root,"assets","blog-check.ico")}})
            t.InvokeMember(pair[0],BindingFlags.SetProperty,null,link,new object[]{pair[1]});
        t.InvokeMember("Save",BindingFlags.InvokeMethod,null,link,null);
    }
    void Install(bool shortcuts) {
        if(!Environment.Is64BitOperatingSystem) throw new Exception("64비트 Windows가 필요합니다.");
        if(Environment.GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")=="ARM64") throw new Exception("현재 설치판은 Intel/AMD 64비트 Windows용입니다.");
        // Do not replace files while either managed local instance is running.
        if(File.Exists(Path.Combine(root,"data","runtime","launcher.json")))
            foreach(int port in new[]{18765,18766}) { using(var tcp=new System.Net.Sockets.TcpClient()) { try { tcp.Connect("127.0.0.1",port); } catch(System.Net.Sockets.SocketException) { continue; } throw new Exception("실행 중인 검사기를 종료한 뒤 다시 설치해 주세요."); } }
        Directory.CreateDirectory(Path.Combine(root,"data"));
        log=new StreamWriter(Path.Combine(root,"data","install.log"),true,Encoding.UTF8);
        try {
            ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
            Say("1/5 프로그램 파일 준비");
            using(var payload=Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip")) Extract(payload,root);
            string runtime=Path.Combine(root,"runtime"), python=Path.Combine(runtime,"python.exe");
            Say("2/5 전용 Python 준비");
            string download=Path.Combine(root,"data","runtime-download.zip");
            if(!File.Exists(Path.Combine(runtime,"runtime-ready"))) {
                Download(PyUrl,PyHash,download); using(var f=File.OpenRead(download)) Extract(f,runtime);
                File.WriteAllText(Path.Combine(runtime,"python311._pth"),"python311.zip\n.\n..\nLib\\site-packages\nimport site\n");
                Download(PipUrl,PipHash,download); using(var f=File.OpenRead(download)) Extract(f,Path.Combine(runtime,"Lib","site-packages"));
                Run(python,"-m pip --version"); File.WriteAllText(Path.Combine(runtime,"runtime-ready"),PyHash);
                File.Delete(download);
            }
            Say("3/5 라이브러리 설치 (첫 설치는 시간이 걸릴 수 있습니다)");
            Run(python,"-m pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu torch==2.15.0");
            Run(python,"-m pip install --only-binary=:all: --index-url https://pypi.org/simple -r " + Q(Path.Combine(root,"requirements.txt")));
            Run(python,"-m pip check");
            Say("4/5 AI 모델 다운로드 및 예시 문장 확인");
            Run(python,Q(Path.Combine(root,"installer","prepare_model.py")));
            Say("5/5 설치 완료 준비");
            if(shortcuts) { Shortcut(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory)); Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs),"Blog Similarity Checker")); }
            File.WriteAllText(Path.Combine(root,"data","installation.json"),"{\"version\":\"1.1.0\",\"complete\":true}");
            Say("설치 완료! 샘플 글 3개로 검사기를 체험할 수 있습니다.");
        } finally { lock(this) { log.Dispose(); log=null; } }
    }
    [STAThread] static int Main(string[] args) {
        string target=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BlogSimilarityChecker");
        bool quiet=false,shortcuts=true;
        for(int i=0;i<args.Length;i++) { if(args[i]=="--install-dir") target=args[++i]; else if(args[i]=="--quiet") quiet=true; else if(args[i]=="--no-shortcuts") shortcuts=false; else return 2; }
        using(var mutex=new Mutex(false,"Local\\BlogSimilarityCheckerSetup")) {
            if(!mutex.WaitOne(0)) { if(!quiet) MessageBox.Show("설치 프로그램이 이미 실행 중입니다."); return 3; }
            try { Application.EnableVisualStyles(); var form=new Setup(target); if(quiet) { try { form.Install(shortcuts); return 0; } catch(Exception e) { File.WriteAllText(Path.Combine(Path.GetTempPath(),"BlogSimilarityChecker-setup-error.txt"),e.ToString()); return 1; } } Application.Run(form); return form.done ? 0 : 1; }
            finally { mutex.ReleaseMutex(); }
        }
    }
}
