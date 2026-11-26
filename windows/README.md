# Part 2: Windows look

<p><b>English</b> · <a href="README.pt-BR.md">Português (BR)</a></p>

A **launcher** that opens the game through the program you already use and
only takes care of the look. It does three things:

- shows the game's **splash screen**, sharp at any Windows display scale,
  until the game starts drawing;
- puts the **icon** on the game window, the taskbar, Alt+Tab, the desktop
  shortcut and the Start menu;
- swaps the **cursor** if you want: only while the game window has focus, and
  it goes back to normal when you leave.

It **changes no line** of VIctory or any fork. It works from the outside, so
it fits all of them:

| Fork | Part 1 (key icons) | Part 2 (this launcher) |
|---|:-:|:-:|
| VIctory | ✅ | ✅ |
| Belobug/VIctory-Belobug-AMD | ✅ | ✅ |
| avatarmanz/VIctory-7900XTX | ✅ | ✅ |
| DexNom/VIctory (uses its own `victory-play.exe`) | ✅ | ✅ |

Checked by reading each one's code. All of them mount the game folder the same
way, let the game create its own window and write "fps" in its title once they
start drawing; that is the signal that closes the splash.

> [!IMPORTANT]
> Nothing from the game is in here. The splash comes from **your** build
> (`xbs_splash.png`). The icon comes from a logo PNG of yours (`-Logo`) or,
> without one, from the official icon your build ships (`xbs_logo_480.png`).

## Test

[Test video on Windows 11](../docs/windows_teste.mp4) (16 s): the shortcut, the splash,
the window icon and the cursor, with a stand-in window that mimics the game.

## Install

Windows 10 or 11 is all it needs: the C# compiler ships with .NET Framework 4,
and the installer compiles `Lancador.cs` on the spot.

```powershell
# VIctory, Belobug, avatarmanz (built by you)
powershell -ExecutionPolicy Bypass -File instalar.ps1 instalar `
  -Jogo "D:\game\game_scarlett_master.exe" -Logo "D:\logo.png" `
  -Programa "D:\VIctory\target\release\victory.exe" -Pasta "D:\VIctory" `
  -Argumentos 'run "D:\game\game_scarlett_master.exe" --execute'

# DexNom (after its Setup.cmd)
powershell -ExecutionPolicy Bypass -File instalar.ps1 instalar `
  -Jogo "D:\game\game_scarlett_master.exe" -Logo "D:\logo.png" `
  -Programa "$env:LOCALAPPDATA\DexNom Runtime\victory-play.exe"
```

- `-Jogo`: the game executable. With part 1, use the one in the mirror folder.
- `-Logo` (optional): a PNG with a transparent background. The icon comes out
  at 16 to 256 px.
- Cursor: ours by default (`cursor/radar.cur`: the radar arrow, white body,
  rim in the logo gradient). `-Cursor` uses another `.cur`; `-SemCursor` leaves the cursor alone.
- `-Nome` (optional): the shortcut name (default "Grand Theft Auto VI").

The installer creates `%LOCALAPPDATA%\iconicpink-blue` (the launcher and a
`visual` folder) and the shortcuts. To undo:

```powershell
powershell -ExecutionPolicy Bypass -File instalar.ps1 remover
```

## How it works

1. The shortcut opens `Lancador.exe`, which opens your program with the same
   arguments as always.
2. The launcher follows that process, the processes it starts and the game,
   if it relaunches itself.
3. When the game window appears, it gets the icon (`WM_SETICON`).
4. The splash goes away when the window title gains "fps", or after
   2 minutes.
5. When the game closes, the launcher restores the Windows cursor and quits.

## Limits

- Opening `victory.exe` directly, without the shortcut, opens the game without
  this look.
- `victory.exe` itself keeps the default icon in Explorer; `Lancador.exe`, the
  shortcut and the window get the new one.
