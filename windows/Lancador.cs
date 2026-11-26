// iconicpink-blue, parte 2: lançador visual para o Windows.
//
// Abre o jogo pelo programa que você já usa (victory.exe de qualquer fork do
// VIctory, ou o victory-play.exe do DexNom) e cuida só do visual, por fora,
// sem mudar nenhuma linha do fork:
//   - tela de abertura (splash.png), nítida em qualquer escala do Windows,
//     até o jogo começar a desenhar (todos os forks põem "fps" no título da
//     janela nessa hora) ou por no máximo 2 minutos;
//   - ícone (icon.ico) na janela do jogo, na barra de tarefas e no Alt+Tab;
//   - cursor (cursor.cur, opcional) só enquanto a janela do jogo está em foco;
//     ao sair dela, ou ao fechar o jogo, o cursor do Windows volta ao normal.
//
// Uso: Lancador.exe --visual <pasta> [--pasta <pasta de trabalho>] -- <programa> [argumentos...]
//   <pasta> tem icon.ico, splash.png e, se quiser, cursor.cur.
//
// Compilar (o compilador já vem no Windows, com o .NET Framework 4):
//   %WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize+
//     /win32icon:icon.ico /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll
//     /out:Lancador.exe Lancador.cs
// (o instalar.ps1 faz isso). C# 5: é a versão que esse compilador aceita.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

static class Lancador
{
    const double SplashShare = 0.62;          // fração da tela que a abertura ocupa, no máximo
    const int SplashLimitMs = 120000;         // a abertura fecha sozinha depois disso
    const int TickMs = 250;

