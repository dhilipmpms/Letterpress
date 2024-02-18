conf = configuration_data()
conf.set('app_id', app_id)

scalable_dir = join_paths('hicolor', 'scalable', 'apps')
install_data(
  join_paths(scalable_dir, ('@0@.svg').format(app_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir)
)

symbolic_dir = join_paths('hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, 'io.gitlab.gregorni.Letterpress-symbolic.svg'),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_dir)
)
