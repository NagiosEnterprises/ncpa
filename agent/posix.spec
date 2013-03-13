# -*- mode: python -*-
a = Analysis(['ncpa_posix_listener.py'],
             pathex=['.'],
             hookspath='',
	     )
b = Analysis(['ncpa_posix_passive.py'],
             pathex=['.'],
              )

pya = PYZ(a.pure)

pyb = PYZ(b.pure)

exea = EXE(pya,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.linux2/ncpa_posix', 'ncpa_posix_listener'),
          debug=False,
          strip=None,
          upx=True,
          console=True )

exeb = EXE(pyb,
          b.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.linux2/ncpa_posix', 'ncpa_posix_passive'),
          debug=False,
          strip=None,
          upx=True,
          console=True )


coll = COLLECT(exea,
	       exeb,
               a.binaries,
	       b.binaries,
               a.zipfiles,
	       b.zipfiles,
               [('plugins/test.sh', 'plugins/yancyforprez.sh', 'DATA')],
               [('etc/ncpa.cfg', 'etc/ncpa.cfg', 'DATA')],
               [('var/ncpa_listener.log',  'var/ncpa_listener.log', 'DATA')],
               [('var/ncpa_passive.log', 'var/ncpa_passive.log', 'DATA')],
               a.datas,
	       b.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'ncpa_posix'))