    [STAThread]
    static int Main(string[] args)
    {
        string visual = null, workDir = null, program = null;
        var rest = new List<string>();
        for (int i = 0; i < args.Length; i++)
        {
            if (program != null) { rest.Add(args[i]); continue; }
            if (args[i] == "--") { if (i + 1 < args.Length) program = args[++i]; continue; }
            if (args[i] == "--visual" && i + 1 < args.Length) { visual = args[++i]; continue; }
            if (args[i] == "--pasta" && i + 1 < args.Length) { workDir = args[++i]; continue; }
        }
        if (program == null || visual == null)
        {
            MessageBox.Show("Uso: Lancador.exe --visual <pasta> [--pasta <pasta de trabalho>] -- <programa> [argumentos...]",
                            "iconicpink-blue", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 2;
        }
        Native.MakeDpiAware();
        Native.RestoreCursors();   // se uma execução anterior caiu com o cursor trocado

        var start = new ProcessStartInfo(program, JoinArgs(rest));
        start.UseShellExecute = false;
        start.WorkingDirectory = workDir ?? Path.GetDirectoryName(Path.GetFullPath(program));

        Application.EnableVisualStyles();
        // a tela de abertura aparece antes de o programa abrir
        var watcher = new Watcher(Path.GetFullPath(program), visual);
        try { watcher.Follow(Process.Start(start)); }
        catch (Exception e)
        {
            watcher.Cleanup();
            MessageBox.Show("Não consegui abrir " + program + ":\n" + e.Message, "iconicpink-blue",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        Application.ApplicationExit += delegate { watcher.Cleanup(); };
        AppDomain.CurrentDomain.UnhandledException += delegate { watcher.Cleanup(); };
        Application.Run(watcher);
        return 0;
    }

    // Regras de aspas da linha de comando do Windows (CommandLineToArgvW).
    static string JoinArgs(List<string> args)
    {
        var sb = new StringBuilder();
        foreach (var a in args)
        {
            if (sb.Length > 0) sb.Append(' ');
            if (a.Length > 0 && a.IndexOfAny(new[] { ' ', '\t', '"' }) < 0) { sb.Append(a); continue; }
            sb.Append('"');
            int slashes = 0;
            foreach (char c in a)
            {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') { sb.Append('\\', slashes * 2 + 1); sb.Append('"'); slashes = 0; continue; }
                sb.Append('\\', slashes); slashes = 0; sb.Append(c);
            }
            sb.Append('\\', slashes * 2);
            sb.Append('"');
        }
        return sb.ToString();
    }

    // Acompanha o jogo: processos (o aberto, os filhos e os relançados), janelas, abertura e cursor.
    sealed class Watcher : ApplicationContext
    {
        readonly HashSet<int> known = new HashSet<int>();
        readonly Dictionary<IntPtr, int> iconed = new Dictionary<IntPtr, int>();   // janela -> vezes que recebeu o ícone
        readonly string programPath, cursorPath;
        readonly IntPtr iconBig, iconSmall;
        readonly Timer timer = new Timer();
        readonly Stopwatch clock = Stopwatch.StartNew();
        Splash splash;
        DateTime followedAt;
        bool cursorOn, sawWindow;
        long lastAlive;

        public Watcher(string programPath, string visual)
        {
            this.programPath = programPath;
            string icon = Path.Combine(visual, "icon.ico");
            if (File.Exists(icon))
            {
                iconBig = Native.LoadIcon(icon, Native.GetSystemMetrics(11), Native.GetSystemMetrics(12));
                iconSmall = Native.LoadIcon(icon, Native.GetSystemMetrics(49), Native.GetSystemMetrics(50));
            }
            string cur = Path.Combine(visual, "cursor.cur");
            cursorPath = File.Exists(cur) ? cur : null;
            string png = Path.Combine(visual, "splash.png");
            if (File.Exists(png))
            {
                try { splash = new Splash(png, SplashShare); splash.Show(); splash.Present(); }
                catch (Exception) { splash = null; }   // sem abertura, o resto segue
            }
        }

        // Começa a acompanhar o processo aberto (e o que vier dele).
        public void Follow(Process child)
        {
            known.Add(child.Id);
            followedAt = DateTime.Now.AddSeconds(-1);
            lastAlive = clock.ElapsedMilliseconds;
            timer.Interval = TickMs;
            timer.Tick += delegate { Tick(); };
            timer.Start();
        }

        void Tick()
        {
            var tree = Native.Processes();
            bool grew = true;
            while (grew)
            {
                grew = false;
                foreach (var p in tree)
                    if (!known.Contains(p.Key) && (known.Contains(p.Value.Parent) || SameProgram(p.Key, p.Value.Exe)))
                    { known.Add(p.Key); grew = true; }
            }
            bool alive = false;
            foreach (int pid in known) if (tree.ContainsKey(pid)) { alive = true; break; }
            if (alive) lastAlive = clock.ElapsedMilliseconds;
            else if (clock.ElapsedMilliseconds - lastAlive > 3000) { ExitThread(); return; }

            var windows = Native.TopWindows(known);
            bool drawing = false;
            foreach (var w in windows)
            {
                int times;
                iconed.TryGetValue(w, out times);
                // de novo depois de uns segundos, se o jogo trocar o ícone ao abrir
                if (iconBig != IntPtr.Zero && (times == 0 || (times == 1 && clock.ElapsedMilliseconds % 4000 < TickMs)))
                {
                    Native.PostMessage(w, 0x0080, (IntPtr)1, iconBig);     // WM_SETICON, ICON_BIG
                    Native.PostMessage(w, 0x0080, IntPtr.Zero, iconSmall); // ICON_SMALL
                    iconed[w] = times + 1;
                }
                if (Native.Title(w).IndexOf(" fps", StringComparison.OrdinalIgnoreCase) >= 0) drawing = true;
            }
            if (windows.Count > 0) sawWindow = true;
            // a janela do jogo fechou antes de desenhar: a abertura sai junto
            bool closed = sawWindow && windows.Count == 0;
            if (splash != null && (drawing || closed || clock.ElapsedMilliseconds > SplashLimitMs || !alive))
            {
                splash.FadeOutAndClose();
                splash = null;
            }

            if (cursorPath != null)
            {
                bool focused = windows.Contains(Native.GetForegroundWindow());
                if (focused && !cursorOn) cursorOn = Native.UseCursor(cursorPath);
                else if (!focused && cursorOn) { Native.RestoreCursors(); cursorOn = false; }
            }
        }

        bool SameProgram(int pid, string exe)
        {
            // um jogo que se relança abre o mesmo programa de novo; só conta o que
            // abriu depois do lançador (nunca outra janela já aberta, como um PowerShell)
            if (!string.Equals(exe, Path.GetFileName(programPath), StringComparison.OrdinalIgnoreCase)) return false;
            try { if (Process.GetProcessById(pid).StartTime < followedAt) return false; }
            catch (Exception) { return false; }   // processo de outro usuário ou já fechado
            string path = Native.ImagePath(pid);
            return path != null && string.Equals(path, programPath, StringComparison.OrdinalIgnoreCase);
        }

        public void Cleanup()
        {
            if (cursorOn) { Native.RestoreCursors(); cursorOn = false; }
            if (splash != null) { splash.Close(); splash = null; }
        }

        protected override void ExitThreadCore()
        {
            timer.Stop();
            Cleanup();
            base.ExitThreadCore();
        }
    }

    // Janela em camadas com alfa por pixel: a arte com cantos arredondados e sombra.
    sealed class Splash : Form
    {
        readonly Bitmap picture;
        readonly Timer fade = new Timer();
        int alpha = 255;

        public Splash(string png, double share)
        {
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            using (var source = new Bitmap(png)) picture = Compose(source, Screen.PrimaryScreen.WorkingArea, share);
            var area = Screen.PrimaryScreen.WorkingArea;
            Bounds = new Rectangle(area.Left + (area.Width - picture.Width) / 2,
                                   area.Top + (area.Height - picture.Height) / 2, picture.Width, picture.Height);
        }

        protected override CreateParams CreateParams
        {
            get
            {
                var cp = base.CreateParams;
                // camadas, sempre por cima, sem botão na barra, sem foco, cliques passam
                cp.ExStyle |= 0x00080000 | 0x00000008 | 0x00000080 | 0x08000000 | 0x00000020;
                return cp;
            }
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        // Desenha já, sem esperar o laço de mensagens (o programa só abre depois).
        public void Present() { Native.SetLayered(this, picture, 255); }

        public void FadeOutAndClose()
        {
            fade.Interval = 16;
            fade.Tick += delegate
            {
                alpha -= 22;
                if (alpha <= 0) { fade.Stop(); Close(); return; }
                Native.SetLayered(this, picture, (byte)alpha);
            };
            fade.Start();
        }

        static Bitmap Compose(Bitmap source, Rectangle area, double share)
        {
            double k = Math.Min(1.0, Math.Min(share * area.Width / source.Width, share * area.Height / source.Height));
            int w = Math.Max(1, (int)(source.Width * k)), h = Math.Max(1, (int)(source.Height * k));
            int m = Math.Max(8, w / 48);                 // margem da sombra
            int r = Math.Max(6, w / 70);                 // raio dos cantos
            var bmp = new Bitmap(w + 2 * m, h + 2 * m + m / 3, PixelFormat.Format32bppArgb);
            using (var g = Graphics.FromImage(bmp))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                g.CompositingQuality = CompositingQuality.HighQuality;
                for (int i = 1; i <= 12; i++)       // sombra suave
                {
                    int d = i * m / 12;
                    using (var path = Rounded(new Rectangle(m - d, m - d + m / 3, w + 2 * d, h + 2 * d), r + d))
                    using (var brush = new SolidBrush(Color.FromArgb(12, 0, 0, 0)))
                        g.FillPath(brush, path);
                }
                using (var path = Rounded(new Rectangle(m, m, w, h), r))
                {
                    g.SetClip(path);
                    using (var attrs = new ImageAttributes())
                    {
                        attrs.SetWrapMode(WrapMode.TileFlipXY);   // sem borda clara no redimensionamento
                        g.DrawImage(source, new Rectangle(m, m, w, h), 0, 0, source.Width, source.Height,
                                    GraphicsUnit.Pixel, attrs);
                    }
                    g.ResetClip();
                    using (var pen = new Pen(Color.FromArgb(30, 255, 255, 255), Math.Max(1f, w / 960f)))
                        g.DrawPath(pen, path);
                }
            }
            return bmp;
        }

        static GraphicsPath Rounded(Rectangle b, int r)
        {
            var p = new GraphicsPath();
            int d = r * 2;
            p.AddArc(b.Left, b.Top, d, d, 180, 90);
            p.AddArc(b.Right - d, b.Top, d, d, 270, 90);
            p.AddArc(b.Right - d, b.Bottom - d, d, d, 0, 90);
            p.AddArc(b.Left, b.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) { picture.Dispose(); fade.Dispose(); }
            base.Dispose(disposing);
        }
    }

    static class Native
    {
        [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr value);
        [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
        [DllImport("user32.dll")] public static extern int GetSystemMetrics(int index);
        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr LoadImage(IntPtr hinst, string name, uint type, int cx, int cy, uint flags);
        [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd, uint msg, IntPtr w, IntPtr l);
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] static extern bool SetSystemCursor(IntPtr cursor, uint id);
        [DllImport("user32.dll")] static extern bool SystemParametersInfo(uint action, uint param, IntPtr pv, uint ini);
        delegate bool EnumProc(IntPtr hwnd, IntPtr lparam);
        [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc proc, IntPtr lparam);
        [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
        [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")] static extern IntPtr GetWindow(IntPtr hwnd, uint cmd);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int max);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        static extern int GetClassName(IntPtr hwnd, StringBuilder text, int max);
        [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool Process32FirstW(IntPtr snap, ref ENTRY e);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern bool Process32NextW(IntPtr snap, ref ENTRY e);
        [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
        [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
        static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder name, ref int size);
        [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr hwnd);
        [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr hwnd, IntPtr dc);
        [DllImport("gdi32.dll")] static extern IntPtr CreateCompatibleDC(IntPtr dc);
        [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr dc);
        [DllImport("gdi32.dll")] static extern IntPtr SelectObject(IntPtr dc, IntPtr obj);
        [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr obj);
        [DllImport("user32.dll")]
        static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr dst, ref POINT at, ref SIZE size, IntPtr src,
                                               ref POINT srcAt, int key, ref BLEND blend, int flags);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        struct ENTRY
        {
            public uint dwSize, cntUsage, th32ProcessID;
            public IntPtr th32DefaultHeapID;
            public uint th32ModuleID, cntThreads, th32ParentProcessID;
            public int pcPriClassBase;
            public uint dwFlags;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szExeFile;
        }
        [StructLayout(LayoutKind.Sequential)] struct POINT { public int X, Y; }
        [StructLayout(LayoutKind.Sequential)] struct SIZE { public int W, H; }
        [StructLayout(LayoutKind.Sequential, Pack = 1)] struct BLEND { public byte Op, Flags, Alpha, Format; }

        public struct Proc { public int Parent; public string Exe; }

        public static void MakeDpiAware()
        {
            try { if (SetProcessDpiAwarenessContext((IntPtr)(-4))) return; }   // por monitor, v2
            catch (EntryPointNotFoundException) { }
            SetProcessDPIAware();
        }

        public static IntPtr LoadIcon(string path, int cx, int cy)
        {
            return LoadImage(IntPtr.Zero, path, 1 /* IMAGE_ICON */, cx, cy, 0x10 /* LR_LOADFROMFILE */);
        }

        // Troca a seta do Windows pelo nosso cursor (uma cópia nova a cada vez:
        // o Windows fica com ela). Devolve se trocou.
        public static bool UseCursor(string path)
        {
            IntPtr c = LoadImage(IntPtr.Zero, path, 2 /* IMAGE_CURSOR */, 0, 0, 0x10 | 0x40 /* DEFAULTSIZE */);
            return c != IntPtr.Zero && SetSystemCursor(c, 32512 /* OCR_NORMAL */);
        }

        // Recarrega o esquema de cursores do próprio usuário.
        public static void RestoreCursors() { SystemParametersInfo(0x0057 /* SPI_SETCURSORS */, 0, IntPtr.Zero, 0); }

        public static Dictionary<int, Proc> Processes()
        {
            var all = new Dictionary<int, Proc>();
            IntPtr snap = CreateToolhelp32Snapshot(2 /* TH32CS_SNAPPROCESS */, 0);
            if (snap == (IntPtr)(-1)) return all;
            var e = new ENTRY();
            e.dwSize = (uint)Marshal.SizeOf(typeof(ENTRY));
            for (bool ok = Process32FirstW(snap, ref e); ok; ok = Process32NextW(snap, ref e))
            {
                var p = new Proc();
                p.Parent = (int)e.th32ParentProcessID;
                p.Exe = e.szExeFile;
                all[(int)e.th32ProcessID] = p;
            }
            CloseHandle(snap);
            return all;
        }

        public static string ImagePath(int pid)
        {
            IntPtr h = OpenProcess(0x1000 /* QUERY_LIMITED_INFORMATION */, false, pid);
            if (h == IntPtr.Zero) return null;
            try
            {
                var sb = new StringBuilder(1024);
                int size = sb.Capacity;
                return QueryFullProcessImageName(h, 0, sb, ref size) ? sb.ToString() : null;
            }
            finally { CloseHandle(h); }
        }

        // Janelas de primeiro nível, visíveis e sem dono, dos processos do jogo (sem consoles).
        public static HashSet<IntPtr> TopWindows(HashSet<int> pids)
        {
            var found = new HashSet<IntPtr>();
            EnumWindows(delegate(IntPtr hwnd, IntPtr l)
            {
                uint pid;
                GetWindowThreadProcessId(hwnd, out pid);
                if (pids.Contains((int)pid) && IsWindowVisible(hwnd) && GetWindow(hwnd, 4 /* GW_OWNER */) == IntPtr.Zero)
                {
                    var cls = new StringBuilder(256);
                    GetClassName(hwnd, cls, cls.Capacity);
                    string c = cls.ToString();
                    if (c != "ConsoleWindowClass" && c != "CASCADIA_HOSTING_WINDOW_CLASS") found.Add(hwnd);
                }
                return true;
            }, IntPtr.Zero);
            return found;
        }

        public static string Title(IntPtr hwnd)
        {
            var sb = new StringBuilder(512);
            GetWindowText(hwnd, sb, sb.Capacity);
            return sb.ToString();
        }

        public static void SetLayered(Form form, Bitmap bmp, byte alpha)
        {
            IntPtr screen = GetDC(IntPtr.Zero), mem = CreateCompatibleDC(screen);
            IntPtr hbmp = bmp.GetHbitmap(Color.FromArgb(0)), old = SelectObject(mem, hbmp);
            try
            {
                var at = new POINT { X = form.Left, Y = form.Top };
                var size = new SIZE { W = bmp.Width, H = bmp.Height };
                var origin = new POINT();
                var blend = new BLEND { Op = 0, Flags = 0, Alpha = alpha, Format = 1 /* AC_SRC_ALPHA */ };
                UpdateLayeredWindow(form.Handle, screen, ref at, ref size, mem, ref origin, 0, ref blend, 2 /* ULW_ALPHA */);
            }
            finally
            {
                SelectObject(mem, old);
                DeleteObject(hbmp);
                DeleteDC(mem);
                ReleaseDC(IntPtr.Zero, screen);
            }
        }
    }
}
