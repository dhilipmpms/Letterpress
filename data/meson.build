conf = configuration_data()
conf.set('app_id', app_id)

desktop_file = i18n.merge_file(
	input: configure_file(
		         input: 'io.gitlab.gregorni.Letterpress.desktop.in.in',
		        output: 'io.gitlab.gregorni.Letterpress.desktop.in',
		 configuration: conf
		),
       output: app_id + '.desktop',

         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: configure_file(
                  input: 'io.gitlab.gregorni.Letterpress.metainfo.xml.in.in',
                 output: 'io.gitlab.gregorni.Letterpress.metainfo.xml.in',
          configuration: conf
        ),
       output: app_id + '.metainfo.xml',

       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'metainfo',
)

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validate appstream file',
       appstreamcli,
       args: ['validate', '--no-net', '--explain', appstream_file],
       workdir: meson.current_build_dir()
  )
endif

install_data('io.gitlab.gregorni.Letterpress.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0/schemas'
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

subdir('icons')
