pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'letterpress')
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

gnome.compile_resources('letterpress',
  'letterpress.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: [blueprints, appstream_file],
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'letterpress.in',
  output: 'letterpress',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

letterpress_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'file_chooser.py',
  'pasting.py',
  'texture_to_file.py',
]

install_data(letterpress_sources, install_dir: moduledir)
