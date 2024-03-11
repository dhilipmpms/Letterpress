pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'letterpress'
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'gtk/tips-dialog.blp',
    'gtk/window.blp',
    'gtk/zoom-box.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('app_id', app_id)
conf.set('profile', get_option('profile'))

gnome.compile_resources('letterpress',
  configure_file(
            input: 'letterpress.gresource.xml.in',
           output: 'letterpress.gresource.xml',
    configuration: conf
  ),
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: [blueprints, appstream_file],
)

configure_file(
  input: 'letterpress.in',
  output: 'letterpress',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'profile.py.in',
  output: 'profile.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

letterpress_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'file_chooser.py',
  'pasting.py',
  'texture_to_file.py',
  'zoom_consts.py',
  'zoom_box.py',
  'tips_dialog.py',
  'supported_formats.py',
]

install_data(letterpress_sources, install_dir: moduledir)
