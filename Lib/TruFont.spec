# -*- mode: python -*-

block_cipher = None


a = Analysis(['trufont/__main__.py'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='TruFont',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='trufont/resources/app.ico')
app = BUNDLE(exe,
             name='TruFont.app',
             icon='trufont/resources/app.icns',
             bundle_identifier='io.github.trufont',
             info_plist={
               'NSHighResolutionCapable': 'True',
               'LSBackgroundOnly': '0'
             },
             version='0.2.0')
