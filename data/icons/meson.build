conf = configuration_data()
conf.set('app_id', app_id)

scalable_dir = 'hicolor' / 'scalable' / 'apps'
install_data(
  scalable_dir / ('@0@.svg').format(app_id),
  install_dir: get_option('datadir') / 'icons' / scalable_dir
)

symbolic_dir = 'hicolor' / 'symbolic' / 'apps'
install_data(
  symbolic_dir / 'io.gitlab.gregorni.Letterpress-symbolic.svg',
  install_dir: get_option('datadir') / 'icons' / symbolic_dir
)
