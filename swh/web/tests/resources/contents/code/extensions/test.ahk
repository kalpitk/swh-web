﻿; hotkeys and hotstrings
#a::WinSet, AlwaysOnTop, Toggle, A
#Space::
  MsgBox, Percent sign (`%) need to be escaped.
  Run "C:\Program Files\some\program.exe"
  Gosub, label1
return
::btw::by the way
; volume
#Numpad8::Send {Volume_Up}
#Numpad5::Send {Volume_Mute}
#Numpad2::Send {Volume_Down}

label1:
  if (Clipboard = "")
  {
    MsgBox, , Clipboard, Empty!
  }
  else
  {
    StringReplace, temp, Clipboard, old, new, All
    MsgBox, , Clipboard, %temp%
  }
return