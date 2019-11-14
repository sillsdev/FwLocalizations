@REM this is a script to call the converter documented at http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/po2tmx.html
@REM Usage: po2tmxcaller.bat <locale>
po2tmx --language %1 messages.%1.po messages.%1.tmx
